from fastapi import FastAPI, Body
from settings import settings
from services.real_models import real_e2e

app = FastAPI()

@app.post("/run_real")
async def run_real(body: dict = Body(...)):
    objective = (body.get("objective") or "").strip()
    if not objective:
        return {"error": "objective is required"}
    artifacts = await real_e2e(objective)
    return {"artifacts": artifacts, "models": settings.get_available_models()}