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
def ping():
    """Fast health check for latency testing."""
    start = time.time()
    # Quick system check
    typer.echo("pong")
    duration = time.time() - start
    typer.echo(f"response_time: {duration:.4f}s", err=True)

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

@app.command()
def git_push(folder: str,
             repo_url: Optional[str] = typer.Option(None, help="git remote URL (e.g., https://github.com/you/repo.git)"),
             message: str = typer.Option("CodeCompanion commit", help="commit message")):
    """
    Init git (if needed), add/commit all, set remote (if provided), and push.
    Requires GITHUB_TOKEN if using https with token embedding or preconfigured credentials.
    """
    import subprocess, shlex, os, pathlib
    p = pathlib.Path(folder).resolve()
    if not p.exists():
        raise typer.BadParameter(f"Folder not found: {p}")

    def run(cmd):
        typer.echo(f"$ {cmd}")
        # Convert string command to list for shell=False (more secure)
        if isinstance(cmd, str):
            cmd_list = shlex.split(cmd)
        else:
            cmd_list = cmd
        res = subprocess.run(cmd_list, shell=False, cwd=str(p), capture_output=True, text=True)
        if res.stdout: typer.echo(res.stdout.strip())
        if res.stderr: typer.echo(res.stderr.strip())
        if res.returncode != 0:
            raise typer.Exit(res.returncode)

    if not (p / ".git").exists():
        run("git init")
        # set default identity if missing
        run('git config user.name "codecompanion"')
        run('git config user.email "codecompanion@local"')

    run("git add -A")
    # allow empty commit to create initial history
    run(f'git commit -m {shlex.quote(message)} || true')

    if repo_url:
        run("git remote remove origin || true")
        # support token env
        token = os.getenv("GITHUB_TOKEN")
        if token and repo_url.startswith("https://"):
            # embed token into URL for non-interactive push
            repo_url = repo_url.replace("https://", f"https://{token}:x-oauth-basic@")
        run(f'git remote add origin {shlex.quote(repo_url)} || true')
        run("git push -u origin HEAD || true")

    typer.echo("✅ Git push step finished")

if __name__ == "__main__":
    app()