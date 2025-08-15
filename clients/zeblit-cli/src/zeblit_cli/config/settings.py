"""
Configuration settings for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial settings implementation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from pydantic_settings import BaseSettings
from pydantic import Field

logger = logging.getLogger(__name__)


@dataclass
class UserPreferences:
    """User preferences for CLI behavior."""
    
    default_editor: str = "vim"
    color_output: bool = True
    auto_sync_files: bool = True
    verbose_output: bool = False
    confirmation_prompts: bool = True
    max_log_lines: int = 1000


class ZeblitSettings(BaseSettings):
    """Settings for Zeblit CLI."""
    
    # API Configuration
    api_base_url: str = Field(
        default="http://localhost:8000/api/v1",
        description="Base URL for Zeblit API"
    )
    api_timeout: float = Field(
        default=30.0,
        description="API request timeout in seconds"
    )
    websocket_timeout: float = Field(
        default=60.0,
        description="WebSocket connection timeout in seconds"
    )
    
    # Authentication
    api_key: Optional[str] = Field(
        default=None,
        description="User API key for authentication"
    )
    
    # Current session
    current_project_id: Optional[str] = Field(
        default=None,
        description="Currently selected project ID"
    )
    
    # User preferences
    preferences: UserPreferences = Field(
        default_factory=UserPreferences,
        description="User preferences"
    )
    
    # Debug settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    class Config:
        """Pydantic config."""
        env_prefix = "ZEBLIT_"
        case_sensitive = False


class ConfigManager:
    """Manages CLI configuration persistence."""
    
    def __init__(self):
        """Initialize config manager."""
        self.config_dir = Path.home() / ".zeblit"
        self.config_file = self.config_dir / "config.json"
        self._settings: Optional[ZeblitSettings] = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
    
    def load_settings(self) -> ZeblitSettings:
        """Load settings from config file and environment."""
        # Load from file if exists
        file_config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                logger.debug(f"Loaded config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        # Handle preferences separately (they're nested)
        preferences_data = file_config.pop("preferences", {})
        preferences = UserPreferences(**preferences_data)
        
        # Create settings with file config and environment overrides
        settings = ZeblitSettings(
            preferences=preferences,
            **file_config
        )
        
        self._settings = settings
        return settings
    
    def save_settings(self, settings: ZeblitSettings) -> None:
        """Save settings to config file."""
        try:
            # Convert to dict, handling special objects
            config_dict = {}
            for key, value in settings.dict().items():
                if key == "preferences" and hasattr(value, '__dict__'):
                    # Convert preferences object to dict
                    config_dict[key] = value.__dict__
                else:
                    config_dict[key] = value
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.debug(f"Saved config to {self.config_file}")
            self._settings = settings
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def get_settings(self) -> ZeblitSettings:
        """Get current settings."""
        if self._settings is None:
            self._settings = self.load_settings()
        return self._settings
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a single setting and save."""
        settings = self.get_settings()
        
        # Handle nested preferences
        if key.startswith("preferences."):
            pref_key = key.split(".", 1)[1]
            preferences = settings.preferences.__dict__.copy()
            preferences[pref_key] = value
            settings.preferences = UserPreferences(**preferences)
        else:
            setattr(settings, key, value)
        
        self.save_settings(settings)
    
    def clear_auth(self) -> None:
        """Clear authentication data."""
        settings = self.get_settings()
        settings.api_key = None
        settings.current_project_id = None
        self.save_settings(settings)
    
    def set_current_project(self, project_id: str) -> None:
        """Set the current project."""
        self.update_setting("current_project_id", project_id)
    
    def set_api_key(self, api_key: str) -> None:
        """Set the API key."""
        self.update_setting("api_key", api_key)
    
    def get_config_file_path(self) -> str:
        """Get the config file path."""
        return str(self.config_file)
    
    def config_exists(self) -> bool:
        """Check if config file exists."""
        return self.config_file.exists()
    
    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        if self.config_file.exists():
            self.config_file.unlink()
        self._settings = None


# Global config manager instance
_config_manager = ConfigManager()


def get_settings() -> ZeblitSettings:
    """Get current settings."""
    return _config_manager.get_settings()


def get_config_manager() -> ConfigManager:
    """Get the config manager instance."""
    return _config_manager


def update_setting(key: str, value: Any) -> None:
    """Update a setting."""
    _config_manager.update_setting(key, value)


def set_current_project(project_id: str) -> None:
    """Set the current project."""
    _config_manager.set_current_project(project_id)


def set_api_key(api_key: str) -> None:
    """Set the API key."""
    _config_manager.set_api_key(api_key)


def clear_auth() -> None:
    """Clear authentication data."""
    _config_manager.clear_auth()
