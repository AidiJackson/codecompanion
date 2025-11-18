"""
Run quality gates command.

Executes quality checks and displays quality reports.
"""

import argparse
from ..quality_gates import QualityGates


def run_quality_command(args: argparse.Namespace) -> int:
    """
    Run quality gates.

    Executes all quality checks and generates a report.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        gates = QualityGates()
        return gates.run_quality_checks()
    except Exception as e:
        print(f"[quality] Error: {e}")
        return 1


def setup_run_quality_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up argument parser for quality command.

    Args:
        subparsers: Subparser action from main argument parser
    """
    parser = subparsers.add_parser(
        "quality",
        help="Run quality gates and display report",
        description="Execute quality checks and generate a quality report.",
    )
    parser.set_defaults(func=run_quality_command)
