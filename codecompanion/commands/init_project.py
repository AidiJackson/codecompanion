"""
Project initialization command for CodeCompanion.

Creates a default .codecompanion_settings.json file in the current directory.
"""

from pathlib import Path

from ..settings import Settings, save_settings


def init_project() -> int:
    """
    Initialize CodeCompanion project settings.

    Creates .codecompanion_settings.json with default values:
    - project_name: current directory name
    - model_policy_mode: "balanced"
    - project_root: "."
    - notes: []

    Returns:
        0 on success, 1 on error
    """
    try:
        # Get current directory name as default project name
        current_dir = Path.cwd()
        project_name = current_dir.name

        # Create default settings
        settings = Settings(
            project_name=project_name,
            model_policy_mode="balanced",
            project_root=".",
            notes=[]
        )

        # Save to .codecompanion_settings.json
        config_path = current_dir / ".codecompanion_settings.json"
        save_settings(settings, config_path)

        # Print confirmation
        print(f"[codecompanion] Initialized project: {project_name}")
        print(f"[codecompanion] Settings saved to: {config_path}")
        print(f"[codecompanion] Model policy mode: {settings.model_policy_mode}")

        return 0

    except Exception as e:
        print(f"[codecompanion] Error initializing project: {e}")
        return 1
