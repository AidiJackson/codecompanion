# api.py — CodeCompanion API (token-protected)

import os
from fastapi import FastAPI, Body, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from settings import settings
from services.real_models import real_e2e

TOKEN: str | None = os.getenv("CODECOMPANION_TOKEN")

app = FastAPI(title="CodeCompanion API")

# Allow CLI calls from anywhere; token enforces auth on protected endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    """
    Accept either:
      - Authorization: Bearer <token>
      - X-API-Key: <token>
    Raises 403 if token is missing/invalid, 500 if server token is unset.
    """
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization.split(" ", 1)[1].strip()
    elif x_api_key:
        provided = x_api_key.strip()

    if not TOKEN:
        raise HTTPException(
            status_code=500, detail="Server missing CODECOMPANION_TOKEN"
        )
    if provided != TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    return None


# --- Friendly homepage so the root URL isn't a 404 ---
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <head><title>CodeCompanion</title></head>
      <body style="font-family: system-ui; text-align: center; padding: 48px;">
        <h1 style="margin:0 0 8px 0;">
          <a href="/" style="text-decoration:none;color:inherit">
            ✅ CodeCompanion API is running 🇬🇧
          </a>
        </h1>
        <div style="margin: 4px 0 16px 0; font-size: 14px; opacity: 0.9;">English (UK)</div>
        <p style="margin:0 0 16px 0;">Endpoints:</p>
        <ul style="list-style: none; padding: 0;">
          <li><code>GET /health</code> (no auth)</li>
          <li><code>GET /keys</code> (requires token)</li>
          <li><code>POST /run_real</code> (requires token)</li>
        </ul>
      </body>
    </html>
    """


# --- Health (open) ---
@app.get("/health")
async def health():
    return {"ok": True, "event_bus": settings.EVENT_BUS}


# --- Keys (protected) ---
@app.get("/keys", dependencies=[Depends(require_token)])
async def keys():
    return {
        "claude": bool(settings.ANTHROPIC_API_KEY),
        "gpt4": bool(settings.OPENAI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
    }


# --- Run real pipeline (protected) ---
@app.post("/run_real", dependencies=[Depends(require_token)])
async def run_real(body: dict = Body(...)):
    objective = (body.get("objective") or "").strip()
    if not objective:
        raise HTTPException(status_code=400, detail="objective is required")
    try:
        return await real_e2e(objective)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="pipeline failed")
