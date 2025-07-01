"""
Configuration utilities and helper functions.

This module provides utility functions for configuration management,
including file discovery, validation helpers, and configuration merging.
"""

import os
import json
import yaml
import toml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from . import config


def discover_config_files(search_paths: Optional[List[Union[str, Path]]] = None) -> Dict[str, List[Path]]:
    """
    Discover configuration files in specified search paths.
    
    Args:
        search_paths: Optional list of paths to search for config files
        
    Returns:
        Dictionary mapping file types to lists of discovered files
    """
    if search_paths is None:
        search_paths = [
            Path.cwd(),
            Path.home() / ".cloudcraver",
            Path(__file__).parent,
            "/etc/cloudcraver"
        ]
    
    # Convert to Path objects
    search_paths = [Path(p) for p in search_paths]
    
    discovered_files = {
        "toml": [],
        "yaml": [],
        "json": [],
        "env": []
    }
    
    config_file_patterns = {
        "toml": ["*.toml", "settings.toml", "config.toml", "local_settings.toml"],
        "yaml": ["*.yaml", "*.yml", "config.yaml", "config.yml"],
        "json": ["*.json", "config.json", "settings.json"],
        "env": [".env", ".env.*", "*.env"]
    }
    
    for search_path in search_paths:
        if not search_path.exists() or not search_path.is_dir():
            continue
            
        for file_type, patterns in config_file_patterns.items():
            for pattern in patterns:
                for file_path in search_path.glob(pattern):
                    if file_path.is_file():
                        discovered_files[file_type].append(file_path)
    
    return discovered_files


def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a file based on its extension.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration data
        
    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file does not exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    file_extension = file_path.suffix.lower()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_extension == '.toml':
                return toml.load(f)
            elif file_extension in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            elif file_extension == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {file_extension}")
                
    except Exception as e:
        raise ValueError(f"Error loading configuration file {file_path}: {e}")


