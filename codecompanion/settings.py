"""
Settings Management for CodeCompanion

Handles project-level configuration including model policy mode.
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class Settings:
    """CodeCompanion project settings."""

    # Model policy configuration
    model_policy_mode: str = "balanced"
    model_policy_path: str = "ops/MODEL_POLICY.json"

    # Project metadata
    project_name: str = ""
    project_root: str = "."

    # LLM provider fallback (for backwards compatibility)
    default_provider: str = "claude"


DEFAULT_SETTINGS_FILE = ".codecompanion_settings.json"


def load_settings(
    settings_path: Path | str | None = None,
    project_root: Path | str = "."
) -> Settings:
    """
    Load settings from a JSON file.

    Args:
        settings_path: Path to settings file. If None, uses DEFAULT_SETTINGS_FILE
        project_root: Project root directory

    Returns:
        Settings object with loaded or default values
    """
    project_root = Path(project_root)

    if settings_path is None:
        settings_path = project_root / DEFAULT_SETTINGS_FILE
    else:
        settings_path = Path(settings_path)

    if not settings_path.exists():
        # Return default settings
        return Settings(project_root=str(project_root))

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Create Settings from loaded data
        return Settings(
            model_policy_mode=data.get("model_policy_mode", "balanced"),
            model_policy_path=data.get("model_policy_path", "ops/MODEL_POLICY.json"),
            project_name=data.get("project_name", ""),
            project_root=data.get("project_root", str(project_root)),
            default_provider=data.get("default_provider", "claude")
        )
    except json.JSONDecodeError as e:
        print(f"[settings] WARNING: Invalid JSON in {settings_path}: {e}")
        return Settings(project_root=str(project_root))
    except Exception as e:
        print(f"[settings] WARNING: Error loading settings from {settings_path}: {e}")
        return Settings(project_root=str(project_root))


def save_settings(settings: Settings, settings_path: Path | str | None = None) -> None:
    """
    Save settings to a JSON file.

    Args:
        settings: Settings object to save
        settings_path: Path to save to. If None, uses project_root/DEFAULT_SETTINGS_FILE
    """
    if settings_path is None:
        settings_path = Path(settings.project_root) / DEFAULT_SETTINGS_FILE
    else:
        settings_path = Path(settings_path)

    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2)
        print(f"[settings] Saved to {settings_path}")
    except Exception as e:
        print(f"[settings] ERROR: Failed to save settings to {settings_path}: {e}")


def init_settings(project_root: Path | str = ".", force: bool = False) -> Settings:
    """
    Initialize settings for a project.

    Args:
        project_root: Project root directory
        force: If True, overwrite existing settings file

    Returns:
        The initialized Settings object
    """
    project_root = Path(project_root)
    settings_path = project_root / DEFAULT_SETTINGS_FILE

    if settings_path.exists() and not force:
        print(f"[settings] Settings file already exists at {settings_path}")
        return load_settings(settings_path, project_root)

    # Detect project name from directory
    project_name = project_root.resolve().name

    settings = Settings(
        model_policy_mode="balanced",
        model_policy_path="ops/MODEL_POLICY.json",
        project_name=project_name,
        project_root=str(project_root),
        default_provider="claude"
    )

    save_settings(settings, settings_path)
    return settings


def get_state_info(settings: Settings) -> dict[str, Any]:
    """
    Get current state information for display.

    Args:
        settings: The settings object

    Returns:
        Dictionary with state information
    """
    return {
        "project_name": settings.project_name or "(unnamed)",
        "project_root": settings.project_root,
        "model_policy_mode": settings.model_policy_mode,
        "model_policy_path": settings.model_policy_path,
        "default_provider": settings.default_provider
    }
