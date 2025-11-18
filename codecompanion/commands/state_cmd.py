"""
State Command - Show Current State

This command shows the current CodeCompanion state and settings.
"""

import json
from ..settings import load_settings, get_state_info


def state_command(args=None) -> int:
    """
    Display current CodeCompanion state and settings.

    Args:
        args: Command line arguments (from argparse)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        settings = load_settings()
        state_info = get_state_info(settings)

        print("\nCodeCompanion State")
        print("=" * 50)
        print(f"Project Name:        {state_info['project_name']}")
        print(f"Project Root:        {state_info['project_root']}")
        print(f"Model Policy Mode:   {state_info['model_policy_mode']}")
        print(f"Model Policy Path:   {state_info['model_policy_path']}")
        print(f"Default Provider:    {state_info['default_provider']}")
        print("=" * 50)
        print()

        return 0
    except Exception as e:
        print(f"ERROR: Failed to get state: {e}")
        import traceback
        traceback.print_exc()
        return 1


def add_state_subcommand(subparsers):
    """
    Add the 'state' subcommand to the CLI.

    Args:
        subparsers: The subparsers object from argparse
    """
    state_parser = subparsers.add_parser(
        "state",
        help="Show current state and settings"
    )
    state_parser.set_defaults(func=state_command)