def save_config_file(config_data: Dict[str, Any], file_path: Union[str, Path], 
                    file_format: Optional[str] = None) -> bool:
    """
    Save configuration data to a file.
    
    Args:
        config_data: Configuration data to save
        file_path: Path where to save the file
        file_format: Optional format override ('toml', 'yaml', 'json')
        
    Returns:
        True if saved successfully, False otherwise
    """
    file_path = Path(file_path)
    
    # Determine format from extension if not specified
    if file_format is None:
        file_extension = file_path.suffix.lower()
        if file_extension == '.toml':
            file_format = 'toml'
        elif file_extension in ['.yaml', '.yml']:
            file_format = 'yaml'
        elif file_extension == '.json':
            file_format = 'json'
        else:
            file_format = 'toml'  # Default to TOML
    
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_format == 'toml':
                toml.dump(config_data, f)
            elif file_format == 'yaml':
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            elif file_format == 'json':
                json.dump(config_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {file_format}")
        
        return True
        
    except Exception as e:
        print(f"Error saving configuration file {file_path}: {e}")
        return False


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge multiple configuration dictionaries.
    
    Args:
        *configs: Variable number of configuration dictionaries to merge
        
    Returns:
        Merged configuration dictionary
    """
    def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    if not configs:
        return {}
    
    result = configs[0].copy()
    for config_dict in configs[1:]:
        result = deep_merge(result, config_dict)
    
    return result


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation.
    
    Args:
        key: Configuration key in dot notation (e.g., 'cloud.aws.region')
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
    try:
        return config.get(key, default)
    except:
        return default


def set_config_value(key: str, value: Any) -> bool:
    """
    Set a configuration value using dot notation.
    
    Args:
        key: Configuration key in dot notation
        value: Value to set
        
    Returns:
        True if set successfully, False otherwise
    """
    try:
        config.set(key, value)
        return True
    except:
        return False


def validate_config_structure(config_data: Dict[str, Any]) -> List[str]:
    """
    Validate the basic structure of configuration data.
    
    Args:
        config_data: Configuration data to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check for required top-level sections
    required_sections = ['app', 'cloud']
    for section in required_sections:
        if section not in config_data:
            errors.append(f"Missing required section: {section}")
    
    # Validate app section
    if 'app' in config_data:
        app_config = config_data['app']
        if not isinstance(app_config, dict):
            errors.append("'app' section must be a dictionary")
        else:
            if 'name' not in app_config:
                errors.append("Missing required field: app.name")
            if 'version' not in app_config:
                errors.append("Missing required field: app.version")
    
    # Validate cloud section
    if 'cloud' in config_data:
        cloud_config = config_data['cloud']
        if not isinstance(cloud_config, dict):
            errors.append("'cloud' section must be a dictionary")
        else:
            if 'default_provider' not in cloud_config:
                errors.append("Missing required field: cloud.default_provider")
            elif cloud_config['default_provider'] not in ['aws', 'azure', 'gcp']:
                errors.append("Invalid default_provider. Must be one of: aws, azure, gcp")
            
            if 'providers' not in cloud_config:
                errors.append("Missing required field: cloud.providers")
            elif not isinstance(cloud_config['providers'], list):
                errors.append("cloud.providers must be a list")
            elif not cloud_config['providers']:
                errors.append("cloud.providers cannot be empty")
    
    return errors


def backup_config_file(file_path: Union[str, Path], backup_suffix: str = ".backup") -> Optional[Path]:
    """
    Create a backup of a configuration file.
    
    Args:
        file_path: Path to the file to backup
        backup_suffix: Suffix to add to backup file
        
    Returns:
        Path to backup file if successful, None otherwise
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f"{backup_suffix}_{timestamp}{file_path.suffix}")
    
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"Error creating backup of {file_path}: {e}")
        return None


def get_environment_variables(prefix: str = "CLOUDCRAVER") -> Dict[str, str]:
    """
    Get environment variables with the specified prefix.
    
    Args:
        prefix: Environment variable prefix
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    prefix_with_separator = f"{prefix}_"
    
    for key, value in os.environ.items():
        if key.startswith(prefix_with_separator):
            # Remove prefix and convert to lowercase
            config_key = key[len(prefix_with_separator):].lower()
            env_vars[config_key] = value
    
    return env_vars


def normalize_config_key(key: str) -> str:
    """
    Normalize a configuration key to standard format.
    
    Args:
        key: Configuration key to normalize
        
    Returns:
        Normalized key
    """
    # Convert to lowercase and replace underscores with dots
    return key.lower().replace('_', '.')


def get_config_diff(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the difference between two configuration dictionaries.
    
    Args:
        config1: First configuration
        config2: Second configuration
        
    Returns:
        Dictionary containing the differences
    """
    def dict_diff(d1: Dict, d2: Dict, path: str = "") -> Dict[str, Any]:
        diff = {}
        
        # Check for keys in d1 but not in d2
        for key in d1:
            current_path = f"{path}.{key}" if path else key
            if key not in d2:
                diff[f"removed.{current_path}"] = d1[key]
            elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                nested_diff = dict_diff(d1[key], d2[key], current_path)
                diff.update(nested_diff)
            elif d1[key] != d2[key]:
                diff[f"changed.{current_path}"] = {"old": d1[key], "new": d2[key]}
        
        # Check for keys in d2 but not in d1
        for key in d2:
            current_path = f"{path}.{key}" if path else key
            if key not in d1:
                diff[f"added.{current_path}"] = d2[key]
        
        return diff
    
    return dict_diff(config1, config2)


def export_config(output_file: Union[str, Path], include_secrets: bool = False, 
                 file_format: str = "toml") -> bool:
    """
    Export current configuration to a file.
    
    Args:
        output_file: Path to output file
        include_secrets: Whether to include sensitive configuration
        file_format: Output format ('toml', 'yaml', 'json')
        
    Returns:
        True if exported successfully, False otherwise
    """
    try:
        # Get current configuration
        config_data = dict(config)
        
        # Remove secrets if not requested
        if not include_secrets:
            # Remove sensitive keys
            sensitive_keys = [
                'cloud.aws.access_key_id',
                'cloud.aws.secret_access_key',
                'cloud.azure.client_secret',
                'cloud.gcp.service_account_key'
            ]
            
            for key in sensitive_keys:
                keys = key.split('.')
                current = config_data
                for k in keys[:-1]:
                    if k in current and isinstance(current[k], dict):
                        current = current[k]
                    else:
                        break
                else:
                    if keys[-1] in current:
                        del current[keys[-1]]
        
        return save_config_file(config_data, output_file, file_format)
        
    except Exception as e:
        print(f"Error exporting configuration: {e}")
        return False


# Export all utility functions
__all__ = [
    'discover_config_files',
    'load_config_file',
    'save_config_file',
    'merge_configs',
    'get_config_value',
    'set_config_value',
    'validate_config_structure',
    'backup_config_file',
    'get_environment_variables',
    'normalize_config_key',
    'get_config_diff',
    'export_config'
] 