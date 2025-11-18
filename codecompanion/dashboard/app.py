from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from ..info_core import gather_info_snapshot


def create_dashboard_app() -> FastAPI:
    """
    Create and configure the FastAPI dashboard application.
    """
    app = FastAPI(title="CodeCompanion Dashboard", version="0.1.0")

    # Set up templates directory
    base_dir = Path(__file__).resolve().parent.parent  # codecompanion/
    templates_dir = base_dir / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))

    @app.get("/api/info")
    async def api_info() -> JSONResponse:
        """
        JSON API endpoint returning raw info payload.
        This matches the output of `codecompanion --info --raw`.
        """
        snapshot = gather_info_snapshot()
        return JSONResponse(snapshot.raw)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        """
        HTML Control Tower page showing system information.
        This is the web equivalent of `codecompanion --info`.
        """
        snapshot = gather_info_snapshot()
        data = snapshot.raw
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "data": data,
            },
        )

    @app.get("/health")
    async def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok"}

    return app
