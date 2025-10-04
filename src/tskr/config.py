"""Configuration management for Tskr CLI."""

import json
from pathlib import Path
from typing import Any, Optional

from .models import AppConfig


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager."""
        if config_dir is None:
            self.config_dir = Path.home() / ".config" / "tskr"
        else:
            self.config_dir = config_dir

        self.config_file = self.config_dir / "config.json"
        self._config: Optional[AppConfig] = None

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config

        self._ensure_config_dir()

        if not self.config_file.exists():
            self._config = AppConfig()
            self.save_config(self._config)
            return self._config

        try:
            with open(self.config_file, encoding="utf-8") as f:
                config_data = json.load(f)

            self._config = AppConfig(**config_data)
            return self._config

        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Failed to load config file: {e}")
            print("Using default configuration.")
            self._config = AppConfig()
            return self._config

    def save_config(self, config: AppConfig) -> None:
        """Save configuration to file."""
        self._ensure_config_dir()

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config.model_dump(), f, indent=2, default=str)

            self._config = config

        except Exception as e:
            print(f"Warning: Failed to save config file: {e}")

    def get_config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

    def update_config(self, **updates: Any) -> None:
        """Update configuration with new values."""
        config = self.get_config()

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.save_config(config)

    def set_current_project(self, project: Optional[str]) -> None:
        """Set current project context."""
        self.update_config(current_project=project)

    def get_current_project(self) -> Optional[str]:
        """Get current project context."""
        config = self.get_config()
        return config.current_project

    def get_auto_tags(self, keyword: str) -> list[str]:
        """Get auto-tags for keyword."""
        config = self.get_config()
        return config.auto_tags.get(keyword, [])

    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        self._config = AppConfig()
        self.save_config(self._config)


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get current configuration."""
    return get_config_manager().get_config()


def set_current_project(project: Optional[str]) -> None:
    """Set current project context."""
    get_config_manager().set_current_project(project)


def get_current_project() -> Optional[str]:
    """Get current project context."""
    return get_config_manager().get_current_project()


def get_auto_tags(keyword: str) -> list[str]:
    """Get auto-tags for keyword."""
    return get_config_manager().get_auto_tags(keyword)
