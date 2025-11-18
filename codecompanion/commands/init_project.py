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


def get_default_settings() -> Dict[str, Any]:
    """
    Get default project settings.

    Returns:
        Dictionary containing default project settings
    """
    return {
        "provider": "claude",
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "temperature": 0.7,
        "features": {
            "auto_architect": False,
            "auto_specialist": False,
            "quality_gates": True,
        },
    }


def init_command(args: argparse.Namespace) -> int:
    """
    Initialize a CodeCompanion project.

    Creates .codecompanion_state.json and .codecompanion_settings.json files with default configuration.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    state_file = ".codecompanion_state.json"
    settings_file = ".codecompanion_settings.json"

    # Check if files already exist
    files_exist = os.path.exists(state_file) or os.path.exists(settings_file)
    if files_exist:
        print(f"[init] Warning: Project files already exist")
        response = input("[init] Overwrite? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("[init] Initialization cancelled")
            return 1

    # Create default state and settings
    state = get_default_state()
    settings = get_default_settings()

    try:
        # Write state file
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        # Write settings file
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        # Get absolute paths for output
        state_path = os.path.abspath(state_file)
        settings_path = os.path.abspath(settings_file)

        # Print required output
        print("CodeCompanion project initialised.")
        print(f"State file: {state_path}")
        print(f"Settings file: {settings_path}")

        return 0

    except Exception as e:
        print(f"[init] Error: Failed to create project files: {e}")
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
