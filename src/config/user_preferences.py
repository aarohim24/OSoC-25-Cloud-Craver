"""
User preferences management module.

This module provides functionality for managing user-specific preferences,
including default cloud providers, regions, and application settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

from . import config


@dataclass
class UserPreferences:
    """User preferences data class."""
    default_provider: str = "aws"
    default_region: str = "us-east-1"
    auto_save: bool = True
    confirm_destructive_actions: bool = True
    theme: str = "auto"
    editor: str = "vim"
    recent_providers: List[str] = None
    recent_regions: List[str] = None
    recent_templates: List[str] = None
    last_updated: str = None
    
    def __post_init__(self):
        """Initialize default values for list fields."""
        if self.recent_providers is None:
            self.recent_providers = []
        if self.recent_regions is None:
            self.recent_regions = []
        if self.recent_templates is None:
            self.recent_templates = []
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()


class UserPreferencesManager:
    """Manages user preferences with persistence and validation."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the user preferences manager.
        
        Args:
            config_dir: Optional custom config directory
        """
        if config_dir is None:
            config_dir = Path(__file__).parent
        
        self.config_dir = config_dir
        self.preferences_file = config_dir / "user_preferences.json"
        self.backup_file = config_dir / "user_preferences.backup.json"
        self._preferences = None
    
    def get_preferences_file_path(self) -> Path:
        """Get the path to the user preferences file."""
        return self.preferences_file
    
    def load_preferences(self) -> UserPreferences:
        """
        Load user preferences from file or create defaults.
        
        Returns:
            UserPreferences object
        """
        if self._preferences is not None:
            return self._preferences
        
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                self._preferences = UserPreferences(**data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"Warning: Could not load user preferences: {e}")
                print("Using default preferences")
                self._preferences = self._create_default_preferences()
        else:
            self._preferences = self._create_default_preferences()
        
        return self._preferences
    
    def save_preferences(self, preferences: Optional[UserPreferences] = None) -> bool:
        """
        Save user preferences to file.
        
        Args:
            preferences: Optional preferences object to save. If None, saves current preferences.
            
        Returns:
            True if saved successfully, False otherwise
        """
        if preferences is None:
            preferences = self.load_preferences()
        
        # Update last_updated timestamp
        preferences.last_updated = datetime.now().isoformat()
        
        try:
            # Create backup if file exists
            if self.preferences_file.exists():
                self.preferences_file.rename(self.backup_file)
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save preferences
            with open(self.preferences_file, 'w') as f:
                json.dump(asdict(preferences), f, indent=2)
            
            self._preferences = preferences
            
            # Remove backup on successful save
            if self.backup_file.exists():
                self.backup_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error saving user preferences: {e}")
            
            # Restore backup if save failed
            if self.backup_file.exists() and not self.preferences_file.exists():
                self.backup_file.rename(self.preferences_file)
            
            return False
    
    def update_preference(self, key: str, value: Any) -> bool:
        """
        Update a specific preference.
        
        Args:
            key: Preference key to update
            value: New value for the preference
            
        Returns:
            True if updated successfully, False otherwise
        """
        preferences = self.load_preferences()
        
        if hasattr(preferences, key):
            setattr(preferences, key, value)
            return self.save_preferences(preferences)
        else:
            print(f"Warning: Unknown preference key: {key}")
            return False
    
    def add_recent_item(self, item_type: str, item: str, max_items: int = 10) -> bool:
        """
        Add an item to the recent items list.
        
        Args:
            item_type: Type of item ('providers', 'regions', 'templates')
            item: Item to add
            max_items: Maximum number of recent items to keep
            
        Returns:
            True if added successfully, False otherwise
        """
        preferences = self.load_preferences()
        
        attr_name = f"recent_{item_type}"
        if not hasattr(preferences, attr_name):
            print(f"Warning: Unknown recent item type: {item_type}")
            return False
        
        recent_list = getattr(preferences, attr_name)
        
        # Remove item if it already exists
        if item in recent_list:
            recent_list.remove(item)
        
        # Add item to the beginning
        recent_list.insert(0, item)
        
        # Limit the list size
        if len(recent_list) > max_items:
            recent_list = recent_list[:max_items]
            setattr(preferences, attr_name, recent_list)
        
        return self.save_preferences(preferences)
    
    def get_recent_items(self, item_type: str) -> List[str]:
        """
        Get recent items of specified type.
        
        Args:
            item_type: Type of item ('providers', 'regions', 'templates')
            
        Returns:
            List of recent items
        """
        preferences = self.load_preferences()
        attr_name = f"recent_{item_type}"
        
        if hasattr(preferences, attr_name):
            return getattr(preferences, attr_name)
        else:
            print(f"Warning: Unknown recent item type: {item_type}")
            return []
    
    def reset_preferences(self) -> bool:
        """
        Reset preferences to defaults.
        
        Returns:
            True if reset successfully, False otherwise
        """
        self._preferences = self._create_default_preferences()
        return self.save_preferences()
    
    def export_preferences(self, file_path: Path) -> bool:
        """
        Export preferences to a specified file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if exported successfully, False otherwise
        """
        preferences = self.load_preferences()
        
        try:
            with open(file_path, 'w') as f:
                json.dump(asdict(preferences), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting preferences: {e}")
            return False
    
    def import_preferences(self, file_path: Path) -> bool:
        """
        Import preferences from a specified file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            preferences = UserPreferences(**data)
            return self.save_preferences(preferences)
            
        except Exception as e:
            print(f"Error importing preferences: {e}")
            return False
    
    def _create_default_preferences(self) -> UserPreferences:
        """Create default user preferences."""
        # Try to get defaults from main config if available
        try:
            user_config = config.get_user_preferences()
            return UserPreferences(
                default_provider=getattr(user_config, 'default_provider', 'aws'),
                default_region=getattr(user_config, 'default_region', 'us-east-1'),
                auto_save=getattr(user_config, 'auto_save', True),
                confirm_destructive_actions=getattr(user_config, 'confirm_destructive_actions', True),
                theme=getattr(user_config, 'theme', 'auto'),
                editor=getattr(user_config, 'editor', 'vim')
            )
        except:
            # Fallback to hardcoded defaults
            return UserPreferences()
    
    def validate_preferences(self, preferences: UserPreferences) -> List[str]:
        """
        Validate user preferences.
        
        Args:
            preferences: Preferences to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate default provider
        valid_providers = ["aws", "azure", "gcp"]
        if preferences.default_provider not in valid_providers:
            errors.append(f"Invalid default provider: {preferences.default_provider}. Must be one of: {valid_providers}")
        
        # Validate theme
        valid_themes = ["auto", "light", "dark"]
        if preferences.theme not in valid_themes:
            errors.append(f"Invalid theme: {preferences.theme}. Must be one of: {valid_themes}")
        
        # Validate recent items lists
        for attr_name in ['recent_providers', 'recent_regions', 'recent_templates']:
            attr_value = getattr(preferences, attr_name)
            if not isinstance(attr_value, list):
                errors.append(f"{attr_name} must be a list")
        
        return errors


# Global preferences manager instance
_preferences_manager = None


def get_preferences_manager() -> UserPreferencesManager:
    """Get the global preferences manager instance."""
    global _preferences_manager
    if _preferences_manager is None:
        _preferences_manager = UserPreferencesManager()
    return _preferences_manager


def get_user_preferences() -> UserPreferences:
    """Get current user preferences."""
    return get_preferences_manager().load_preferences()


def save_user_preferences(preferences: UserPreferences) -> bool:
    """Save user preferences."""
    return get_preferences_manager().save_preferences(preferences)


def update_user_preference(key: str, value: Any) -> bool:
    """Update a specific user preference."""
    return get_preferences_manager().update_preference(key, value)


def add_recent_item(item_type: str, item: str) -> bool:
    """Add an item to recent items."""
    return get_preferences_manager().add_recent_item(item_type, item)


def get_recent_items(item_type: str) -> List[str]:
    """Get recent items of specified type."""
    return get_preferences_manager().get_recent_items(item_type)


# Export all public functions
__all__ = [
    'UserPreferences',
    'UserPreferencesManager',
    'get_preferences_manager',
    'get_user_preferences',
    'save_user_preferences',
    'update_user_preference',
    'add_recent_item',
    'get_recent_items'
] 