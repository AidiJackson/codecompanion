import os
import sys
import argparse
import json
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent


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

    # Add subcommands for new functionality
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize CodeCompanion project")

    # run command with subcommands
    run_parser = subparsers.add_parser("run", help="Run a specific agent")
    run_parser.add_argument("agent", help="Agent to run (e.g., 'architect', 'specialist')")
    run_parser.add_argument("--type", help="Specialist type (backend, frontend, docs, test)")

    # state command
    state_parser = subparsers.add_parser("state", help="Show current workflow state")

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

    # Handle new subcommands
    if args.command == "init":
        return cmd_init(info)
    elif args.command == "run":
        if args.agent == "architect":
            from .commands.run_architect import run_architect_command
            return run_architect_command(args)
        elif args.agent == "specialist":
            if not hasattr(args, 'type') or args.type is None:
                print("Error: --type is required for specialist agent", file=sys.stderr)
                print("Valid types: backend, frontend, docs, test", file=sys.stderr)
                return 1
            from .commands.run_specialist import run_specialist_command
            return run_specialist_command(args)
        else:
            print(f"Unknown agent: {args.agent}")
            return 1
    elif args.command == "state":
        return cmd_state()

    # Handle legacy flags
    if args.chat:
        return chat_repl(provider=args.provider)
    if args.auto:
        return run_pipeline(provider=args.provider)
    if args.run:
        return run_single_agent(args.run, provider=args.provider)

    # default help
    parser.print_help()
    return 0


def cmd_init(info: dict) -> int:
    """Initialize CodeCompanion project."""
    print("[codecompanion] Project initialized successfully")
    print(f"[codecompanion] Bootstrap dir: {info['dir']}")
    if info["created"]:
        print(f"[codecompanion] Created: {', '.join(info['created'])}")
    print(f"[codecompanion] Agents dir: {info['agents_dir']}")
    return 0


def cmd_state() -> int:
    """Show current workflow state."""
    from .orchestrator import Orchestrator

    try:
        orchestrator = Orchestrator()
        state = orchestrator.get_state()
        print(json.dumps(state, indent=2))
        return 0
    except Exception as e:
        print(f"Error loading state: {e}")
        return 1
