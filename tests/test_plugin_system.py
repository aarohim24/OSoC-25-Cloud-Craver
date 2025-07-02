"""
Comprehensive tests for the plugin system.

These tests demonstrate the complete plugin system functionality
and serve as examples for plugin development.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import plugin system components
from src.plugins.core import (
    PluginManager, Plugin, PluginInterface, PluginManifest, 
    PluginMetadata, PluginType, PluginLifecycleStage
)
from src.plugins.discovery import PluginDiscovery
from src.plugins.loader import PluginLoader
from src.plugins.registry import PluginRegistry
from src.plugins.validator import PluginValidator
from src.plugins.examples.aws_s3_template import AWSS3TemplatePlugin


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_plugin_manifest():
    """Create a sample plugin manifest for testing."""
    return PluginManifest(
        metadata=PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin for demonstration",
            author="Test Author",
            email="test@example.com",
            license="MIT",
            keywords=["test", "example"],
            categories=["testing"],
            dependencies=[],
            min_core_version="1.0.0"
        ),
        plugin_type=PluginType.TEMPLATE,
        main_class="TestPlugin",
        module_path="test_plugin",
        hooks=["test_hook"],
        provides=["test_functionality"],
        permissions=["file_read"]
    )


@pytest.fixture
def mock_plugin_config():
    """Create mock plugin configuration."""
    return {
        'discovery': {'search_paths': []},
        'loader': {'isolation': True, 'temp_dir': '/tmp'},
        'validator': {'strict_mode': False},
        'security': {'enabled': True, 'max_cpu_time': 30},
        'dependencies': {'strict_versioning': True},
        'marketplace': {'repositories': []},
        'versioning': {'auto_update': False}
    }


class TestPluginManager:
    """Test the main PluginManager functionality."""
    
    @pytest.mark.asyncio
    async def test_plugin_manager_initialization(self, temp_dir, mock_plugin_config):
        """Test plugin manager initialization."""
        manager = PluginManager(mock_plugin_config, temp_dir, temp_dir / 'cache')
        
        assert manager.config == mock_plugin_config
        assert manager.data_dir == temp_dir
        assert len(manager.plugins) == 0
        assert len(manager.hooks) == 0
    
    @pytest.mark.asyncio
    async def test_plugin_discovery(self, temp_dir, mock_plugin_config):
        """Test plugin discovery functionality."""
        manager = PluginManager(mock_plugin_config, temp_dir, temp_dir / 'cache')
        
        # Create a mock plugin directory
        plugin_dir = temp_dir / 'test_plugin'
        plugin_dir.mkdir()
        
        # Create plugin manifest
        manifest_file = plugin_dir / 'plugin.json'
        manifest_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "type": "template",
            "main_class": "TestPlugin"
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest_data, f)
        
        # Discover plugins
        manifests = await manager.discover_plugins([temp_dir])
        
        assert len(manifests) == 1
        assert manifests[0].metadata.name == "test-plugin"
        assert manifests[0].plugin_type == PluginType.TEMPLATE
    
    @pytest.mark.asyncio
    async def test_plugin_loading_lifecycle(self, temp_dir, mock_plugin_config, sample_plugin_manifest):
        """Test complete plugin loading lifecycle."""
        manager = PluginManager(mock_plugin_config, temp_dir, temp_dir / 'cache')
        
        # Mock a plugin implementation
        class MockPlugin(PluginInterface):
            def __init__(self, manifest, config=None):
                super().__init__(manifest, config)
                self.initialized = False
                self.activated = False
            
            async def initialize(self):
                self.initialized = True
                return True
            
            async def activate(self):
                self.activated = True
                return True
            
            async def deactivate(self):
                self.activated = False
                return True
            
            async def cleanup(self):
                self.initialized = False
                return True
        
        # Create plugin instance
        plugin_instance = MockPlugin(sample_plugin_manifest)
        plugin = Plugin(
            instance=plugin_instance,
            manifest=sample_plugin_manifest,
            file_path=temp_dir / 'test_plugin',
            context=manager.context
        )
        
        # Test lifecycle stages
        assert plugin.stage == PluginLifecycleStage.UNLOADED
        
        await plugin.load()
        assert plugin.stage == PluginLifecycleStage.LOADED
        
        await plugin.initialize()
        assert plugin.stage == PluginLifecycleStage.INITIALIZED
        assert plugin_instance.initialized
        
        await plugin.activate()
        assert plugin.stage == PluginLifecycleStage.ACTIVE
        assert plugin_instance.activated
        
        await plugin.deactivate()
        assert plugin.stage == PluginLifecycleStage.SUSPENDED
        assert not plugin_instance.activated
        
        await plugin.unload()
        assert plugin.stage == PluginLifecycleStage.UNLOADED
        assert not plugin_instance.initialized


class TestPluginDiscovery:
    """Test plugin discovery functionality."""
    
    def test_discovery_initialization(self):
        """Test plugin discovery initialization."""
        config = {'search_paths': ['/custom/path']}
        discovery = PluginDiscovery(config)
        
        # Should include both default and custom paths
        assert len(discovery.search_paths) >= 4  # 3 default + 1 custom
        assert Path('/custom/path') in discovery.search_paths
    
    @pytest.mark.asyncio
    async def test_manifest_parsing(self, temp_dir):
        """Test plugin manifest parsing."""
        discovery = PluginDiscovery({})
        
        # Create valid manifest
        manifest_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "type": "template",
            "main_class": "TestPlugin",
            "keywords": ["test"],
            "dependencies": ["dep1>=1.0.0"]
        }
        
        manifest = discovery._parse_manifest(manifest_data, str(temp_dir))
        
        assert manifest is not None
        assert manifest.metadata.name == "test-plugin"
        assert manifest.metadata.version == "1.0.0"
        assert manifest.plugin_type == PluginType.TEMPLATE
        assert manifest.main_class == "TestPlugin"
        assert "dep1>=1.0.0" in manifest.metadata.dependencies
    
    @pytest.mark.asyncio
    async def test_invalid_manifest_handling(self, temp_dir):
        """Test handling of invalid manifests."""
        discovery = PluginDiscovery({})
        
        # Missing required fields
        invalid_manifest = {
            "name": "test-plugin",
            # Missing version, description, author, type, main_class
        }
        
        manifest = discovery._parse_manifest(invalid_manifest, str(temp_dir))
        assert manifest is None


class TestPluginValidator:
    """Test plugin validation functionality."""
    
    def test_validator_initialization(self):
        """Test plugin validator initialization."""
        config = {
            'strict_mode': True,
            'max_file_size': 2048,
            'allowed_imports': ['custom_module']
        }
        
        validator = PluginValidator(config)
        
        assert validator.strict_mode is True
        assert validator.max_file_size == 2048
        assert 'custom_module' in validator.allowed_imports
    
    @pytest.mark.asyncio
    async def test_manifest_validation(self, sample_plugin_manifest):
        """Test plugin manifest validation."""
        validator = PluginValidator({'strict_mode': False})
        
        violations = validator._validate_manifest_content(sample_plugin_manifest)
        
        # Should pass basic validation
        critical_violations = [v for v in violations if v.severity == 'critical']
        assert len(critical_violations) == 0
    
    def test_security_pattern_detection(self):
        """Test detection of security patterns in code."""
        validator = PluginValidator({'strict_mode': False})
        
        # Code with security issues
        dangerous_code = """
