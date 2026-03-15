import asyncio
import json
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, Prompt, PromptArgument, PromptMessage, GetPromptResult
from mcp.server.stdio import stdio_server
import data
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
# The client will automatically look for 'GOOGLE_API_KEY' in your environment
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", "dummy_key"))

app = Server("interactive-portfolio")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources for the portfolio."""
    return [
        Resource(
            uri="resume://experience",
            name="Professional Experience",
            description="Detailed work history and roles.",
            mimeType="application/json",
        ),
        Resource(
            uri="resume://skills",
            name="Technical Skills",
            description="List of proficient technologies and concepts.",
            mimeType="application/json",
        )
    ]

@app.read_resource()
async def read_resource(uri: str | object) -> str:
    """Read a specific resource's content."""
    # Handle possible variations in URI formatting between clients and servers
    # The 'uri' might be passed as a Pydantic AnyUrl object by the SDK, so we cast it to string first.
    normalized_uri = str(uri).rstrip('/')
    
    if normalized_uri == "resume://experience":
        return json.dumps(data.EXPERIENCE, indent=2)
    elif normalized_uri == "resume://skills":
        return json.dumps(data.SKILLS, indent=2)
    raise ValueError(f"Unknown resource URI: {uri} (normalized: {normalized_uri})")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for analyzing the portfolio."""
    return [
        Tool(
            name="query_skill",
            description="Find projects and context where a specific skill was used.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill": {"type": "string", "description": "The technology name (e.g., 'Python', 'React')."}
                },
                "required": ["skill"]
            }
        ),
        Tool(
            name="get_contact_info",
            description="Retrieve my professional contact information and social links.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="read_resource",
            description="Search and read the content of any available MCP resource by its URI. Use this to dive into deep career data like 'resume://experience'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {"type": "string", "description": "The exact URI of the resource to read."}
                },
                "required": ["uri"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a requested tool."""
    if name == "query_skill":
        skill = arguments.get("skill")
        if not skill:
             raise ValueError("Missing 'skill' argument")
        matching_projects = data.get_projects_by_skill(skill)
        if not matching_projects:
             return [TextContent(type="text", text=f"No specific projects found using '{skill}', but I may have used it in general roles.")]
        return [TextContent(type="text", text=json.dumps(matching_projects, indent=2))]

    elif name == "get_contact_info":
        return [TextContent(type="text", text=json.dumps(data.get_contact_info(), indent=2))]

    elif name == "read_resource":
        uri = arguments.get("uri")
        if not uri:
             raise ValueError("Missing 'uri' argument")
        content = await read_resource(uri)
        return [TextContent(type="text", text=content)]

    raise ValueError(f"Unknown tool: {name}")


@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="write-cover-letter",
            description="Drafts a tailored cover letter using the resume context.",
            arguments=[
                PromptArgument(
                    name="company_name",
                    description="The name of the company to apply to.",
                    required=True
                ),
                PromptArgument(
                     name="job_role",
                     description="The role being applied for.",
                     required=True
                )
            ]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """Get a prompt by name."""
    if name != "write-cover-letter":
        raise ValueError(f"Unknown prompt: {name}")

    company = arguments.get("company_name", "a company")
    role = arguments.get("job_role", "a role")

    return GetPromptResult(
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text", 
                    text=f"Please read my `resume://experience` and write a short, compelling cover letter for the '{role}' position at {company}."
                )
            )
        ]
    )

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

fastapi_app = FastAPI(strict_slashes=False)
fastapi_app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Allow the React frontend to communicate with this server
# In production, set ALLOWED_ORIGINS to your frontend domain (e.g., https://yourportfolio.com)
allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins_raw == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

import traceback
# Create the SSE transport
sse = SseServerTransport("/messages")

