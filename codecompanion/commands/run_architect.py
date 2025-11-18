"""
Run architect agent command.

Executes the architect agent through the orchestrator.
"""

import argparse
from ..orchestrator import Orchestrator


def run_architect_command(args: argparse.Namespace) -> int:
    """
    Run the architect agent.

    The architect agent performs high-level architectural analysis and planning.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        orchestrator = Orchestrator()
        return orchestrator.run_architect()
    except Exception as e:
        print(f"[architect] Error: {e}")
        return 1


def setup_run_architect_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up argument parser for run architect command.

    Args:
        subparsers: Subparser action from main argument parser
    """
    parser = subparsers.add_parser(
        "architect",
        help="Run the architect agent",
        description="Execute the architect agent to perform architectural analysis and planning.",
    )
    parser.set_defaults(func=run_architect_command)
