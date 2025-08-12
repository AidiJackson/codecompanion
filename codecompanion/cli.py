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
    parser.add_argument("--provider", default=os.getenv("CC_PROVIDER","claude"), help="LLM provider (claude, gpt4, gemini)")
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