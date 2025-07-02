# Cloud Craver Configuration System

A comprehensive configuration management system built with Dynaconf for the Cloud Craver application. This system provides robust configuration handling with multiple sources, validation, user preferences, and CLI integration.

## 🌟 Features

- **Multiple Configuration Sources**: Support for TOML, YAML, JSON, and environment variables
- **Configuration Precedence**: Clear hierarchy for configuration overrides
- **Schema Validation**: Type-safe configuration with Pydantic schemas
- **User Preferences**: Persistent user-specific settings
- **CLI Integration**: Command-line argument support with automatic configuration updates
- **Environment Support**: Development, production, and custom environment configurations
- **File Discovery**: Automatic discovery of configuration files
- **Configuration Export/Import**: Easy backup and sharing of configurations

## 📁 Configuration Structure

```
src/config/
├── __init__.py              # Main configuration module
├── settings.toml            # Default application settings
├── config.yaml              # Additional structured configuration
├── base_config.toml         # Minimal base configuration
├── local_settings.toml      # Local overrides (gitignored)
├── schema.py                # Pydantic validation schemas
├── user_preferences.py      # User preferences management
├── cli_config.py            # CLI argument integration
├── utils.py                 # Configuration utilities
├── demo.py                  # Demonstration script
└── README.md                # This documentation
```

## 🚀 Quick Start

### Basic Usage

```python
from src.config import config, get_cloud_config, get_user_preferences

# Access application configuration
app_name = config.app.name
debug_mode = config.app.debug

# Access cloud provider configuration
cloud_config = get_cloud_config()
default_provider = cloud_config.default_provider
aws_region = cloud_config.aws.region

# Access user preferences
user_prefs = get_user_preferences()
theme = user_prefs.theme
auto_save = user_prefs.auto_save
```

### CLI Integration

```bash
# Override configuration via CLI arguments
cloudcraver --provider aws --region us-west-2 --debug
cloudcraver --config-file custom.toml --theme dark
cloudcraver --env production --strict --fail-on-warnings
```

### Environment Variables

```bash
# Set configuration via environment variables
export CLOUDCRAVER_APP__DEBUG=true
export CLOUDCRAVER_CLOUD__DEFAULT_PROVIDER=azure
export CLOUDCRAVER_USER__PREFERENCES__THEME=dark
```

## 📋 Configuration Sources & Precedence

Configuration is loaded from multiple sources in the following order (highest to lowest precedence):

1. **CLI Arguments** - Command-line flags and options
2. **Environment Variables** - Variables prefixed with `CLOUDCRAVER_`
3. **local_settings.toml** - Local development overrides
4. **settings.toml** - Main application configuration
5. **config.yaml** - Additional structured configuration
6. **base_config.toml** - Minimal base configuration

## ⚙️ Configuration Sections

### Application Configuration (`app`)

```toml
[app]
name = "Cloud Craver"
version = "1.0.0"
debug = false
log_level = "INFO"
output_format = "rich"  # Options: "rich", "json", "text"
```

### Cloud Provider Configuration (`cloud`)

```toml
[cloud]
default_provider = "aws"
providers = ["aws", "azure", "gcp"]

[cloud.aws]
profile = "default"
region = "us-east-1"
output_format = "json"

[cloud.azure]
subscription_id = ""
resource_group_prefix = "rg-cloudcraver"
location = "East US"

[cloud.gcp]
project_id = ""
region = "us-central1"
zone = "us-central1-a"
```

### User Preferences (`user`)

```toml
[user.preferences]
default_provider = "aws"
default_region = "us-east-1"
auto_save = true
confirm_destructive_actions = true
theme = "auto"  # Options: "auto", "light", "dark"
editor = "vim"
```

### Terraform Configuration (`terraform`)

```toml
[terraform]
version = "latest"
auto_init = true
auto_plan = false
auto_apply = false
state_backend = "local"  # Options: "local", "s3", "azurerm", "gcs"

[terraform.validation]
enable_syntax_check = true
enable_security_scan = true
enable_cost_estimation = false
enable_drift_detection = false
```

