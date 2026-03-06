import asyncio
import json
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, Prompt, PromptArgument, PromptMessage
import data

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
async def get_prompt(name: str, arguments: dict) -> PromptMessage:
    """Get a prompt by name."""
    if name != "write-cover-letter":
        raise ValueError(f"Unknown prompt: {name}")

    company = arguments.get("company_name", "a company")
    role = arguments.get("job_role", "a role")

    return PromptMessage(
         role="user",
         content=TextContent(
             type="text", 
             text=f"Please read my `resume://experience` and write a short, compelling cover letter for the '{role}' position at {company}."
         )
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.sse import SseServerTransport
from starlette.requests import Request

fastapi_app = FastAPI()

# Allow the React frontend to communicate with this server
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sse = SseServerTransport("/messages")

@fastapi_app.get("/sse")
async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())

@fastapi_app.post("/messages")
async def handle_messages(request: Request):
    await sse.handle_post_message(request.scope, request.receive, request._send)