@fastapi_app.get("/sse")
async def sse_handler(request: Request):
    """Event stream for MCP messages."""
    print("SSE connection attempt received")
    try:
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            print("SSE transport connected, running MCP server...")
            await app.run(streams[0], streams[1], app.create_initialization_options())
    except Exception as e:
        print(f"CRITICAL SSE ERROR: {e}")
        traceback.print_exc()
        raise e

@fastapi_app.post("/messages")
async def post_message_handler(request: Request):
    """Handle POST messages from the client."""
    try:
        await sse.handle_post_message(request.scope, request.receive, request._send)
    except Exception as e:
        print(f"CRITICAL POST ERROR: {e}")
        traceback.print_exc()
        raise e

# Health check
@fastapi_app.get("/health")
async def health_check():
    print("Health check requested")
    return {"status": "ok", "port": os.environ.get("PORT", "8000")}

# --- AI Orchestration Helpers ---

async def query_skill(skill: str) -> str:
    """Find projects and context where a specific skill was used."""
    # skill: The technology name (e.g., 'Python', 'React').
    result = await call_tool("query_skill", {"skill": skill})
    return result[0].text if result else "No data found."

async def get_contact_info() -> str:
    """Retrieve my professional contact information and social links."""
    result = await call_tool("get_contact_info", {})
    return result[0].text if result else "No contact info available."

async def get_full_experience() -> str:
    """Retrieve the complete work history, project details, and roles from the resume."""
    return await read_resource("resume://experience")

async def get_technical_skills() -> str:
    """Retrieve the full list of technical skills and proficiencies."""
    return await read_resource("resume://skills")

async def draft_cover_letter(company_name: str, job_role: str) -> str:
    """Generate a tailored cover letter for a specific company and role using the resume context."""
    prompt_msg = await get_prompt("write-cover-letter", {"company_name": company_name, "job_role": job_role})
    return prompt_msg.content.text

@fastapi_app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Orchestrated chat endpoint that uses MCP tools to answer queries."""
    body = await request.json()
    user_message = body.get("message")
    
    if not user_message:
        return {"error": "Message is required"}

    # We use the new google-genai SDK pattern with async support
    # gemini-2.5-flash is the recommended workhorse model
    chat = client.aio.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="""You are a Smart Career Consultant and Portfolio Assistant. 
            You have access to the user's career context via MCP Tools and Resources.
            
            Key Guidelines:
            1. Use `read_resource` with 'resume://experience' or 'resume://skills' when you need full background context or project lists.
            2. When asked for a cover letter, fetch the experience and contact info first, then write a highly personalized and professional letter yourself.
            3. Use `query_skill` for specific technology deep-dives.
            4. Always be helpful, professional, and highlight the user's strengths based on the ACTUAL data retrieved.""",
            tools=[query_skill, get_contact_info, get_full_experience, get_technical_skills]
        )
    )
    
    max_retries = 3
    retry_delay = 2 # seconds
    
    for attempt in range(max_retries):
        try:
            # Gemini handles the loop of "thinking -> calling tool -> receiving data -> answering" automatically
            response = await chat.send_message(user_message)
            return {"response": response.text}
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < max_retries - 1:
                print(f"Quota exceeded (429), retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
                continue
                
            print(f"Chat Error after {attempt + 1} attempts: {e}")
            return {"response": "I'm a bit overwhelmed with requests right now! Please try again in 30 seconds, or check out my data panels on the left!"}

# Routes and handlers are defined above with fastapi_app.add_route

if __name__ == "__main__":
    import sys
    # If run with --stdio, run as a standard MCP server
    if "--stdio" in sys.argv:
        async def run_stdio():
            async with stdio_server() as (read_stream, write_stream):
                await app.run(read_stream, write_stream, app.create_initialization_options())
        
        asyncio.run(run_stdio())
    else:
        # Otherwise, run the FastAPI app (using uvicorn)
        import uvicorn
        # We lock this to 8000 to match your Railway Networking settings
        port = 8000
        print(f"Starting server on port {port}...")
        uvicorn.run(fastapi_app, host="0.0.0.0", port=port)
