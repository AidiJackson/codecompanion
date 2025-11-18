"""
Show project state command for CodeCompanion.

Displays current project settings and state information.
"""

import json
from pathlib import Path
from typing import Optional

from ..orchestrator import Orchestrator


def show_state(json_output: bool = False, orchestrator: Optional[Orchestrator] = None) -> int:
    """
    Show current CodeCompanion project state.

    Displays:
    - Project name
    - Model policy mode
    - Project root
    - Notes (if any)

    Args:
        json_output: If True, output as JSON instead of human-readable format
        orchestrator: Optional Orchestrator instance. If None, creates a new one.

    Returns:
        0 on success, 1 on error
    """
    try:
        # Create or use provided orchestrator
        if orchestrator is None:
            orchestrator = Orchestrator()

        # Get settings
        settings = orchestrator.get_settings()

        if json_output:
            # Output as JSON
            state = {
                "project_name": settings.project_name,
                "model_policy_mode": settings.model_policy_mode,
                "project_root": settings.project_root,
                "notes": settings.notes
            }
            print(json.dumps(state, indent=2))
        else:
            # Human-readable format
            print("[codecompanion] Project State")
            print("=" * 50)
            print(f"Project Name:       {settings.project_name or '(not set)'}")
            print(f"Model Policy Mode:  {settings.model_policy_mode}")
            print(f"Project Root:       {settings.project_root}")

            if settings.notes:
                print(f"\nNotes ({len(settings.notes)}):")
                for i, note in enumerate(settings.notes, 1):
                    print(f"  {i}. {note}")
            else:
                print("\nNotes:              (none)")

            # Show config file location
            config_path = Path.cwd() / ".codecompanion_settings.json"
            if config_path.exists():
                print(f"\nConfig file:        {config_path}")
            else:
                print(f"\nConfig file:        (using defaults)")

        return 0

    except FileNotFoundError as e:
        print(f"[codecompanion] Configuration error: {e}")
        print("[codecompanion] Hint: Run 'codecompanion --init' to create settings")
        return 1
    except Exception as e:
        print(f"[codecompanion] Error showing state: {e}")
        return 1
