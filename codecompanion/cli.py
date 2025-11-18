import os
import argparse
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent
from .commands.run_file_orchestrator import run_file_orchestrator_command
from .commands.init import init_command
from .commands.architect import architect_command
from .commands.specialist import specialist_command
from .commands.quality import quality_command
from .commands.state import state_command


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
        "--build", action="store_true", help="Run File Orchestrator to collect agent outputs"
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("CC_PROVIDER", "claude"),
        help="LLM provider (claude, gpt4, gemini)",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init subcommand
    subparsers.add_parser("init", help="Initialize the project")

    # architect subcommand
    subparsers.add_parser("architect", help="Run the Architect agent")

    # specialist subcommand
    specialist_parser = subparsers.add_parser("specialist", help="Run a Specialist agent")
    specialist_parser.add_argument("--type", required=True, help="Type of specialist (backend, frontend, docs, test)")

    # quality subcommand
    subparsers.add_parser("quality", help="Run the Quality agent")

    # build subcommand
    subparsers.add_parser("build", help="Run File Orchestrator to collect agent outputs")

    # state subcommand
    subparsers.add_parser("state", help="Display current state")

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

    # Handle subcommands
    if args.command == "init":
        return init_command(args)
    if args.command == "architect":
        return architect_command(args)
    if args.command == "specialist":
        return specialist_command(args)
    if args.command == "quality":
        return quality_command(args)
    if args.command == "build":
        return run_file_orchestrator_command(args)
    if args.command == "state":
        return state_command(args)

    # Handle legacy flags
    if args.chat:
        return chat_repl(provider=args.provider)
    if args.auto:
        return run_pipeline(provider=args.provider)
    if args.run:
        return run_single_agent(args.run, provider=args.provider)
    if args.build:
        return run_file_orchestrator_command(args)

    # default help
    parser.print_help()
    return 0
