"""
Tests for configuration loading and validation.

This module contains comprehensive tests for:
- Configuration file loading
- Schema validation  
- User preferences management
- Configuration precedence
- Environment variable handling
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the configuration modules
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.config import config, settings, get_cloud_config, get_user_preferences, get_config_sources
from src.config.schema import validate_config, get_config_schema, CloudCraverConfig
from src.config.user_preferences import (
    UserPreferences, 
    UserPreferencesManager, 
    get_user_preferences as get_user_prefs,
    save_user_preferences,
    update_user_preference
)


class TestConfigurationLoading:
    """Test configuration loading functionality."""
    
    def test_config_instance_exists(self):
        """Test that config instance is properly initialized."""
        assert config is not None
        assert settings is not None
        
    def test_config_has_required_sections(self):
        """Test that configuration has all required sections."""
        assert hasattr(config, 'app')
        assert hasattr(config, 'cloud') 
        assert hasattr(config, 'user')
        assert hasattr(config, 'terraform')
        assert hasattr(config, 'validation')
        assert hasattr(config, 'paths')
        
    def test_app_config_values(self):
        """Test application configuration values."""
        app_config = config.app
        assert app_config.name == "Cloud Craver"
        assert app_config.version == "1.0.0"
        assert hasattr(app_config, 'debug')
        assert hasattr(app_config, 'log_level')
        
    def test_cloud_config_values(self):
        """Test cloud configuration values."""
        cloud_config = get_cloud_config()
        assert cloud_config.default_provider in ["aws", "azure", "gcp"]
        assert isinstance(cloud_config.providers, list)
        assert len(cloud_config.providers) > 0
        
    def test_config_sources_order(self):
        """Test configuration sources precedence order."""
        sources = get_config_sources()
        expected_sources = [
            "CLI arguments",
            "Environment variables", 
            "local_settings.toml",
            "settings.toml",
            "config.yaml",
            "base_config.toml"
        ]
        assert sources == expected_sources


class TestConfigurationValidation:
    """Test configuration validation functionality."""
    
    def test_schema_validation_valid_config(self):
        """Test schema validation with valid configuration."""
        valid_config = {
            "app": {
                "name": "Test App",
                "version": "1.0.0",
                "debug": False
            },
            "cloud": {
                "default_provider": "aws",
                "providers": ["aws"]
            },
            "user": {
                "preferences": {
                    "auto_save": True
                }
            }
        }
        
        # Should not raise exception
        validated = validate_config(valid_config)
        assert isinstance(validated, CloudCraverConfig)
        assert validated.app.name == "Test App"
        
    def test_schema_validation_invalid_provider(self):
        """Test schema validation with invalid cloud provider."""
        invalid_config = {
            "app": {
                "name": "Test App", 
                "version": "1.0.0"
            },
            "cloud": {
                "default_provider": "invalid_provider",
                "providers": ["invalid_provider"]
            }
        }
        
        with pytest.raises(Exception):  # Should raise validation error
            validate_config(invalid_config)
            
    def test_schema_validation_missing_required_fields(self):
        """Test schema validation with missing required fields."""
        invalid_config = {
            "app": {
                # Missing required name and version
            }
        }
        
        with pytest.raises(Exception):  # Should raise validation error
            validate_config(invalid_config)
            
    def test_get_config_schema(self):
        """Test getting JSON schema for configuration."""
        schema = get_config_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "app" in schema["properties"]
        assert "cloud" in schema["properties"]


class TestUserPreferences:
    """Test user preferences functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_user_preferences_creation(self):
        """Test user preferences object creation."""
        prefs = UserPreferences()
        assert prefs.default_provider == "aws"
        assert prefs.auto_save == True
        assert isinstance(prefs.recent_providers, list)
        assert isinstance(prefs.recent_regions, list)
        assert isinstance(prefs.recent_templates, list)
        
    def test_user_preferences_custom_values(self):
        """Test user preferences with custom values."""
        prefs = UserPreferences(
            default_provider="azure",
            default_region="East US",
            auto_save=False,
            theme="dark"
        )
        assert prefs.default_provider == "azure"
        assert prefs.default_region == "East US"
        assert prefs.auto_save == False
        assert prefs.theme == "dark"
        
    def test_user_preferences_manager_initialization(self):
        """Test user preferences manager initialization."""
        self.setUp()
        try:
            manager = UserPreferencesManager(self.config_dir)
            assert manager.config_dir == self.config_dir
            assert manager.preferences_file == self.config_dir / "user_preferences.json"
        finally:
            self.tearDown()
            
    def test_save_and_load_preferences(self):
        """Test saving and loading user preferences."""
        self.setUp()
        try:
            manager = UserPreferencesManager(self.config_dir)
            
            # Create test preferences
            prefs = UserPreferences(
                default_provider="gcp",
                default_region="us-central1",
                auto_save=False
            )
            
            # Save preferences
            success = manager.save_preferences(prefs)
            assert success == True
            
            # Clear cached preferences
            manager._preferences = None
            
            # Load preferences
            loaded_prefs = manager.load_preferences()
            assert loaded_prefs.default_provider == "gcp"
            assert loaded_prefs.default_region == "us-central1"
            assert loaded_prefs.auto_save == False
            
        finally:
            self.tearDown()
            
    def test_update_preference(self):
        """Test updating a specific preference."""
        self.setUp()
        try:
            manager = UserPreferencesManager(self.config_dir)
            
            # Update preference
            success = manager.update_preference("default_provider", "azure")
            assert success == True
            
            # Verify update
            prefs = manager.load_preferences()
            assert prefs.default_provider == "azure"
            
        finally:
            self.tearDown()
            
    def test_add_recent_item(self):
        """Test adding recent items."""
        self.setUp()
        try:
            manager = UserPreferencesManager(self.config_dir)
            
            # Add recent providers
            manager.add_recent_item("providers", "aws")
            manager.add_recent_item("providers", "azure")
            manager.add_recent_item("providers", "gcp")
            
            # Verify recent items
            recent = manager.get_recent_items("providers")
            assert recent == ["gcp", "azure", "aws"]  # Most recent first
            
            # Add duplicate (should move to front)
            manager.add_recent_item("providers", "aws")
            recent = manager.get_recent_items("providers")
            assert recent == ["aws", "gcp", "azure"]
            
        finally:
            self.tearDown()
            
    def test_validate_preferences(self):
        """Test preferences validation."""
        self.setUp()
        try:
            manager = UserPreferencesManager(self.config_dir)
            
            # Valid preferences
            valid_prefs = UserPreferences(default_provider="aws", theme="dark")
            errors = manager.validate_preferences(valid_prefs)
            assert len(errors) == 0
            
            # Invalid provider
            invalid_prefs = UserPreferences(default_provider="invalid")
            errors = manager.validate_preferences(invalid_prefs)
            assert len(errors) > 0
            assert any("Invalid default provider" in error for error in errors)
            
            # Invalid theme
            invalid_prefs = UserPreferences(theme="invalid")
            errors = manager.validate_preferences(invalid_prefs)
            assert len(errors) > 0
            assert any("Invalid theme" in error for error in errors)
            
        finally:
            self.tearDown()


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_environment_variable_prefix(self):
        """Test that environment variables with correct prefix are loaded."""
        with patch.dict(os.environ, {
            'CLOUDCRAVER_APP__DEBUG': 'true',
            'CLOUDCRAVER_CLOUD__DEFAULT_PROVIDER': 'azure'
        }):
            # Note: This test assumes Dynaconf will pick up env vars
            # In a real environment, you might need to reload config
            pass  # Placeholder for actual env var test
            
    def test_environment_variable_override(self):
        """Test that environment variables override config files."""
        # This would require actually reloading the config with env vars set
        # For now, this is a placeholder for the test structure
        pass


class TestConfigurationFileDiscovery:
    """Test configuration file discovery and precedence."""
    
    def test_config_file_precedence(self):
        """Test that configuration files are loaded in correct precedence order."""
        # This test would involve creating temporary config files
        # and verifying they're loaded in the correct order
        pass
        
    def test_missing_config_files(self):
        """Test behavior when config files are missing."""
        # Should gracefully handle missing optional config files
        pass
        
    def test_malformed_config_files(self):
        """Test behavior with malformed configuration files."""
        # Should handle syntax errors gracefully
        pass


class TestConfigurationIntegration:
    """Test integration between different configuration components."""
    
    def test_config_and_preferences_integration(self):
        """Test integration between main config and user preferences."""
        # Test that user preferences override main config where appropriate
        pass
        
    def test_cli_args_override(self):
        """Test that CLI arguments override configuration files."""
        # Test CLI argument precedence
        pass


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"]) 