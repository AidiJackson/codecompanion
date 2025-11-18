"""
Run Architect command - Execute the Architect agent.
"""
import sys
from typing import Any

from ..orchestrator import Orchestrator


def run_architect_command(args: Any) -> int:
    """
    Execute the Architect agent to generate architecture documentation.

    Args:
        args: Command-line arguments (unused for now)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create orchestrator and run architect
        orchestrator = Orchestrator()
        result = orchestrator.run_architect()

        # Print results
        print("Architect agent executed successfully.")
        print(f"Architecture file: {result['architecture_file']}")
        print(f"Phases file: {result['phases_file']}")
        print(f"Architecture version: {result['version']}")

        return 0

    except Exception as e:
        print(f"Error running architect: {e}", file=sys.stderr)
        return 1
