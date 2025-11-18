"""
Show project state command.

Displays the current project state in a readable format.
"""

import argparse
import json
import os
from typing import Dict, Any


def pretty_print_state(state: Dict[str, Any]) -> None:
    """
    Pretty print project state.

    Args:
        state: Project state dictionary
    """
    print("\n" + "=" * 60)
    print("PROJECT STATE")
    print("=" * 60)
    print()

    # General info
    print("General:")
    print(f"  Initialized: {state.get('initialized', False)}")
    print(f"  Version: {state.get('version', 'N/A')}")
    print()

    # Architecture
    architecture = state.get("architecture", {})
    print("Architecture:")
    if architecture:
        if architecture.get("analyzed"):
            print("  Status: Analyzed")
            components = architecture.get("components", [])
            if components:
                print(f"  Components ({len(components)}):")
                for component in components:
                    print(f"    - {component}")
            recommendations = architecture.get("recommendations", [])
            if recommendations:
                print(f"  Recommendations ({len(recommendations)}):")
                for rec in recommendations:
                    print(f"    - {rec}")
        else:
            print("  Status: Not analyzed")
    else:
        print("  Status: Not analyzed")
    print()

    # Specialists
    specialists = state.get("specialists_run", [])
    print("Specialists:")
    if specialists:
        print(f"  Run ({len(specialists)}):")
        for specialist in specialists:
            print(f"    - {specialist}")
    else:
        print("  None run yet")
    print()

    # Quality reports
    quality_reports = state.get("quality_reports", [])
    print("Quality Reports:")
    if quality_reports:
        print(f"  Total reports: {len(quality_reports)}")
        latest = quality_reports[-1]
        print("  Latest report:")
        print(f"    Timestamp: {latest.get('timestamp', 'N/A')}")
        print(f"    Score: {latest.get('score', 0):.1f}/100")
        print(f"    Status: {'PASSED' if latest.get('passed') else 'FAILED'}")
    else:
        print("  No reports generated yet")
    print()

    # Configuration
    config = state.get("config", {})
    if config:
        print("Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print()

    print("=" * 60)


def show_state_command(args: argparse.Namespace) -> int:
    """
    Show current project state.

    Reads and displays the project state and settings in a human-readable format or JSON.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    state_file = ".codecompanion_state.json"
    settings_file = ".codecompanion_settings.json"

    # Check if files exist
    state_exists = os.path.exists(state_file)
    settings_exists = os.path.exists(settings_file)

    if not state_exists and not settings_exists:
        print("No CodeCompanion project found in current directory.")
        print("Run 'python -m codecompanion.cli init' to initialize a project.")
        return 0

    try:
        # Load state if exists
        state = None
        if state_exists:
            with open(state_file, "r") as f:
                state = json.load(f)

        # Load settings if exists
        settings = None
        if settings_exists:
            with open(settings_file, "r") as f:
                settings = json.load(f)

        # Print combined output
        if args.raw:
            # Raw JSON output with both state and settings
            combined = {
                "state": state,
                "settings": settings
            }
            print(json.dumps(combined, indent=2))
        else:
            # Pretty formatted output
            if state:
                pretty_print_state(state)
            else:
                print("\n[state] No state file found")

            if settings:
                print("\nSETTINGS:")
                print("=" * 60)
                print(json.dumps(settings, indent=2))
                print("=" * 60)
            else:
                print("\n[state] No settings file found")

        return 0

    except json.JSONDecodeError as e:
        print(f"[state] Error: Failed to parse project files: {e}")
        return 1
    except Exception as e:
        print(f"[state] Error: {e}")
        return 1


def setup_show_state_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up argument parser for state command.

    Args:
        subparsers: Subparser action from main argument parser
    """
    parser = subparsers.add_parser(
        "state",
        help="Show current project state",
        description="Display the current project state in a readable format.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw JSON output",
    )
    parser.set_defaults(func=show_state_command)
