"""
Settings and configuration management for CodeCompanion.

Provides a typed configuration system that loads defaults, overlays project-level
settings, and respects environment variable overrides.
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """
    CodeCompanion project settings.

    Attributes:
        project_name: Optional project name (defaults to directory name)
        model_policy_mode: Model selection mode (e.g., "balanced", "cheapest", "fastest")
        project_root: Root directory for the project
        notes: List of notes/comments about the project
    """
    project_name: Optional[str]
    model_policy_mode: str
    project_root: str
    notes: list[str]


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """
    Load settings from defaults, project config, and environment overrides.

    Loading order (later sources override earlier ones):
    1. DEFAULT_SETTINGS.json from ops/
    2. .codecompanion_settings.json from current directory (if exists)
    3. Environment variables (CC_PROJECT_NAME, CC_MODEL_POLICY_MODE)

    Args:
        config_path: Optional explicit path to settings file. If None,
                    looks for .codecompanion_settings.json in current dir.

    Returns:
        Settings instance with fully-populated values

    Raises:
        FileNotFoundError: If DEFAULT_SETTINGS.json is missing
        json.JSONDecodeError: If any JSON file is malformed
        ValueError: If required settings are missing or invalid
    """
    # Determine project root
    project_root = Path.cwd()

    # Load default settings
    default_settings_path = Path(__file__).parent.parent / "ops" / "DEFAULT_SETTINGS.json"
    if not default_settings_path.exists():
        raise FileNotFoundError(
            f"Default settings not found: {default_settings_path}. "
            "This is a critical configuration file."
        )

    try:
        with open(default_settings_path, "r") as f:
            settings_dict = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in DEFAULT_SETTINGS.json: {e.msg}",
            e.doc,
            e.pos
        )

    # Determine project config path
    if config_path is None:
        config_path = project_root / ".codecompanion_settings.json"

    # Overlay project-level settings if they exist
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                project_settings = json.load(f)
            settings_dict.update(project_settings)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {config_path}: {e.msg}",
                e.doc,
                e.pos
            )

    # Environment variable overrides
    if "CC_PROJECT_NAME" in os.environ:
        settings_dict["project_name"] = os.environ["CC_PROJECT_NAME"]

    if "CC_MODEL_POLICY_MODE" in os.environ:
        settings_dict["model_policy_mode"] = os.environ["CC_MODEL_POLICY_MODE"]

    # Validate required fields
    if "model_policy_mode" not in settings_dict:
        raise ValueError("model_policy_mode is required but not set")

    if "project_root" not in settings_dict:
        settings_dict["project_root"] = "."

    if "notes" not in settings_dict:
        settings_dict["notes"] = []

    # Create Settings instance
    try:
        return Settings(
            project_name=settings_dict.get("project_name"),
            model_policy_mode=settings_dict["model_policy_mode"],
            project_root=settings_dict["project_root"],
            notes=settings_dict["notes"]
        )
    except KeyError as e:
        raise ValueError(f"Missing required setting: {e}")


def save_settings(settings: Settings, config_path: Optional[Path] = None) -> None:
    """
    Save settings to a JSON configuration file.

    Args:
        settings: Settings instance to save
        config_path: Optional path to save to. If None, saves to
                    .codecompanion_settings.json in current directory

    Raises:
        OSError: If unable to create directories or write file
    """
    # Determine save path
    if config_path is None:
        config_path = Path.cwd() / ".codecompanion_settings.json"

    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert settings to dict
    settings_dict = asdict(settings)

    # Write to file with pretty printing
    try:
        with open(config_path, "w") as f:
            json.dump(settings_dict, f, indent=2)
    except OSError as e:
        raise OSError(f"Failed to write settings to {config_path}: {e}")
