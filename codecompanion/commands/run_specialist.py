"""
Run specialist agent command.

Executes specialist agents for different domains.
"""

import argparse
from ..specialist_loader import SpecialistAgentLoader, SpecialistType


def run_specialist_command(args: argparse.Namespace) -> int:
    """
    Run a specialist agent.

    Loads and executes the specified specialist agent.

    Args:
        args: Command-line arguments containing specialist type

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    specialist_type: SpecialistType = args.type

    try:
        # Load the specialist agent
        agent = SpecialistAgentLoader.load(specialist_type)

        # Run the agent
        return agent.run()

    except Exception as e:
        print(f"[specialist] Error: {e}")
        return 1


def setup_run_specialist_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up argument parser for run specialist command.

    Args:
        subparsers: Subparser action from main argument parser
    """
    parser = subparsers.add_parser(
        "specialist",
        help="Run a specialist agent",
        description="Execute a specialist agent for a specific domain (frontend, backend, test, docs).",
    )
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        choices=["frontend", "backend", "test", "docs"],
        help="Type of specialist to run",
    )
    parser.set_defaults(func=run_specialist_command)
