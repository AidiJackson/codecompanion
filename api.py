# api.py — CodeCompanion API (token-protected)

import os
from fastapi import FastAPI, Body, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# Your existing imports; keep them if already present:
from settings import settings
from services.real_models import real_e2e

TOKEN = os.getenv("CODECOMPANION_TOKEN")

app = FastAPI(title="CodeCompanion API")

# Allow CLI calls from anywhere. Security is enforced by the token below.
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
    Accept either header:
      - Authorization: Bearer <token>
      - X-API-Key: <token>
    """
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization.split(" ", 1)[1].strip()
    elif x_api_key:
        provided = x_api_key.strip()

    if not TOKEN:
        raise HTTPException(status_code=500, detail="Server missing CODECOMPANION_TOKEN")
    if provided != TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

# Health stays open so you can ping without a token
@app.get("/health")
async def health():
    return {"ok": True, "event_bus": settings.EVENT_BUS}

# Keys & main endpoint require token
@app.get("/keys", dependencies=[Depends(require_token)])
async def keys():
    return {
        "claude": bool(settings.ANTHROPIC_API_KEY),
        "gpt4": bool(settings.OPENAI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
    }

@app.post("/run_real", dependencies=[Depends(require_token)])
async def run_real(body: dict = Body(...)):
    objective = (body.get("objective") or "").strip()
    if not objective:
        raise HTTPException(status_code=400, detail="objective is required")
    result = await real_e2e(objective)
    return result