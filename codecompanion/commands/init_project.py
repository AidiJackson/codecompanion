"""
Project initialization command.

Initializes a CodeCompanion project by creating the state file with defaults.
"""

import argparse
import json
import os
from typing import Dict, Any


def get_default_state() -> Dict[str, Any]:
    """
    Get default project state.

    Returns:
        Dictionary containing default project state
    """
    return {
        "initialized": True,
        "version": "1.0.0",
        "architecture": {},
        "specialists_run": [],
        "quality_reports": [],
        "config": {
            "state_file": ".codecompanion_state.json",
            "auto_save": True,
        },
    }


def init_command(args: argparse.Namespace) -> int:
    """
    Initialize a CodeCompanion project.

    Creates a .codecompanion_state.json file with default configuration.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    state_file = ".codecompanion_state.json"

    # Check if state file already exists
    if os.path.exists(state_file):
        print(f"[init] Warning: {state_file} already exists")
        response = input("[init] Overwrite? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("[init] Initialization cancelled")
            return 1

    # Create default state
    state = get_default_state()

    try:
        # Write state file
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        print(f"[init] Created {state_file}")
        print("[init] Project initialized successfully")
        print()
        print("Next steps:")
        print("  1. Run 'cc run architect' to analyze project architecture")
        print("  2. Run 'cc run specialist --type <frontend|backend|test|docs>' to run specialists")
        print("  3. Run 'cc quality' to check quality gates")
        print("  4. Run 'cc state' to view project state")

        return 0

    except Exception as e:
        print(f"[init] Error: Failed to create state file: {e}")
        return 1


def setup_init_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up argument parser for init command.

    Args:
        subparsers: Subparser action from main argument parser
    """
    parser = subparsers.add_parser(
        "init",
        help="Initialize a CodeCompanion project",
        description="Initialize a new CodeCompanion project by creating a state file with default configuration.",
    )
    parser.set_defaults(func=init_command)
