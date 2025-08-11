# api.py — CodeCompanion API (token-protected)
import os
from fastapi import FastAPI, Body, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from settings import settings
from services.real_models import real_e2e

TOKEN = os.getenv("CODECOMPANION_TOKEN")

app = FastAPI(title="CodeCompanion API")

# Allow CLI calls from anywhere; token enforces auth.
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
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization.split(" ", 1)[1].strip()
    elif x_api_key:
        provided = x_api_key.strip()

    if not TOKEN:
        raise HTTPException(status_code=500, detail="Server missing CODECOMPANION_TOKEN")
    if provided != TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing token")

@app.get("/health")
async def health():
    return {"ok": True, "event_bus": settings.EVENT_BUS}

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
    return await real_e2e(objective)