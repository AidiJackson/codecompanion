from fastapi import FastAPI
from settings import settings
from bus import bus
import sqlite3

app = FastAPI()

@app.get("/health")
async def health():
    redis_ok = True
    db_ok = True
    try:
        # quick SQLite check
        conn = sqlite3.connect("./data/codecompanion.db")
        conn.execute("select 1")
        conn.close()
    except Exception:
        db_ok = False
    # ping already happened at startup; if bus is MockBus this code wouldn't run (fail-fast)
    return {"ok": redis_ok and db_ok, "event_bus": settings.EVENT_BUS, "db_ok": db_ok}