import os
import subprocess

def bad_function():
    os.system('rm -rf /')
    subprocess.call(['dangerous', 'command'])
    exec('malicious code')
    eval('user input')
"""
        
        violations = validator._analyze_code_patterns(dangerous_code, Path('test.py'))
        
        # Should detect multiple security issues
        assert len(violations) > 0
        critical_violations = [v for v in violations if v.severity == 'critical']
        assert len(critical_violations) > 0


class TestPluginRegistry:
    """Test plugin registry functionality."""
    
    @pytest.mark.asyncio
    async def test_registry_initialization(self, temp_dir):
        """Test plugin registry initialization."""
        registry_file = temp_dir / 'registry.json'
        registry = PluginRegistry(registry_file)
        
        assert registry.registry_file == registry_file
        assert 'plugins' in registry.registry_data
        assert 'index' in registry.registry_data
    
    @pytest.mark.asyncio
    async def test_plugin_registration(self, temp_dir, sample_plugin_manifest):
        """Test plugin registration in registry."""
        registry_file = temp_dir / 'registry.json'
        registry = PluginRegistry(registry_file)
        
        install_path = temp_dir / 'test_plugin'
        install_path.mkdir()
        
        # Register plugin
        success = await registry.register(sample_plugin_manifest, install_path)
        assert success
        
        # Verify registration
        plugin_info = await registry.get_plugin('test-plugin')
        assert plugin_info is not None
        assert plugin_info['manifest']['metadata']['name'] == 'test-plugin'
        assert plugin_info['install_path'] == str(install_path)
    
    @pytest.mark.asyncio
    async def test_plugin_listing_and_filtering(self, temp_dir, sample_plugin_manifest):
        """Test plugin listing with filters."""
        registry_file = temp_dir / 'registry.json'
        registry = PluginRegistry(registry_file)
        
        # Register test plugin
        await registry.register(sample_plugin_manifest, temp_dir / 'test_plugin')
        
        # List all plugins
        all_plugins = await registry.list_plugins()
        assert 'test-plugin' in all_plugins
        
        # Filter by type
        template_plugins = await registry.list_plugins(plugin_type='template')
        assert 'test-plugin' in template_plugins
        
        # Filter by non-matching type
        provider_plugins = await registry.list_plugins(plugin_type='provider')
        assert 'test-plugin' not in provider_plugins


class TestExamplePlugins:
    """Test the example plugins."""
    
    @pytest.mark.asyncio
    async def test_aws_s3_template_plugin(self, sample_plugin_manifest):
        """Test the AWS S3 template plugin example."""
        config = {
            'default_region': 'us-west-2',
            'enable_logging': True
        }
        
        plugin = AWSS3TemplatePlugin(sample_plugin_manifest, config)
        
        # Test initialization
        assert await plugin.initialize()
        assert await plugin.activate()
        
        # Test template class
        template_class = plugin.get_template_class()
        assert template_class is not None
        
        # Test supported providers
        providers = plugin.get_supported_providers()
        assert 'aws' in providers
        
        # Test template creation
        template = plugin.create_template('test-bucket', bucket_name='my-test-bucket')
        assert template is not None
        
        # Test template generation
        content = template.generate()
        assert content is not None
        assert 'AWS::S3::Bucket' in content
        
        # Test template validation
        assert template.validate()
        
        # Test cleanup
        assert await plugin.deactivate()
        assert await plugin.cleanup()


class TestPluginIntegration:
    """Integration tests for the complete plugin system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_plugin_workflow(self, temp_dir, mock_plugin_config):
        """Test complete end-to-end plugin workflow."""
        # Initialize plugin manager
        manager = PluginManager(mock_plugin_config, temp_dir, temp_dir / 'cache')
        
        # Create a test plugin directory structure
        plugin_dir = temp_dir / 'plugins' / 'test_plugin'
        plugin_dir.mkdir(parents=True)
        
        # Create plugin manifest
        manifest_file = plugin_dir / 'plugin.json'
        manifest_data = {
            "name": "integration-test-plugin",
            "version": "1.0.0",
            "description": "Integration test plugin",
            "author": "Test Suite",
            "type": "template",
            "main_class": "IntegrationTestPlugin",
            "module_path": "main",
            "permissions": ["file_read"]
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest_data, f)
        
        # Create plugin Python file
        plugin_file = plugin_dir / 'main.py'
        plugin_code = '''
from src.plugins.core import TemplatePlugin

class IntegrationTestPlugin(TemplatePlugin):
    async def initialize(self):
        return True
    
    async def activate(self):
        return True
    
    async def deactivate(self):
        return True
    
    async def cleanup(self):
        return True
    
    def get_template_class(self):
        return None
    
    def get_supported_providers(self):
        return ["test"]
'''
        
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        # Test discovery
        manifests = await manager.discover_plugins([temp_dir / 'plugins'])
        assert len(manifests) == 1
        assert manifests[0].metadata.name == "integration-test-plugin"
        
        # Test installation (simulated)
        plugin_manifest = manifests[0]
        await manager.registry.register(plugin_manifest, plugin_dir)
        
        # Verify registration
        registered_plugins = await manager.registry.list_plugins()
        assert "integration-test-plugin" in registered_plugins
        
        # Test plugin status
        status = manager.get_status()
        assert status['total_plugins'] == 0  # Not loaded yet
        
        # Test loading would require proper module structure
        # This is demonstrated conceptually
    
    @pytest.mark.asyncio
    async def test_plugin_hook_system(self, temp_dir, mock_plugin_config, sample_plugin_manifest):
        """Test the plugin hook system."""
        manager = PluginManager(mock_plugin_config, temp_dir, temp_dir / 'cache')
        
        # Mock plugin with hooks
        class HookTestPlugin(PluginInterface):
            def __init__(self, manifest, config=None):
                super().__init__(manifest, config)
                self.hook_called = False
            
            async def initialize(self):
                # Register a hook
                self.register_hook('test_event', self._on_test_event)
                return True
            
            async def activate(self):
                return True
            
            async def deactivate(self):
                return True
            
            async def cleanup(self):
                return True
            
            async def _on_test_event(self, data):
                self.hook_called = True
                return f"Hook processed: {data}"
        
        # Create plugin instance
        plugin_instance = HookTestPlugin(sample_plugin_manifest)
        plugin = Plugin(
            instance=plugin_instance,
            manifest=sample_plugin_manifest,
            file_path=temp_dir / 'hook_test_plugin',
            context=manager.context
        )
        
        # Initialize and activate plugin
        await plugin.initialize()
        await plugin.activate()
        
        # Add to manager
        manager.plugins['hook-test'] = plugin
        manager._register_hooks(plugin)
        
        # Emit hook
        results = await plugin_instance.emit_hook('test_event', 'test_data')
        
        assert len(results) == 1
        assert 'Hook processed: test_data' in results[0]
        assert plugin_instance.hook_called


def test_plugin_configuration_loading():
    """Test plugin configuration loading and validation."""
    from src.plugins.config.plugin_config import plugin_config
    
    # This would test loading the YAML configuration
    # For now, we'll test the structure exists
    config_file = Path('src/plugins/config/plugin_config.yaml')
    
    if config_file.exists():
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        # Test basic structure
        assert 'plugin_system' in config
        assert 'default_permissions' in config
        assert 'plugins' in config
        
        # Test plugin system configuration
        plugin_system = config['plugin_system']
        assert 'discovery' in plugin_system
        assert 'loader' in plugin_system
        assert 'validator' in plugin_system
        assert 'security' in plugin_system


if __name__ == '__main__':
    """Run tests directly for development."""
    pytest.main([__file__, '-v']) 