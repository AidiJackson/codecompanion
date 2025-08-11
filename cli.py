import typer
import requests
import json
from typing import List

app = typer.Typer()

API_URL = "http://0.0.0.0:5050"  # Change this if deployed elsewhere

@app.command()
def run(
    objective: List[str] = typer.Argument(..., metavar="OBJECTIVE...", help="Your goal text")
):
    """
    Run the real agents with a goal.

    Examples:
      python cli.py run "Build a hello world app"
      python cli.py run Build a hello world app
    """
    goal = " ".join(objective).strip()
    if not goal:
        typer.echo("Usage: python cli.py run <your objective text>")
        raise typer.Exit(1)

    typer.echo(f"🎯 Sending to CodeCompanion: {goal}")

    # Check API health first so we give a friendly error
    try:
        h = requests.get(f"{API_URL}/health", timeout=3)
        if h.status_code != 200:
            typer.echo(f"💥 API /health returned {h.status_code}. Is the server running?")
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"💥 Could not reach API on {API_URL} — is the app running?\nError: {e}")
        raise typer.Exit(1)

    # Call /run_real
    try:
        res = requests.post(f"{API_URL}/run_real", json={"objective": goal}, timeout=180)
    except Exception as e:
        typer.echo(f"💥 Network error calling /run_real: {e}")
        raise typer.Exit(1)

    if res.status_code != 200:
        try:
            data = res.json()
        except Exception:
            data = {"raw": res.text}
        typer.echo(f"❌ API error {res.status_code}")
        typer.echo(json.dumps(data, indent=2))
        raise typer.Exit(1)

    data = res.json()
    artifacts = data.get("artifacts") or []
    if not artifacts:
        typer.echo("⚠ No artifacts returned:")
        typer.echo(json.dumps(data, indent=2))
        raise typer.Exit(1)

    typer.echo("✅ Agents finished. Artifacts:\n")
    for a in artifacts:
        t = a.get("type", "?")
        ag = a.get("agent", "?")
        conf = a.get("confidence", 0)
        content = a.get("content", "")
        typer.echo(f"--- {t} by {ag} (conf {conf:.2f}) ---")
        typer.echo(content[:4000])  # avoid flooding the terminal
        typer.echo("\n")

if __name__ == "__main__":
    app()