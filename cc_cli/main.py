import asyncio, os, json, time, pathlib, typer, re
from typing import Optional
from services.real_models import real_e2e
from storage.runs import init, save_run

app = typer.Typer(help="CodeCompanion CLI")

def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    return s or f"cc-{int(time.time())}"

@app.command()
def check():
    """Print model key availability."""
    ok = {
        "claude": bool(os.getenv("ANTHROPIC_API_KEY")),
        "gpt4": bool(os.getenv("OPENAI_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
    }
    typer.echo(json.dumps(ok, indent=2))

@app.command()
def run(objective: str, outdir: Optional[str] = typer.Option(None, help="Folder to write artifacts")):
    """Call real models and save artifacts locally + DB."""
    async def go():
        res = await real_e2e(objective)
        return res
    res = asyncio.run(go())
    run_id = res["run_id"]
    arts = res["artifacts"]

    # persist to DB
    init()
    try:
        save_run(run_id, objective, arts)
    except Exception as e:
        typer.echo(f"warn: db save failed: {e}")

    # write to disk
    root = pathlib.Path(outdir or f"./output/{slugify(objective)}-{run_id}")
    root.mkdir(parents=True, exist_ok=True)
    # split artifacts into files
    for a in arts:
        kind = a["type"].lower()
        fname = {
            "specdoc": "SPEC.md",
            "codedoc": "CODE.md",
            "codepatch": "PATCH.diff",
            "designdoc": "DESIGN.md",
            "testplan": "TESTPLAN.md",
            "evalreport": "EVAL.md",
        }.get(kind, f"{kind}.md")
        (root / fname).write_text(a["content"] or "", encoding="utf-8")
    # bundle a manifest
    (root / "manifest.json").write_text(json.dumps({"run_id": run_id, "objective": objective, "artifacts": arts}, indent=2), encoding="utf-8")

    typer.echo(f"✅ Saved artifacts to {root}")

if __name__ == "__main__":
    app()