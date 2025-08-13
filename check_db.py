#!/usr/bin/env python3

from storage.runs import init, _conn

# Initialize database tables first
init()

with _conn() as c:
    print("=== RUNS TABLE ===")
    runs = c.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 5").fetchall()
    for run in runs:
        print(f"ID: {run[0]}, Objective: {run[1]}, Created: {run[2]}")

    print("\n=== ARTIFACTS TABLE ===")
    artifacts = c.execute(
        "SELECT run_id, kind, agent, confidence FROM artifacts LIMIT 10"
    ).fetchall()
    for art in artifacts:
        print(f"Run: {art[0]}, Type: {art[1]}, Agent: {art[2]}, Confidence: {art[3]}")
