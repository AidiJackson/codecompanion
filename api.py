import logging, traceback
from fastapi import FastAPI, Body
from settings import settings
from services.real_models import real_e2e

log = logging.getLogger("api")
app = FastAPI()

@app.get("/health")
async def health():
    return {"ok": True, "event_bus": settings.EVENT_BUS}

@app.get("/keys")
async def keys():
    return {
        "claude": bool(settings.ANTHROPIC_API_KEY),
        "gpt4": bool(settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
    }

@app.post("/run_real")
async def run_real(body: dict = Body(...)):
    try:
        objective = (body.get("objective") or "").strip()
        if not objective:
            return {"error": "objective is required"}
        result = await real_e2e(objective)
        
        # Save to database
        from storage.runs import init, save_run
        init()
        save_run(result["run_id"], objective, result["artifacts"])
        
        return result
    except Exception as e:
        tb = traceback.format_exc(limit=6)
        log.exception("run_real failed: %s", e)
        return {"error": str(e), "trace": tb}, 500