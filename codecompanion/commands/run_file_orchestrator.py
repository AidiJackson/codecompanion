"""
CLI command for running the File Orchestrator.
"""
from ..orchestrator import Orchestrator


def run_file_orchestrator_command(args):
    """
    Execute the File Orchestrator to collect all agent outputs.

    Args:
        args: Command-line arguments (not used currently)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    orchestrator = Orchestrator()
    result = orchestrator.run_file_orchestrator()

    print("Build completed.")
    print(f"Output folder: {result['output_dir']}")

    return 0
