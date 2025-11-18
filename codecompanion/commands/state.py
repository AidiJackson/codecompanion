"""
CLI command for displaying the current state.
"""
import json
from pathlib import Path


def state_command(args):
    """
    Display the current state from .cc/state.json.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    state_file = Path(".cc/state.json")

    if state_file.exists():
        with open(state_file, "r") as f:
            state = json.load(f)
        print("[state] Current state:")
        print(json.dumps(state, indent=2))
    else:
        print("[state] No state file found")

    return 0
