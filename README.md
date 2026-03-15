# MCP Identity Server

This project consists of an AI-native portfolio backend using the Model Context Protocol (MCP) and FastAPI, with a React frontend.

## How to Run

### Backend (FastAPI + MCP + AI)
The backend exposes the portfolio data as MCP resources and tools, and provides a "Smart Chat" API powered by Gemini.

1.  **Configure environment:** Create a `.env` file in the `backend/` directory with your Gemini API key:
    ```
    GOOGLE_API_KEY=your_key_here
    ```
2.  **Navigate to the backend directory and run:**
    ```powershell
    cd backend
    ```
2.  **Run the server:**
    ```powershell
    uvicorn server:fastapi_app --host 0.0.0.0 --port 8000 --reload
    ```

### Frontend (React + Vite)
The frontend connects to the backend to display the portfolio data.

1.  **Navigate to the frontend directory:**
    ```powershell
    cd frontend
    ```
2.  **Install dependencies:**
    ```powershell
    npm install
    ```
3.  **Run the development server:**
    ```powershell
    npm run dev
    ```

## How to Connect to LLM Clients (Claude Desktop, etc.)

You can connect this MCP server to AI assistants like Claude Desktop for real-time context about your career and skills.

### Option 1: Direct Connection (Recommended for Local Use)
Claude Desktop and most other assistants prefer the `stdio` transport for local servers.

1.  Open your Claude Desktop configuration file:
    - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
2.  Add this server to the `mcpServers` section:
    ```json
    {
      "mcpServers": {
        "mcp-portfolio": {
          "command": "python",
          "args": [
            "./backend/server.py",
            "--stdio"
          ]
        }
      }
    }
    ```
    *(Note: Use the absolute path to your `server.py` and ensure your `python` environment has the requirements installed.)*

### Option 2: Remote/SSE Connection (For Web Deployment)
If you deploy this server to the web, you can connect via SSE. Since some clients don't yet support SSE natively, you might need a bridge:
```powershell
npx @modelcontextprotocol/inspector http://localhost:8000/sse
```

## Deployment with Docker (Recommended)

The easiest way to deploy the entire system (Backend + Frontend) is using Docker Compose.

1.  **Ensure Docker is installed** on your machine.
2.  **Add your API Key** to `./backend/.env`.
3.  **Run the entire system:**
    ```powershell
    docker-compose up --build
    ```

### 🌐 Deploying to Public (Cloud)
When you are ready to host your portfolio on a public domain (e.g., `https://my-portfolio.com`):

1.  Open `docker-compose.yml`.
2.  Update the `VITE_BACKEND_URL` build argument for the frontend:
    ```yaml
    args:
      - VITE_BACKEND_URL=https://my-portfolio-api.com
    ```
3.  Rebuild the containers: `docker-compose up --build`.

- The **Frontend** will be available at [http://localhost:3000](http://localhost:3000).
- The **Backend** (MCP & Chat API) will be available at [http://localhost:8000](http://localhost:8000).

## Project Structure
- `backend/`: Python FastAPI server implementing MCP (SSE & stdio support).
- `frontend/`: React application displaying portfolio data via MCP SSE.
- `docker-compose.yml`: Multi-container orchestration for the full system.