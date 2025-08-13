from typing import List, Dict, Any
import sqlite3
import time
import os

DB = "./data/codecompanion.db"
os.makedirs("./data", exist_ok=True)


def _conn():
    return sqlite3.connect(DB)


def _col_exists(cursor, table: str, col: str) -> bool:
    rows = cursor.execute("PRAGMA table_info(?)", (table,)).fetchall()
    names = {r[1] for r in rows}
    return col in names


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
          content TEXT
        )""")
        # migration: add missing columns if table already existed
        # (SQLite allows ADD COLUMN without default)
        try:
            if not _col_exists(c, "artifacts", "run_id"):
                c.execute("ALTER TABLE artifacts ADD COLUMN run_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column may already exist
        try:
            if not _col_exists(c, "artifacts", "idx"):
                c.execute("ALTER TABLE artifacts ADD COLUMN idx INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            if not _col_exists(c, "artifacts", "kind"):
                c.execute("ALTER TABLE artifacts ADD COLUMN kind TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            if not _col_exists(c, "artifacts", "agent"):
                c.execute("ALTER TABLE artifacts ADD COLUMN agent TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            if not _col_exists(c, "artifacts", "confidence"):
                c.execute("ALTER TABLE artifacts ADD COLUMN confidence REAL")
        except sqlite3.OperationalError:
            pass
        try:
            if not _col_exists(c, "artifacts", "content"):
                c.execute("ALTER TABLE artifacts ADD COLUMN content TEXT")
        except sqlite3.OperationalError:
            pass
        # helpful index
        try:
            c.execute(
                "CREATE INDEX IF NOT EXISTS ix_artifacts_run ON artifacts(run_id, idx)"
            )
        except Exception:
            pass


def save_run(run_id: str, objective: str, artifacts: List[Dict[str, Any]]):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO runs(id, objective, created_at) VALUES (?,?,?)",
            (run_id, objective, time.strftime("%Y-%m-%d %H:%M:%S")),
        )
        for i, a in enumerate(artifacts):
            # Check if we have the old schema with project_id or new schema
            cursor = c.cursor()
            cursor.execute("PRAGMA table_info(artifacts)")
            columns = {col[1] for col in cursor.fetchall()}

            if "project_id" in columns:
                # Use old schema - insert with all required columns
                c.execute(
                    """INSERT INTO artifacts(project_id, artifact_type, title, content, agent_name, run_id, idx, kind, agent, confidence)
                             VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        run_id,
                        a.get("type", "Unknown"),
                        a.get("type", "Untitled"),
                        a.get("content", ""),
                        a.get("agent", "Unknown"),
                        run_id,
                        i,
                        a.get("type"),
                        a.get("agent"),
                        float(a.get("confidence", 0.75)),
                    ),
                )
            else:
                # Use new schema
                c.execute(
                    """INSERT INTO artifacts(run_id, idx, kind, agent, confidence, content)
                             VALUES (?,?,?,?,?,?)""",
                    (
                        run_id,
                        i,
                        a.get("type"),
                        a.get("agent"),
                        float(a.get("confidence", 0.75)),
                        a.get("content", ""),
                    ),
                )


def load_runs(limit=20):
    with _conn() as c:
        return c.execute(
            "SELECT id, objective, created_at FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


def load_artifacts(run_id: str):
    with _conn() as c:
        # Check schema and adapt query accordingly
        cursor = c.cursor()
        cursor.execute("PRAGMA table_info(artifacts)")
        columns = {col[1] for col in cursor.fetchall()}

        if "project_id" in columns:
            # Old schema - map old columns to new format
            return c.execute(
                "SELECT artifact_type as kind, agent_name as agent, confidence, content FROM artifacts WHERE run_id=? ORDER BY idx ASC",
                (run_id,),
            ).fetchall()
        else:
            # New schema
            return c.execute(
                "SELECT kind, agent, confidence, content FROM artifacts WHERE run_id=? ORDER BY idx ASC",
                (run_id,),
            ).fetchall()
