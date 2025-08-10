from fastapi import FastAPI, Body
from settings import settings
from bus import bus, Event
from constants import TOPIC_TASKS
import sqlite3, uuid

app = FastAPI()

@app.get("/health")
async def health():
    # DB check
    db_ok = True
    try:
        conn = sqlite3.connect("./data/codecompanion.db")
        conn.execute("select 1")
        conn.close()
    except Exception:
        db_ok = False
    # If bus is created, assume redis configured (ping done at startup)
    return {"ok": db_ok, "event_bus": settings.EVENT_BUS, "db_ok": db_ok}

@app.post("/simulate_task")
async def simulate_task(obj: dict = Body(default={"objective":"demo"})):
    task_id = f"T-{uuid.uuid4().hex[:8]}"
    payload = {"task_id": task_id, "task_type": "demo", "objective": obj.get("objective","demo")}
    await bus.publish(Event(topic=TOPIC_TASKS, payload=payload))
    return {"task_id": task_id}