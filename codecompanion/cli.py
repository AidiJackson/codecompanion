import os, sys, argparse, textwrap
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent

def main():
    parser = argparse.ArgumentParser(
        prog="codecompanion",
        description="CodeCompanion – standalone agent runner & chat REPL (OpenRouter-backed)."
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--check", action="store_true", help="Check environment and bootstrap presence, then exit")
    parser.add_argument("--chat", action="store_true", help="Start chat REPL")
    parser.add_argument("--auto", action="store_true", help="Run full 10-agent pipeline")
    parser.add_argument("--run", metavar="AGENT", help="Run a single agent by name")
    parser.add_argument("--model", default=os.getenv("CC_MODEL","openrouter/auto"), help="Model ID for LLM calls")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    info = ensure_bootstrap()
    if args.check:
        print("[codecompanion] OK. Bootstrap dir:", info["dir"])
        if info["created"]:
            print("[codecompanion] Created:", ", ".join(info["created"]))
        print("[codecompanion] Agents dir:", info["agents_dir"])
        print("[codecompanion] Model:", args.model)
        return 0

    if args.chat:
        return chat_repl(model=args.model)
    if args.auto:
        return run_pipeline(model=args.model)
    if args.run:
        return run_single_agent(args.run, model=args.model)
    # default help
    parser.print_help()
    return 0