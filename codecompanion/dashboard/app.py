"""
FastAPI dashboard application for CodeCompanion Control Tower.
Provides a web-based live status board with auto-refresh capabilities.

This is a read-only dashboard that uses /api/info endpoint.
No mutations or configuration changes are made through this interface.
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional
import os

# Import info gathering functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from codecompanion.info_core import gather_all_info


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


def run_dashboard(host: str = "0.0.0.0", port: Optional[int] = None):
    """Run the dashboard server using uvicorn."""
    import uvicorn

    if port is None:
        port = int(os.getenv("PORT", 3000))

    print(f"[CodeCompanion] Starting Control Tower dashboard...")
    print(f"[CodeCompanion] Dashboard available at: http://{host}:{port}/")
    print(f"[CodeCompanion] Press Ctrl+C to stop")

    uvicorn.run(app, host=host, port=port, log_level="info")
