"""
Show Policy Command - Display Model Policy Configuration

This command shows the current model policy configuration,
displaying which models are used for each role.
"""

import json
import argparse
from pathlib import Path
from ..model_policy import load_model_policy, get_default_mode, PolicyError
from ..settings import load_settings


def show_policy_command(args=None) -> int:
    """
    Display the current model policy configuration.

    Args:
        args: Command line arguments (from argparse)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if args is None:
        # Create a simple args object for standalone use
        class Args:
            raw = False
        args = Args()

    try:
        # Load settings to get current mode
        settings = load_settings()

        # Load policy
        policy_path = Path(settings.model_policy_path)
        policy = load_model_policy(policy_path)

        # If --raw flag, just dump JSON
        if args.raw:
            print(json.dumps(policy, indent=2))
            return 0

        # Get active mode
        active_mode = settings.model_policy_mode
        default_mode = get_default_mode(policy)

        # Display header
        print(f"\nModel Policy (mode: {active_mode})")
        if active_mode != default_mode:
            print(f"  (default mode is: {default_mode})")
        print()

        # Check if mode exists
        if active_mode not in policy.get("modes", {}):
            print(f"ERROR: Active mode '{active_mode}' not found in policy!")
            print(f"Available modes: {list(policy.get('modes', {}).keys())}")
            return 1

        mode_config = policy["modes"][active_mode]
        if "description" in mode_config:
            print(f"Description: {mode_config['description']}")
            print()

        # Display roles
        roles = mode_config.get("roles", {})
        if not roles:
            print("No roles defined in this mode.")
            return 0

        # Find max role name length for alignment
        max_role_len = max(len(role) for role in roles.keys())

        print("Roles:")
        for role_name in sorted(roles.keys()):
            candidates = roles[role_name]
            if not candidates or len(candidates) == 0:
                print(f"  {role_name:<{max_role_len}} : NO CANDIDATES DEFINED")
                continue

            # Take first candidate
            candidate = candidates[0]
            provider = candidate.get("provider", "?")
            model = candidate.get("model", "?")
            temp = candidate.get("temperature", "?")
            max_tokens = candidate.get("max_tokens", "?")

            print(f"  {role_name:<{max_role_len}} : {provider:12} / {model:30} "
                  f"(temp={temp}, max_tokens={max_tokens})")

        print()
        return 0

    except PolicyError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def add_policy_subcommand(subparsers):
    """
    Add the 'policy' subcommand to the CLI.

    Args:
        subparsers: The subparsers object from argparse
    """
    policy_parser = subparsers.add_parser(
        "policy",
        help="Show model policy configuration"
    )
    policy_parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw JSON policy data"
    )
    policy_parser.set_defaults(func=show_policy_command)
