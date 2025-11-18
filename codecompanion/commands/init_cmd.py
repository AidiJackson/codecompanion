"""
Init Command - Initialize CodeCompanion Settings

This command initializes settings for a project.
"""

from ..settings import init_settings


def init_command(args=None) -> int:
    """
    Initialize CodeCompanion settings for the current project.

    Args:
        args: Command line arguments (from argparse)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        settings = init_settings()
        print("[init] CodeCompanion initialized successfully")
        print(f"[init] Project: {settings.project_name}")
        print(f"[init] Model policy mode: {settings.model_policy_mode}")
        print(f"[init] Settings saved to: .codecompanion_settings.json")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return 1


def add_init_subcommand(subparsers):
    """
    Add the 'init' subcommand to the CLI.

    Args:
        subparsers: The subparsers object from argparse
    """
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize CodeCompanion settings"
    )
    init_parser.set_defaults(func=init_command)
