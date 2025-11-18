"""
Orchestrator for CodeCompanion workflows with settings integration.

Manages project settings and provides configuration access for CLI commands.
"""

from pathlib import Path
from typing import Optional

from .settings import Settings, load_settings


class Orchestrator:
    """
    CodeCompanion orchestrator for managing workflows and settings.

    Loads and maintains project settings, providing access to configuration
    for CLI commands and other components.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the orchestrator.

        Args:
            config_path: Optional path to settings file. If None,
                        uses default .codecompanion_settings.json
        """
        self.config_path = config_path
        self.settings = self._load_settings()

    def _load_settings(self) -> Settings:
        """
        Load settings from configuration.

        Returns:
            Settings instance

        Raises:
            FileNotFoundError: If DEFAULT_SETTINGS.json is missing
            json.JSONDecodeError: If any JSON file is malformed
            ValueError: If required settings are missing or invalid
        """
        return load_settings(config_path=self.config_path)

    def get_settings(self) -> Settings:
        """
        Get current settings.

        Returns:
            Settings instance with current configuration
        """
        return self.settings

    def reload_settings(self) -> Settings:
        """
        Reload settings from disk.

        Useful if settings file has been modified externally.

        Returns:
            Reloaded Settings instance
        """
        self.settings = self._load_settings()
        return self.settings
