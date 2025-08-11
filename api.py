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
        "gpt4": bool(settings.OPENAI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
    }

@app.post("/run_real")
async def run_real(body: dict = Body(...)):
    try:
        objective = (body.get("objective") or "").strip()
        if not objective:
            return {"error": "objective is required"}
        result = await real_e2e(objective)   # returns {"run_id": ..., "artifacts": [...]}

        # Try to persist, but never fail the request if DB write has an issue
        try:
            from storage.runs import init, save_run
            init()
            save_run(result["run_id"], objective, result["artifacts"])
        except Exception as e:
            import logging, traceback
            logging.getLogger("api").warning("save_run failed: %s\n%s", e, traceback.format_exc(limit=4))
            result["persist_warning"] = str(e)

        return result
    except Exception as e:
        import traceback, logging
        logging.getLogger("api").exception("run_real failed: %s", e)
        return {"error": str(e), "trace": traceback.format_exc(limit=6)}, 500