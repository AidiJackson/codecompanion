"""
Run Specialist command - Execute a specialist agent.
"""
import sys
from typing import Any

from ..orchestrator import Orchestrator


def run_specialist_command(args: Any) -> int:
    """
    Execute a specialist agent to generate specialized analysis.

    Args:
        args: Command-line arguments containing 'type' attribute

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Get specialist type from args
        specialist_type = args.type

        # Create orchestrator and run specialist
        orchestrator = Orchestrator()
        result = orchestrator.run_specialist(specialist_type)

        # Print results
        print(f"Specialist '{specialist_type}' executed successfully.")
        print(f"Output file: {result['output_file']}")

        return 0

    except ValueError as e:
        # Handle unknown specialist type
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        # Handle other errors
        print(f"Error running specialist: {e}", file=sys.stderr)
        return 1
