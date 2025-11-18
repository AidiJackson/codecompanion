import os
import argparse
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent
from .commands.show_info import show_info_command


def main():
    parser = argparse.ArgumentParser(
        prog="codecompanion",
        description="CodeCompanion – standalone agent runner & chat REPL (OpenRouter-backed).",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check environment and bootstrap presence, then exit",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show system information panel (Control Tower view)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw JSON (use with --info)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Start the CodeCompanion web dashboard (FastAPI)",
    )
    parser.add_argument(
        "--dashboard-port",
        type=int,
        default=8008,
        help="Port for the dashboard server (default: 8008)",
    )
    parser.add_argument("--chat", action="store_true", help="Start chat REPL")
    parser.add_argument(
        "--auto", action="store_true", help="Run full 10-agent pipeline"
    )
    parser.add_argument("--run", metavar="AGENT", help="Run a single agent by name")
    parser.add_argument(
        "--provider",
        default=os.getenv("CC_PROVIDER", "claude"),
        help="LLM provider (claude, gpt4, gemini)",
    )
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    info = ensure_bootstrap()

    if args.info:
        show_info_command(raw=args.raw)
        return 0

    if args.dashboard:
        # Import uvicorn only when needed to avoid dependency issues
        try:
            import uvicorn
            from .dashboard import create_dashboard_app
        except ImportError as e:
            print(f"[error] Dashboard dependencies not installed: {e}")
            print("[error] Install with: pip install fastapi uvicorn jinja2")
            return 1

        print(f"[codecompanion] Starting dashboard on http://127.0.0.1:{args.dashboard_port}")
        print("[codecompanion] Press Ctrl+C to stop")
        app = create_dashboard_app()
        uvicorn.run(app, host="127.0.0.1", port=args.dashboard_port)
        return 0

    if args.check:
        print("[codecompanion] OK. Bootstrap dir:", info["dir"])
        if info["created"]:
            print("[codecompanion] Created:", ", ".join(info["created"]))
        print("[codecompanion] Agents dir:", info["agents_dir"])
        print("[codecompanion] Provider:", args.provider)
        return 0

    if args.chat:
        return chat_repl(provider=args.provider)
    if args.auto:
        return run_pipeline(provider=args.provider)
    if args.run:
        return run_single_agent(args.run, provider=args.provider)
    # default help
    parser.print_help()
    return 0
