"""
Run Quality command - Execute quality gate checks.
"""
import sys
from typing import Any

from ..orchestrator import Orchestrator


def run_quality_command(args: Any) -> int:
    """
    Execute quality gate checks on the project.

    Args:
        args: Command-line arguments (unused for now)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create orchestrator and run quality checks
        orchestrator = Orchestrator()
        result = orchestrator.run_quality()

        # Print results
        print("Quality check completed successfully.")
        print(f"Report file: {result['report_file']}")

        return 0

    except Exception as e:
        # Handle errors
        print(f"Error running quality checks: {e}", file=sys.stderr)
        return 1
