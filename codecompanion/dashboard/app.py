"""
FastAPI dashboard application for CodeCompanion Control Tower.
Provides a web-based live status board with auto-refresh capabilities.

This is a read-only dashboard that uses /api/info endpoint.
No mutations or configuration changes are made through this interface.
"""
import os
import sys
from pathlib import Path
from typing import Optional

# Suppress Streamlit warnings before any imports that might trigger it
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime

# Import info gathering functions
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from codecompanion.info_core import gather_all_info
from codecompanion.llm import complete, LLMError
from codecompanion.runner import run_pipeline, run_single_agent


app = FastAPI(
    title="CodeCompanion Control Tower",
    description="Live status dashboard for CodeCompanion standalone Dev OS",
    version="0.1.0",
)


@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Serve the main dashboard HTML page."""
    template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"

    if not template_path.exists():
        return HTMLResponse(
            content="<h1>Dashboard template not found</h1>",
            status_code=500,
        )

    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@app.get("/api/info")
async def get_info():
    """
    API endpoint that returns current system information.
    This is the same data structure returned by `codecompanion --info --raw`.

    Returns JSON with:
    - bootstrap: Project and bootstrap status
    - agent_workflow: Agent files and completion status
    - providers: LLM provider configurations and API key status
    - pipeline: Pipeline execution history (placeholder)
    - errors: Error history and recovery status (placeholder)
    - recommendations: System recommendations based on current state
    """
    project_root = os.getcwd()
    info_data = gather_all_info(project_root)
    return JSONResponse(content=info_data)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "codecompanion-dashboard"}


def run_console_command(mode: str, input_text: str, agent_name: Optional[str] = None, provider: str = "claude") -> dict:
    """
    Run a CodeCompanion command programmatically and capture output.

    Args:
        mode: "chat", "auto", or "agent"
        input_text: User input/instruction
        agent_name: Optional agent name (for mode="agent")
        provider: LLM provider to use (default: "claude")

    Returns:
        dict with status, output, timestamps, etc.
    """
    started_at = datetime.utcnow().isoformat() + "Z"
    output_buffer = io.StringIO()
    error_buffer = io.StringIO()

    try:
        # Capture stdout and stderr
        with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
            if mode == "chat":
                # Single-turn chat mode: send user input and get response
                try:
                    response = complete(
                        "You are CodeCompanion, a helpful coding assistant. Respond to the user's question or instruction concisely.",
                        [{"role": "user", "content": input_text}],
                        provider=provider,
                    )
                    output = response.get("content", "")
                    print(output)
                except LLMError as e:
                    raise Exception(f"LLM Error: {str(e)}")

            elif mode == "auto":
                # Run full pipeline
                print(f"[console] Running full pipeline in current repo...")
                print(f"[console] Project root: {os.getcwd()}")
                exit_code = run_pipeline(provider=provider)
                if exit_code != 0:
                    raise Exception(f"Pipeline failed with exit code {exit_code}")
                print(f"[console] Pipeline completed successfully")

            elif mode == "agent":
                # Run single agent
                if not agent_name:
                    raise Exception("Agent name is required for mode='agent'")
                print(f"[console] Running agent: {agent_name}")
                print(f"[console] Project root: {os.getcwd()}")
                exit_code = run_single_agent(agent_name, provider=provider)
                if exit_code != 0:
                    raise Exception(f"Agent '{agent_name}' failed with exit code {exit_code}")
                print(f"[console] Agent '{agent_name}' completed successfully")

            else:
                raise Exception(f"Unknown mode: {mode}. Use 'chat', 'auto', or 'agent'")

        # Success case
        finished_at = datetime.utcnow().isoformat() + "Z"
        stdout_output = output_buffer.getvalue()
        stderr_output = error_buffer.getvalue()

        # Combine stdout and stderr for display
        full_output = stdout_output
        if stderr_output.strip():
            full_output += "\n\n[stderr]\n" + stderr_output

        return {
            "status": "ok",
            "mode": mode,
            "input": input_text,
            "output": full_output,
            "started_at": started_at,
            "finished_at": finished_at,
        }

    except Exception as e:
        # Error case
        finished_at = datetime.utcnow().isoformat() + "Z"
        stdout_output = output_buffer.getvalue()
        stderr_output = error_buffer.getvalue()

        # Include captured output in error response
        error_context = ""
        if stdout_output.strip():
            error_context += f"\n\n[stdout]\n{stdout_output}"
        if stderr_output.strip():
            error_context += f"\n\n[stderr]\n{stderr_output}"

        return {
            "status": "error",
            "mode": mode,
            "input": input_text,
            "error": str(e) + error_context,
            "started_at": started_at,
            "finished_at": finished_at,
        }


@app.post("/api/console")
async def console_command(request: Request):
    """
    Execute a console command and return results.

    Request body (JSON):
    {
        "mode": "chat" | "auto" | "agent",
        "input": "<user instruction>",
        "agent": "<optional agent name>",
        "provider": "<optional provider, defaults to claude>"
    }

    Response (JSON):
    {
        "status": "ok" | "error",
        "mode": "...",
        "input": "...",
        "output": "..." (on success) or "error": "..." (on failure),
        "started_at": "...",
        "finished_at": "..."
    }
    """
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "error": f"Invalid JSON request body: {str(e)}",
            },
            status_code=400,
        )

    # Extract parameters with defaults
    mode = body.get("mode", "chat")
    input_text = body.get("input", "").strip()
    agent_name = body.get("agent")
    provider = body.get("provider", "claude")

    # Validate input
    if not input_text:
        return JSONResponse(
            content={
                "status": "error",
                "error": "Input text is required",
            },
            status_code=400,
        )

    if mode not in ["chat", "auto", "agent"]:
        return JSONResponse(
            content={
                "status": "error",
                "error": f"Invalid mode: {mode}. Use 'chat', 'auto', or 'agent'",
            },
            status_code=400,
        )

    # Execute command
    result = run_console_command(mode, input_text, agent_name, provider)

    # Return result with appropriate status code
    status_code = 200 if result["status"] == "ok" else 500
    return JSONResponse(content=result, status_code=status_code)


def run_dashboard(host: str = "0.0.0.0", port: Optional[int] = None):
    """Run the dashboard server using uvicorn with graceful shutdown."""
    import uvicorn
    import signal
    import sys

    if port is None:
        port = int(os.getenv("PORT", 3000))

    print(f"[CodeCompanion] Starting Control Tower dashboard...")
    print(f"[CodeCompanion] Dashboard available at: http://{host}:{port}/")
    print(f"[CodeCompanion] Press Ctrl+C to stop")

    # Create uvicorn server instance for graceful shutdown
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
    )

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\n[CodeCompanion] Shutting down dashboard...")
        server.should_exit = True
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the server
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n[CodeCompanion] Dashboard stopped")
        sys.exit(0)
