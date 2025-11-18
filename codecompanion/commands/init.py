"""
CLI command for initializing the project.
"""
from ..bootstrap import ensure_bootstrap


def init_command(args):
    """
    Initialize the project with required directories and files.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    info = ensure_bootstrap()
    print("[init] Bootstrap complete")
    print(f"[init] Directory: {info['dir']}")
    if info['created']:
        print(f"[init] Created: {', '.join(info['created'])}")
    print(f"[init] Agents directory: {info['agents_dir']}")
    return 0
