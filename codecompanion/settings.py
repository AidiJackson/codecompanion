"""Settings management for CodeCompanion."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class FailPathSettings:
    """Settings for fail-path and recovery behavior."""

    max_attempts: int = 2
    backoff_seconds: float = 0.0
    fallback_enabled: bool = False
    strict_validation: bool = False
    llm_repair_enabled: bool = False
    llm_repair_max_attempts: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Settings:
    """CodeCompanion settings."""

    model_policy_mode: str = "balanced"
    fail_path: FailPathSettings = None
    provider: str = "claude"
    log_level: str = "INFO"

    def __post_init__(self):
        """Initialize nested dataclasses if needed."""
        if self.fail_path is None:
            self.fail_path = FailPathSettings()
        elif isinstance(self.fail_path, dict):
            self.fail_path = FailPathSettings(**self.fail_path)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_policy_mode": self.model_policy_mode,
            "fail_path": self.fail_path.to_dict(),
            "provider": self.provider,
            "log_level": self.log_level,
        }


def load_settings(settings_file: str = ".codecompanion_settings.json") -> Settings:
    """Load settings from file, or return defaults if file doesn't exist."""
    settings_path = Path(settings_file)

    if settings_path.exists():
        try:
            with open(settings_path, "r") as f:
                data = json.load(f)

            # Handle fail_path as dict or FailPathSettings
            fail_path_data = data.get("fail_path", {})
            if isinstance(fail_path_data, dict):
                fail_path = FailPathSettings(**fail_path_data)
            else:
                fail_path = FailPathSettings()

            return Settings(
                model_policy_mode=data.get("model_policy_mode", "balanced"),
                fail_path=fail_path,
                provider=data.get("provider", "claude"),
                log_level=data.get("log_level", "INFO"),
            )
        except (json.JSONDecodeError, OSError, TypeError, KeyError):
            pass

    # Return defaults
    return Settings()


def save_settings(settings: Settings, settings_file: str = ".codecompanion_settings.json") -> None:
    """Save settings to file."""
    settings_path = Path(settings_file)

    with open(settings_path, "w") as f:
        json.dump(settings.to_dict(), f, indent=2)


def init_settings(settings_file: str = ".codecompanion_settings.json") -> Settings:
    """Initialize settings file with defaults if it doesn't exist."""
    settings_path = Path(settings_file)

    if not settings_path.exists():
        settings = Settings()
        save_settings(settings, settings_file)
        return settings

    return load_settings(settings_file)
