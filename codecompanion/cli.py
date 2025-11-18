"""
CodeCompanion CLI - Main entry point.

Provides a command-line interface for CodeCompanion with support for:
- Project initialization
- Architect agent execution
- Specialist agent execution
- Quality gate validation
- State management
- Legacy agent execution (for backward compatibility)
"""

import os
import argparse
from typing import Optional
from .bootstrap import ensure_bootstrap
from . import __version__
from .repl import chat_repl
from .runner import run_pipeline, run_single_agent
from .commands.init_project import setup_init_parser
from .commands.run_architect import setup_run_architect_parser
from .commands.run_specialist import setup_run_specialist_parser
from .commands.run_quality import setup_run_quality_parser
from .commands.show_state import setup_show_state_parser


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="codecompanion",
        description="CodeCompanion – AI-powered development companion with specialized agents.",
        epilog="For more information, visit: https://github.com/codecompanion",
    )

    # Global flags
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check environment and bootstrap presence, then exit",
    )

    # Legacy flags (for backward compatibility)
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start chat REPL"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run full 10-agent pipeline"
    )
    parser.add_argument(
        "--run",
        metavar="AGENT",
        help="Run a single legacy agent by name"
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("CC_PROVIDER", "claude"),
        help="LLM provider (claude, gpt4, gemini) for legacy agents",
    )

    # Create subparsers for new commands
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        help="Command to execute",
    )

    # Set up subcommands
    setup_init_parser(subparsers)

    # Create 'run' subcommand with its own subparsers
    run_parser = subparsers.add_parser(
        "run",
        help="Run agents",
        description="Execute architect or specialist agents.",
    )
    run_subparsers = run_parser.add_subparsers(
        title="agent types",
        description="Available agent types to run",
        dest="agent_type",
        help="Agent type to execute",
    )

    setup_run_architect_parser(run_subparsers)
    setup_run_specialist_parser(run_subparsers)

    # Set up other commands
    setup_run_quality_parser(subparsers)
    setup_show_state_parser(subparsers)

    return parser


def handle_legacy_flags(args: argparse.Namespace) -> Optional[int]:
    """
    Handle legacy command-line flags for backward compatibility.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code if a legacy flag was handled, None otherwise
    """
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

    return None


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Handle legacy flags first (for backward compatibility)
    legacy_result = handle_legacy_flags(args)
    if legacy_result is not None:
        return legacy_result

    # Handle new subcommands
    if hasattr(args, "func"):
        try:
            return args.func(args)
        except Exception as e:
            print(f"[error] Command failed: {e}")
            return 1

    # No command specified, show help
    parser.print_help()
    return 0
