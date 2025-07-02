# Cloud Craver Plugin Development Guide

This guide provides comprehensive documentation for developing plugins for the Cloud Craver infrastructure management tool.

## Table of Contents

1. [Introduction](#introduction)
2. [Plugin Architecture](#plugin-architecture)
3. [Getting Started](#getting-started)
4. [Plugin Types](#plugin-types)
5. [Development Workflow](#development-workflow)
6. [Best Practices](#best-practices)
7. [Security Considerations](#security-considerations)
8. [Testing](#testing)
9. [Publishing](#publishing)
10. [API Reference](#api-reference)

## Introduction

Cloud Craver's plugin system allows developers to extend the platform with custom templates, providers, validators, and other functionality without modifying the core codebase. The plugin system is designed with security, performance, and ease of use in mind.

### Key Features

- **Type Safety**: Strong typing with Python type hints
- **Security**: Sandboxed execution environment with permission controls
- **Lifecycle Management**: Complete plugin lifecycle with proper cleanup
- **Dependency Management**: Automatic dependency resolution and version management
- **Hot Loading**: Load and unload plugins without restarting the application
- **Marketplace Integration**: Discover and install plugins from various sources

## Plugin Architecture

### Core Components

```
Plugin System
├── PluginManager        # Orchestrates all plugin operations
├── PluginDiscovery     # Finds and loads plugin manifests
├── PluginLoader        # Dynamic loading and installation
├── PluginRegistry      # Metadata and installation tracking
├── PluginValidator     # Security and structure validation
├── PluginSandbox       # Execution isolation and security
├── DependencyManager   # Dependency resolution and management
├── PluginMarketplace   # Plugin discovery and distribution
└── VersionManager      # Update and version management
```

### Plugin Lifecycle

1. **Discovery**: Plugin is found in search paths
2. **Validation**: Manifest and code are validated for security
3. **Loading**: Plugin module is dynamically imported
4. **Initialization**: Plugin is initialized with configuration
5. **Activation**: Plugin becomes active and ready for use
6. **Execution**: Plugin methods are called during operation
7. **Deactivation**: Plugin is temporarily disabled
8. **Cleanup**: Plugin resources are cleaned up
9. **Unloading**: Plugin is completely removed from memory

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Cloud Craver development environment
- Basic understanding of Python packaging

### Creating Your First Plugin

1. **Create Plugin Directory Structure**:
```
my_plugin/
├── plugin.json          # Plugin manifest
├── main.py             # Main plugin code
├── config.yaml         # Optional configuration
├── README.md           # Documentation
└── tests/              # Unit tests
    └── test_plugin.py
```


2. **Create Plugin Manifest** (`plugin.json`):
```json
{
  "name": "my-awesome-plugin",
  "version": "1.0.0",
  "description": "An awesome plugin that does amazing things",
  "author": "Your Name",
  "email": "your.email@example.com",
  "type": "template",
  "main_class": "MyAwesomePlugin",
  "module_path": "main",
  "license": "MIT",
  "keywords": ["template", "aws", "example"],
  "categories": ["templates"],
  "min_core_version": "1.0.0",
  "dependencies": [],
  "hooks": ["template_create"],
  "permissions": ["file_read", "temp_write"]
}
```

3. **Implement Plugin Class** (`main.py`):
```python
import logging
from typing import Dict, Any, List, Type

from cloudcraver.plugins.core import TemplatePlugin, PluginManifest
from cloudcraver.templates.base import BaseTemplate

logger = logging.getLogger(__name__)


class MyAwesomeTemplate(BaseTemplate):
    """Custom template implementation."""
    
    def generate(self) -> str:
        """Generate template content."""
        return "# My awesome template content"
    
    def validate(self) -> bool:
        """Validate template."""
        return True
    
    def render(self) -> str:
        """Render final template."""
        return self.generate()


class MyAwesomePlugin(TemplatePlugin):
    """My awesome plugin implementation."""
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        logger.info("Initializing My Awesome Plugin")
        return True
    
    async def activate(self) -> bool:
        """Activate the plugin."""
        logger.info("Activating My Awesome Plugin")
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate the plugin."""
        logger.info("Deactivating My Awesome Plugin")
        return True
    
    async def cleanup(self) -> bool:
        """Clean up plugin resources."""
        logger.info("Cleaning up My Awesome Plugin")
        return True
    
    def get_template_class(self) -> Type[BaseTemplate]:
        """Return the template class."""
        return MyAwesomeTemplate
    
    def get_supported_providers(self) -> List[str]:
        """Return supported providers."""
        return ["aws", "azure"]
```

### Installing and Testing

1. **Install Plugin**:
```bash
# Install from directory
cloudcraver plugin install ./my_plugin

# Install from package
cloudcraver plugin install my_plugin.zip
```

2. **Test Plugin**:
```bash
# List installed plugins
cloudcraver plugin list

# Test plugin functionality
cloudcraver plugin test my-awesome-plugin
```

## Plugin Types

### Template Plugins

Template plugins provide custom infrastructure templates for various cloud providers.

**Base Class**: `TemplatePlugin`

**Required Methods**:
- `get_template_class()`: Return template implementation class
- `get_supported_providers()`: Return list of supported cloud providers

**Example Use Cases**:
- Custom CloudFormation templates
- Terraform modules
- Kubernetes manifests
- Docker Compose files

### Provider Plugins

Provider plugins add support for new cloud providers or services.

**Base Class**: `ProviderPlugin`

**Required Methods**:
- `get_provider_name()`: Return provider name
- `get_template_class()`: Return provider template class
- `validate_credentials()`: Validate provider credentials

**Example Use Cases**:
- Support for new cloud providers
- Custom API integrations
- On-premises infrastructure

### Validator Plugins

Validator plugins implement custom validation rules and security checks.

**Base Class**: `ValidatorPlugin`

**Required Methods**:
- `validate()`: Perform validation and return results

**Example Use Cases**:
- Organizational policy enforcement
- Security compliance checking
- Best practice validation
- Cost optimization rules

### Hook Plugins

Hook plugins extend core functionality by responding to system events.

**Base Class**: `HookPlugin`

**Required Methods**:
- `get_hook_points()`: Return list of supported hook points

**Example Use Cases**:
- Integration with external systems
- Audit logging
- Notification systems
- Custom workflows

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone development template
git clone https://github.com/cloudcraver/plugin-template.git my-plugin
cd my-plugin

# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install
```

### 2. Implement Plugin Logic

Focus on your core plugin functionality:

```python
class MyPlugin(TemplatePlugin):
    async def initialize(self) -> bool:
        # Setup plugin resources
        # Load configuration
        # Initialize connections
        return True
    
    async def activate(self) -> bool:
        # Make plugin active
        # Register handlers
        # Start background tasks
        return True
    
    # Implement plugin-specific methods
```

### 3. Add Configuration Support

Create `config.yaml` for plugin configuration:

```yaml
# Plugin configuration schema
settings:
  api_endpoint: "https://api.example.com"
  timeout: 30
  retry_count: 3
  
defaults:
  region: "us-east-1"
  instance_type: "t3.micro"
```

### 4. Write Tests

```python
import pytest
from cloudcraver.plugins.core import PluginManifest

from main import MyAwesomePlugin


@pytest.fixture
def plugin_manifest():
    return PluginManifest(
        # ... manifest data
    )

@pytest.fixture
def plugin(plugin_manifest):
    return MyAwesomePlugin(plugin_manifest, {})

async def test_plugin_initialization(plugin):
    assert await plugin.initialize()

async def test_plugin_activation(plugin):
    await plugin.initialize()
    assert await plugin.activate()
```

### 5. Package Plugin

```bash
# Run tests
pytest

# Build package
python setup.py sdist bdist_wheel

# Validate package
cloudcraver plugin validate dist/my-plugin-1.0.0.tar.gz
```

## Best Practices

### Code Quality

1. **Use Type Hints**: Always include type hints for better IDE support and documentation
2. **Follow PEP 8**: Adhere to Python style guidelines
3. **Write Docstrings**: Document all public methods and classes
4. **Handle Errors Gracefully**: Use proper exception handling and logging

### Security

1. **Minimal Permissions**: Request only necessary permissions
2. **Validate Input**: Sanitize and validate all external input
3. **Secure Secrets**: Never hardcode credentials or secrets
4. **Use Sandbox**: Respect sandbox limitations and security boundaries

### Performance

1. **Lazy Loading**: Load resources only when needed
2. **Async Operations**: Use async/await for I/O operations
3. **Resource Cleanup**: Always clean up resources in cleanup method
4. **Caching**: Cache expensive operations when appropriate

### Configuration

1. **Schema Validation**: Define configuration schemas
2. **Sensible Defaults**: Provide reasonable default values
3. **Environment Variables**: Support environment-based configuration
4. **Documentation**: Document all configuration options

## Security Considerations

### Sandbox Environment

Plugins run in a sandboxed environment with restricted access to:

- File system (limited to temp directories and allowed paths)
- Network operations (controlled by permissions)
- System resources (CPU, memory limits)
- System calls (monitored and restricted)

### Permission System

Plugins must declare required permissions in their manifest:

```json
{
  "permissions": [
    "file_read",      // Read files from allowed paths
    "file_write",     // Write files to allowed paths
    "temp_write",     // Write to temp directories
    "network_access", // Make network requests
    "system_access"   // Access system modules (restricted)
  ]
}
```

### Code Analysis

All plugins undergo static analysis to detect:

- Dangerous imports (`os`, `subprocess`, etc.)
- Dynamic code execution (`eval`, `exec`)
- Hardcoded credentials
- Suspicious patterns

### Best Practices

1. **Principle of Least Privilege**: Request minimal permissions
2. **Input Validation**: Validate all external input
3. **Secure Defaults**: Use secure configuration defaults
4. **Regular Updates**: Keep dependencies updated

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch

class TestMyPlugin:
    @pytest.fixture
    def plugin(self):
        manifest = Mock()
        config = {"test": True}
        return MyAwesomePlugin(manifest, config)
    
    async def test_initialization(self, plugin):
        result = await plugin.initialize()
        assert result is True
    
    async def test_template_generation(self, plugin):
        template = plugin.get_template_class()("test", Mock())
        content = template.generate()
        assert "My awesome template" in content
```

### Integration Testing

```python
async def test_plugin_integration():
    # Test plugin integration with core system
    manager = PluginManager(config, data_dir, cache_dir)
    
    # Install plugin
    success = await manager.install_plugin("./my_plugin")
    assert success
    
    # Load plugin
    success = await manager.load_plugin("my-awesome-plugin")
    assert success
    
    # Test functionality
    plugin = manager.get_plugin("my-awesome-plugin")
    assert plugin is not None
```

### Manual Testing

```bash
# Install plugin in development mode
cloudcraver plugin install --dev ./my_plugin

# Test plugin commands
cloudcraver template create --plugin my-awesome-plugin test-template

# Validate generated content
cloudcraver validate test-template.json
```

## Publishing

### Plugin Registry

1. **Create Account**: Register at plugins.cloudcraver.io
2. **Verify Identity**: Complete identity verification process
3. **Submit Plugin**: Upload plugin package and metadata

### Marketplace Submission

```bash
# Login to marketplace
cloudcraver auth login

# Publish plugin
cloudcraver plugin publish dist/my-plugin-1.0.0.tar.gz

# Check publication status
cloudcraver plugin status my-awesome-plugin
```

### Distribution

- **Official Registry**: plugins.cloudcraver.io
- **GitHub Releases**: Direct installation from GitHub
- **Private Registries**: Enterprise plugin distribution
- **Local Installation**: Direct file/directory installation

## API Reference

### Core Classes

#### PluginInterface

Base interface that all plugins must implement.

```python
class PluginInterface(abc.ABC):
    async def initialize(self) -> bool: ...
    async def activate(self) -> bool: ...
    async def deactivate(self) -> bool: ...
    async def cleanup(self) -> bool: ...
```

#### TemplatePlugin

Base class for template plugins.

```python
class TemplatePlugin(PluginInterface):
    def get_template_class(self) -> Type[BaseTemplate]: ...
    def get_supported_providers(self) -> List[str]: ...
```

#### ProviderPlugin

Base class for provider plugins.

```python
class ProviderPlugin(PluginInterface):
    def get_provider_name(self) -> str: ...
    def get_template_class(self) -> Type[BaseTemplate]: ...
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool: ...
```

#### ValidatorPlugin

Base class for validator plugins.

```python
class ValidatorPlugin(PluginInterface):
    def validate(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]: ...
```

### Utility Functions

#### Hook Registration

```python
# Register a hook
self.register_hook('template_create', self._on_template_create)

# Emit a hook
results = await self.emit_hook('validation_complete', template, results)
```

#### Configuration Access

```python
# Access plugin configuration
api_key = self.config.get('api_key')
timeout = self.config.get('timeout', 30)
```

#### Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Plugin operation completed")
logger.warning("Configuration value missing")
logger.error("Operation failed", exc_info=True)
```

### Error Handling

```python
from cloudcraver.plugins.exceptions import (
    PluginError,
    PluginConfigurationError,
    PluginValidationError,
    PluginSecurityError
)

# Raise plugin-specific errors
raise PluginConfigurationError("Missing required configuration: api_key")
```