### Validation Configuration (`validation`)

```toml
[validation]
strict_mode = false
fail_on_warnings = false
generate_reports = true
report_format = "json"  # Options: "json", "html", "text"

[validation.naming_conventions]
enabled = true
resource_name_pattern = "^[a-z][a-z0-9-]*[a-z0-9]$"
tag_requirements = ["Environment", "Project", "Owner"]
```

## 👤 User Preferences Management

### Loading and Saving Preferences

```python
from src.config.user_preferences import (
    get_user_preferences, 
    save_user_preferences, 
    update_user_preference,
    UserPreferences
)

# Get current preferences
prefs = get_user_preferences()

# Update a specific preference
update_user_preference("default_provider", "azure")

# Create custom preferences
custom_prefs = UserPreferences(
    default_provider="gcp",
    theme="dark",
    auto_save=True
)
save_user_preferences(custom_prefs)
```

### Recent Items Tracking

```python
from src.config.user_preferences import add_recent_item, get_recent_items

# Add recent items
add_recent_item("providers", "aws")
add_recent_item("regions", "us-east-1")
add_recent_item("templates", "ec2-template")

# Get recent items
recent_providers = get_recent_items("providers")
recent_regions = get_recent_items("regions")
```

## 🔧 CLI Configuration

### Available CLI Options

| Option | Description | Example |
|--------|-------------|---------|
| `--config-file` | Custom configuration file | `--config-file custom.toml` |
| `--config-dir` | Configuration directory | `--config-dir /path/to/config` |
| `--debug` | Enable debug mode | `--debug` |
| `--log-level` | Set logging level | `--log-level DEBUG` |
| `--provider` | Cloud provider | `--provider azure` |
| `--region` | Cloud region | `--region us-west-2` |
| `--theme` | UI theme | `--theme dark` |
| `--strict` | Strict validation | `--strict` |
| `--env` | Environment | `--env production` |

### CLI Integration Example

```python
from src.config.cli_config import parse_cli_args, get_cli_overrides

# Parse CLI arguments and apply to configuration
args = parse_cli_args()

# Get configuration overrides from CLI
overrides = get_cli_overrides()
```

## 🔍 Configuration Validation

### Schema Validation

```python
from src.config.schema import validate_config, get_config_schema

# Validate configuration
config_dict = {"app": {"name": "Test", "version": "1.0.0"}}
validated_config = validate_config(config_dict)

# Get JSON schema
schema = get_config_schema()
```

### Custom Validation

The system includes built-in validators for:
- Cloud provider validation
- User preference validation
- Path validation
- Type checking

## 🛠️ Utility Functions

### Configuration Access

```python
from src.config.utils import (
    get_config_value,
    set_config_value,
    export_config,
    merge_configs
)

# Get configuration values with dot notation
app_name = get_config_value("app.name")
aws_region = get_config_value("cloud.aws.region", default="us-east-1")

# Set configuration values
set_config_value("demo.test", "value")

# Export configuration
export_config("/tmp/config_backup.toml", file_format="toml")
```

### File Discovery

```python
from src.config.utils import discover_config_files, load_config_file

# Discover configuration files
discovered = discover_config_files()

# Load configuration from file
config_data = load_config_file("custom_config.toml")
```

## 🌍 Environment Support

### Environment-Specific Configuration

Create environment-specific settings:

```toml
# Development environment
[development]
debug = true
log_level = "DEBUG"
enable_hot_reload = true

# Production environment  
[production]
debug = false
log_level = "INFO"
enable_hot_reload = false
```

### Switching Environments

```python
from src.config import settings

# Switch to production environment
settings.setenv("production")

# Use environment variable
export CLOUDCRAVER_ENV=production
```

## 🔐 Secrets Management

### Secrets File

Create a `.secrets.toml` file (gitignored) for sensitive data:

```toml
[cloud.aws]
access_key_id = "your-access-key"
secret_access_key = "your-secret-key"

[cloud.azure]
client_secret = "your-client-secret"

[cloud.gcp]
service_account_key = "path/to/service-account.json"
```

