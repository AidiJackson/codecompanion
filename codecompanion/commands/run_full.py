"""
Full end-to-end workflow command for CodeCompanion.
Executes the complete pipeline: init → architect → specialists → quality → build
"""

import sys
from codecompanion.orchestrator import Orchestrator


def run_full_command(args):
    """
    Execute the full CodeCompanion workflow pipeline.

    Workflow executed in this exact sequence:
    1) init (if no state/settings)
    2) architect
    3) specialists (backend, frontend, docs, test)
    4) quality
    5) build

    Args:
        args: Command line arguments (not used currently)

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Create orchestrator instance
    orchestrator = Orchestrator()

    # Run the full pipeline
    result = orchestrator.run_full_pipeline()

    # Check result
    if result["status"] == "success":
        print("=" * 60)
        print("FULL RUN COMPLETED SUCCESSFULLY")
        print(f"Output folder: {result['output_dir']}")
        print("=" * 60)
        return 0
    else:
        # Error already printed during pipeline execution
        return 1
