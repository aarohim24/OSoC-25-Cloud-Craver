"""
Configuration module for Cloud Craver application.

This module initializes Dynaconf with support for multiple configuration sources:
- Configuration files (settings.toml, config.yaml)
- Environment variables
- CLI arguments
- User preferences
"""

from dynaconf import Dynaconf, Validator
from pathlib import Path
import os

# Get the config directory path
CONFIG_DIR = Path(__file__).parent
ROOT_DIR = CONFIG_DIR.parent.parent

# Initialize Dynaconf
settings = Dynaconf(
    # Configuration files to load (in order of precedence)
    settings_files=[
        str(CONFIG_DIR / "settings.toml"),
        str(CONFIG_DIR / "config.yaml"),
        str(CONFIG_DIR / "local_settings.toml"),  # Local overrides (gitignored)
    ],
    
    # Environment variables prefix
    envvar_prefix="CLOUDCRAVER",
    
    # Support for environments (development, production, etc.) - start with False for simplicity
    environments=False,
    
    # Load from environment variables
    load_dotenv=True,
    
    # Merge configs from multiple sources
    merge_enabled=True,
    
    # Validate configuration on load - start with False for initial setup
    validate=False,
    
    # Case-insensitive configuration keys
    lowercase_read=True,
    
    # Additional directories to search for config files
    root_path=ROOT_DIR,
    
    # Support for .secrets files
    secrets=".secrets.toml",
    
    # Include base configuration
    includes=["base_config.toml"],
    
    # Basic validators - start simple and add more as needed
    validators=[
        # Essential application settings
        Validator("app.name", must_exist=True, is_type_of=str),
        Validator("app.version", must_exist=True, is_type_of=str),
        
        # Cloud provider validation
        Validator("cloud.default_provider", must_exist=True, condition=lambda x: x in ["aws", "azure", "gcp"]),
    ]
)

# Export the main configuration instance
config = settings

# Convenience functions for accessing nested configurations
def get_cloud_config():
    """Get cloud provider configuration."""
    return config.cloud

def get_user_preferences():
    """Get user preferences configuration."""
    return config.user.preferences

def get_app_config():
    """Get application configuration."""
    return config.app

def get_validation_config():
    """Get validation configuration."""
    return config.validation

def get_terraform_config():
    """Get Terraform-specific configuration."""
    return config.terraform

# Configuration file discovery and precedence
def get_config_sources():
    """Return the configuration sources in order of precedence (highest to lowest)."""
    return [
        "CLI arguments",
        "Environment variables",
        "local_settings.toml",
        "settings.toml", 
        "config.yaml",
        "base_config.toml"
    ]

def reload_config():
    """Reload configuration from all sources."""
    settings.reload()

# Export all public functions and the main config
__all__ = [
    'config',
    'settings', 
    'get_cloud_config',
    'get_user_preferences', 
    'get_app_config',
    'get_validation_config',
    'get_terraform_config',
    'get_config_sources',
    'reload_config'
] 