### Environment Variables for Secrets

```bash
export CLOUDCRAVER_CLOUD__AWS__ACCESS_KEY_ID="your-access-key"
export CLOUDCRAVER_CLOUD__AWS__SECRET_ACCESS_KEY="your-secret-key"
```

## 📚 Local Development Setup

### Creating Local Settings

1. Copy the example file:
   ```bash
   cp src/config/local_settings.example.toml src/config/local_settings.toml
   ```

2. Customize for your environment:
   ```toml
   [app]
   debug = true
   log_level = "DEBUG"
   
   [cloud.aws]
   profile = "my-dev-profile"
   region = "us-west-2"
   
   [user.preferences]
   default_provider = "aws"
   theme = "dark"
   editor = "code"
   ```

### Gitignore Configuration

The following files are automatically ignored:
- `src/config/local_settings.toml`
- `src/config/.secrets.toml`
- `src/config/user_preferences.json`
- `src/config/user_preferences.backup.json`

## 🧪 Testing

### Running Configuration Tests

```bash
# Run all configuration tests
python -m pytest tests/test_config.py -v

# Run specific test class
python -m pytest tests/test_config.py::TestConfigurationLoading -v

# Run with coverage
python -m pytest tests/test_config.py --cov=src.config
```

### Demo Script

Run the comprehensive demo to see all features in action:

```bash
cd src/config
python demo.py
```

## 🔧 Advanced Usage

### Custom Configuration Loaders

```python
from src.config.utils import load_config_file, merge_configs

# Load multiple configuration files
config1 = load_config_file("base.toml")
config2 = load_config_file("override.yaml")

# Merge configurations
merged = merge_configs(config1, config2)
```

### Configuration Validation

```python
from src.config.utils import validate_config_structure

# Validate configuration structure
errors = validate_config_structure(config_dict)
if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

### Configuration Backup

```python
from src.config.utils import backup_config_file

# Create backup of configuration file
backup_path = backup_config_file("settings.toml")
print(f"Backup created: {backup_path}")
```

## 📖 Best Practices

1. **Use Environment-Specific Settings**: Create separate configurations for development, staging, and production
2. **Keep Secrets Secure**: Never commit secrets to version control; use environment variables or secret files
3. **Validate Configuration**: Use the built-in validation to catch configuration errors early
4. **Document Custom Settings**: Add comments to configuration files explaining custom settings
5. **Use Local Overrides**: Use `local_settings.toml` for development-specific overrides
6. **Test Configuration Changes**: Run tests after making configuration changes
7. **Export Configurations**: Regularly export configurations for backup purposes

## 🐛 Troubleshooting

### Common Issues

1. **Configuration Not Loading**
   - Check file paths and permissions
   - Verify file syntax (TOML/YAML/JSON)
   - Check environment variable names

2. **Validation Errors**
   - Review the schema definitions in `schema.py`
   - Check required fields and types
   - Verify provider names and other enum values

3. **CLI Arguments Not Working**
   - Ensure arguments are parsed before accessing configuration
   - Check for conflicting arguments
   - Verify argument names match expected patterns

4. **Environment Variables Ignored**
   - Verify the `CLOUDCRAVER_` prefix
   - Use double underscores for nested keys: `CLOUDCRAVER_APP__DEBUG`
   - Check variable types (strings need quotes for booleans)

### Debug Mode

Enable debug mode to see configuration loading details:

```python
from src.config import settings
settings.configure(debug=True)
```

## 🤝 Contributing

When contributing to the configuration system:

1. **Add Tests**: Include tests for new configuration features
2. **Update Schema**: Update Pydantic schemas for new configuration options
3. **Document Changes**: Update this README and inline documentation
4. **Validate Backwards Compatibility**: Ensure changes don't break existing configurations
5. **Test Multiple Sources**: Test configuration loading from all sources

## 📄 License

This configuration system is part of the Cloud Craver project and follows the same license terms. 