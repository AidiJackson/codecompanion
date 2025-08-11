from dataclasses import dataclass
from typing import List, Dict, Any
import sqlite3, json, time, os

DB = "./data/codecompanion.db"
os.makedirs("./data", exist_ok=True)

def _conn():
    return sqlite3.connect(DB)

def init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY,
          objective TEXT,
          created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS artifacts (
          run_id TEXT,
          idx INTEGER,
          kind TEXT,
          agent TEXT,
          confidence REAL,
          content TEXT,
          FOREIGN KEY(run_id) REFERENCES runs(id)
        )""")

def save_run(run_id: str, objective: str, artifacts: List[Dict[str,Any]]):
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO runs(id, objective, created_at) VALUES (?,?,?)",
                  (run_id, objective, time.strftime("%Y-%m-%d %H:%M:%S")))
        for i,a in enumerate(artifacts):
            c.execute("""INSERT INTO artifacts(run_id, idx, kind, agent, confidence, content)
                         VALUES (?,?,?,?,?,?)""",
                      (run_id, i, a["type"], a["agent"], a.get("confidence",0.75), a["content"]))

def load_runs(limit=20):
    with _conn() as c:
        return c.execute("SELECT id, objective, created_at FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()

def load_artifacts(run_id: str):
    with _conn() as c:
        return c.execute("SELECT kind, agent, confidence, content FROM artifacts WHERE run_id=? ORDER BY idx ASC", (run_id,)).fetchall()