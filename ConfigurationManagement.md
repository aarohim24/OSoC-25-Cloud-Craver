# Configuration Management in Cloud Craver

## 📋 Overview

Cloud Craver implements a configuration management system using **Dynaconf**, providing robust, flexible, and type-safe configuration handling across multiple sources and environments. This system manages application settings, user preferences, cloud provider configurations, and validation rules with a clear hierarchy and precedence system.

## 🏗️ Architecture

### Core Components

```
Configuration Management System
├── Dynaconf Engine (Core)
├── Configuration Sources (Files, Env Vars, CLI)
├── Validation Layer (Pydantic Schemas)
├── User Preferences (Persistent Settings)
├── CLI Integration (Argument Override)
└── Utility Functions (Helpers & Tools)
```

### File Structure

```
src/config/
├── __init__.py                    # Main Dynaconf setup & exports
├── settings.toml                  # Primary configuration file
├── config.yaml                    # Structured cloud templates
├── base_config.toml              # Minimal base configuration
├── local_settings.toml           # Local dev overrides (gitignored)
├── schema.py                     # Pydantic validation schemas
├── user_preferences.py           # User preference management
├── cli_config.py                 # CLI argument integration
├── utils.py                      # Configuration utilities
└── README.md                     # Technical documentation
```

## 🔄 Configuration Flow

### 1. Initialization Process

```python
# When the application starts:
from src.config import config

# Dynaconf automatically:
# 1. Loads base_config.toml (minimal required settings)
# 2. Merges settings.toml (main application config)
# 3. Overlays config.yaml (structured templates)
# 4. Applies local_settings.toml (dev overrides)
# 5. Processes environment variables (CLOUDCRAVER_*)
# 6. Handles CLI argument overrides
```

### 2. Configuration Precedence (Highest to Lowest)

```
1. CLI Arguments          --provider aws --debug
2. Environment Variables  CLOUDCRAVER_APP__DEBUG=true
3. local_settings.toml    # Developer overrides
4. settings.toml          # Main configuration
5. config.yaml            # Structured data
6. base_config.toml       # Base requirements
```

### 3. Access Patterns

```python
# Direct access
app_name = config.app.name
debug_mode = config.app.debug

# Helper functions (recommended)
from src.config import get_cloud_config, get_user_preferences
cloud_config = get_cloud_config()
user_prefs = get_user_preferences()

# Dot notation with utils
from src.config.utils import get_config_value
aws_region = get_config_value("cloud.aws.region", default="us-east-1")
```

## 📁 Configuration Sources

### 1. Base Configuration (`base_config.toml`)

**Purpose**: Minimal required settings that all environments inherit

```toml
[app]
name = "Cloud Craver"
version = "1.0.0"

[cloud]
default_provider = "aws"
providers = ["aws"]

[user.preferences]
auto_save = false
confirm_destructive_actions = true
```

**When to Use**: Define absolute minimum settings that cannot be omitted

### 2. Main Settings (`settings.toml`)

**Purpose**: Primary application configuration with comprehensive defaults

```toml
[app]
name = "Cloud Craver"
version = "1.0.0"
debug = false
log_level = "INFO"
output_format = "rich"

[cloud]
default_provider = "aws"
providers = ["aws", "azure", "gcp"]

[cloud.aws]
profile = "default"
region = "us-east-1"
output_format = "json"

[terraform]
version = "latest"
auto_init = true
auto_plan = false

[validation]
strict_mode = false
generate_reports = true
```

**When to Use**: Main configuration that ships with the application

### 3. Structured Configuration (`config.yaml`)

**Purpose**: Complex structured data like templates, patterns, and rules

```yaml
cloud_templates:
  aws:
    compute: [ec2, ecs, eks, lambda]
    storage: [s3, ebs, efs]
    networking: [vpc, alb, nlb]

naming_patterns:
  aws:
    ec2: "{env}-{project}-{component}-{index:03d}"
    s3: "{project}-{env}-{purpose}-{random}"

security_rules:
  general:
    - name: "no_hardcoded_secrets"
      severity: "critical"
    - name: "encryption_at_rest"
      severity: "high"
```

**When to Use**: Complex structured data, templates, rules, and patterns

### 4. Local Overrides (`local_settings.toml`)

**Purpose**: Developer-specific settings that override defaults

```toml
[app]
debug = true
log_level = "DEBUG"

[cloud.aws]
profile = "my-dev-profile"
region = "us-west-2"

[user.preferences]
theme = "dark"
editor = "code"
```

**When to Use**: Personal development preferences, local testing configurations

### 5. Environment Variables

**Purpose**: Runtime configuration and deployment-specific settings

```bash
# App settings
export CLOUDCRAVER_APP__DEBUG=true
export CLOUDCRAVER_APP__LOG_LEVEL=DEBUG

# Cloud settings
export CLOUDCRAVER_CLOUD__DEFAULT_PROVIDER=azure
export CLOUDCRAVER_CLOUD__AWS__REGION=us-west-1

# Secrets (preferred for sensitive data)
export CLOUDCRAVER_CLOUD__AWS__ACCESS_KEY_ID=xxxxx
export CLOUDCRAVER_CLOUD__AWS__SECRET_ACCESS_KEY=xxxxx
```

**Naming Convention**: `CLOUDCRAVER_<SECTION>__<SUBSECTION>__<KEY>`

**When to Use**: CI/CD pipelines, container deployments, sensitive data

### 6. CLI Arguments

**Purpose**: Runtime overrides for specific operations

```bash
# Application overrides
cloudcraver --debug --log-level DEBUG

# Cloud provider selection
cloudcraver generate --provider azure --region eastus

# Validation options
cloudcraver validate --strict --fail-on-warnings

# Custom configuration
cloudcraver --config-file custom.toml --env production
```

**When to Use**: One-time overrides, testing different configurations

## 🛠️ Configuration Sections

### Application Settings (`app`)

Controls core application behavior:

```toml
[app]
name = "Cloud Craver"              # Application name
version = "1.0.0"                  # Version string
debug = false                      # Debug mode flag
log_level = "INFO"                 # Logging level
output_format = "rich"             # Output format (rich/json/text)
```

**Usage**:
```python
from src.config import config
if config.app.debug:
    print(f"Running {config.app.name} v{config.app.version}")
```

### Cloud Provider Settings (`cloud`)

Manages multi-cloud configurations:

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
location = "East US"

[cloud.gcp]
project_id = ""
region = "us-central1"
```

**Usage**:
```python
from src.config import get_cloud_config
cloud = get_cloud_config()
provider = cloud.default_provider  # "aws"
region = cloud.aws.region          # "us-east-1"
```

### User Preferences (`user`)

Manages personal user settings:

```toml
[user.preferences]
default_provider = "aws"
default_region = "us-east-1"
auto_save = true
theme = "auto"                     # auto/light/dark
editor = "vim"                     # Default editor

[user.recent]
providers = []                     # Recently used providers
regions = []                       # Recently used regions
templates = []                     # Recently used templates
```

**Usage**:
```python
from src.config.user_preferences import get_user_preferences, update_user_preference

prefs = get_user_preferences()
if prefs.auto_save:
    save_configuration()

# Update preference
update_user_preference("theme", "dark")
```

### Terraform Settings (`terraform`)

Controls Terraform-specific behavior:

```toml
[terraform]
version = "latest"
auto_init = true
auto_plan = false
state_backend = "local"

[terraform.validation]
enable_syntax_check = true
enable_security_scan = true
enable_cost_estimation = false

[terraform.security]
tfsec_enabled = true
checkov_enabled = true
terrascan_enabled = false
```

**Usage**:
```python
from src.config import get_terraform_config
tf_config = get_terraform_config()
if tf_config.auto_init:
    run_terraform_init()
```

### Validation Rules (`validation`)

Defines validation behavior and rules:

```toml
[validation]
strict_mode = false
fail_on_warnings = false
generate_reports = true

[validation.naming_conventions]
enabled = true
resource_name_pattern = "^[a-z][a-z0-9-]*[a-z0-9]$"

[validation.tagging_standards]
enabled = true
required_tags = ["Environment", "Project", "Owner"]
```

**Usage**:
```python
from src.config import get_validation_config
validation = get_validation_config()
if validation.strict_mode:
    enforce_strict_validation()
```

## 👤 User Preference Management

### Persistent Storage

User preferences are automatically saved to `user_preferences.json`:

```json
{
  "default_provider": "aws",
  "default_region": "us-east-1",
  "auto_save": true,
  "theme": "dark",
  "editor": "code",
  "recent_providers": ["aws", "azure"],
  "recent_regions": ["us-east-1", "eastus"],
  "recent_templates": ["ec2-template", "s3-bucket"],
  "last_updated": "2025-01-01T12:00:00"
}
```

### Management Functions

```python
from src.config.user_preferences import (
    get_user_preferences,
    save_user_preferences,
    update_user_preference,
    add_recent_item,
    get_recent_items
)

# Get current preferences
prefs = get_user_preferences()
print(f"Theme: {prefs.theme}")

# Update specific preference
update_user_preference("default_provider", "azure")

# Track recent usage
add_recent_item("providers", "gcp")
add_recent_item("regions", "us-central1")

# Get recent items for UI
recent_providers = get_recent_items("providers")  # ["gcp", "azure", "aws"]
```

### Preference Validation

```python
from src.config.user_preferences import UserPreferencesManager

manager = UserPreferencesManager()
prefs = get_user_preferences()

# Validate preferences
errors = manager.validate_preferences(prefs)
if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

## 🖥️ CLI Integration

### Argument Processing

The CLI system automatically processes arguments and applies them as configuration overrides:

```python
from src.config.cli_config import parse_cli_args, get_cli_overrides

# Parse CLI arguments (typically in main.py)
args = parse_cli_args()

# Get the configuration overrides
overrides = get_cli_overrides()
print(overrides)  # {"app.debug": True, "cloud.default_provider": "azure"}
```

### Available CLI Options

| Category | Option | Example | Effect |
|----------|--------|---------|--------|
| **App** | `--debug` | `--debug` | Sets `app.debug = true` |
| | `--log-level` | `--log-level DEBUG` | Sets `app.log_level = "DEBUG"` |
| | `--output-format` | `--output-format json` | Sets `app.output_format = "json"` |
| **Cloud** | `--provider` | `--provider azure` | Sets `cloud.default_provider = "azure"` |
| | `--region` | `--region eastus` | Sets cloud region for provider |
| | `--profile` | `--profile dev` | Sets cloud profile/subscription |
| **User** | `--theme` | `--theme dark` | Sets `user.preferences.theme = "dark"` |
| | `--auto-save` | `--auto-save` | Sets `user.preferences.auto_save = true` |
| **Validation** | `--strict` | `--strict` | Sets `validation.strict_mode = true` |
| | `--fail-on-warnings` | `--fail-on-warnings` | Sets `validation.fail_on_warnings = true` |
| **Config** | `--config-file` | `--config-file custom.toml` | Loads additional config file |
| | `--env` | `--env production` | Switches to production environment |

### Custom CLI Integration

```python
# In your main application
from src.config.cli_config import CLIConfigManager

def main():
    # Create CLI manager
    cli_manager = CLIConfigManager()
    
    # Add custom arguments
    cli_manager.parser.add_argument(
        "--custom-option",
        help="Custom application option"
    )
    
    # Parse arguments
    args = cli_manager.parse_args()
    
    # Apply configuration overrides
    cli_manager.apply_cli_overrides()
    
    # Use the configuration
    from src.config import config
    if config.app.debug:
        print("Debug mode enabled")
```

## 🔍 Configuration Validation

### Schema-Based Validation

Using Pydantic schemas for type-safe configuration:

```python
from src.config.schema import validate_config, CloudCraverConfig

# Validate configuration dictionary
config_dict = {
    "app": {"name": "Cloud Craver", "version": "1.0.0"},
    "cloud": {"default_provider": "aws", "providers": ["aws"]}
}

try:
    validated_config = validate_config(config_dict)
    print(f"Valid! App: {validated_config.app.name}")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Custom Validation Rules

```python
from src.config.utils import validate_config_structure

# Validate basic structure
errors = validate_config_structure(config_dict)
if errors:
    for error in errors:
        print(f"Structure error: {error}")
```

### Runtime Validation

```python
from src.config import config

# Check if configuration is valid
def validate_runtime_config():
    required_fields = [
        "app.name",
        "app.version", 
        "cloud.default_provider"
    ]
    
    for field in required_fields:
        value = get_config_value(field)
        if not value:
            raise ValueError(f"Required field missing: {field}")
```

## 🔧 Utility Functions

### Configuration Access

```python
from src.config.utils import (
    get_config_value,
    set_config_value,
    merge_configs,
    export_config
)

# Get values with defaults
aws_region = get_config_value("cloud.aws.region", default="us-east-1")
debug_mode = get_config_value("app.debug", default=False)

# Set configuration values dynamically
set_config_value("app.debug", True)
set_config_value("cloud.default_provider", "azure")

# Merge multiple configurations
base_config = load_config_file("base_config.toml")
user_config = load_config_file("user_config.toml")
merged = merge_configs(base_config, user_config)

# Export configuration
export_config("backup.toml", include_secrets=False, file_format="toml")
```

### File Operations

```python
from src.config.utils import (
    discover_config_files,
    load_config_file,
    save_config_file,
    backup_config_file
)

# Discover all configuration files
discovered = discover_config_files()
for file_type, files in discovered.items():
    print(f"{file_type}: {files}")

# Load configuration from any format
config_data = load_config_file("custom_config.yaml")

# Save configuration in different formats
save_config_file(config_data, "output.toml", file_format="toml")
save_config_file(config_data, "output.json", file_format="json")

# Create backup before modifying
backup_path = backup_config_file("settings.toml")
print(f"Backup created: {backup_path}")
```

### Environment Management

```python
from src.config.utils import get_environment_variables

# Get all Cloud Craver environment variables
env_vars = get_environment_variables("CLOUDCRAVER")
for key, value in env_vars.items():
    print(f"{key}: {value}")
```

## 🔄 Integration Patterns

### Application Startup

```python
# main.py
from src.config.cli_config import parse_cli_args
from src.config import config, get_cloud_config
from src.config.user_preferences import get_user_preferences

def main():
    # Parse CLI arguments and apply to configuration
    args = parse_cli_args()
    
    # Load configuration
    app_config = config.app
    cloud_config = get_cloud_config()
    user_prefs = get_user_preferences()
    
    # Configure logging
    import logging
    logging.basicConfig(level=getattr(logging, app_config.log_level))
    
    if app_config.debug:
        logging.info(f"Starting {app_config.name} v{app_config.version}")
        logging.info(f"Cloud provider: {cloud_config.default_provider}")
        logging.info(f"User theme: {user_prefs.theme}")
    
    # Continue with application logic...
```

### Module Configuration

```python
# cloud_provider.py
from src.config import get_cloud_config

class CloudProvider:
    def __init__(self):
        self.config = get_cloud_config()
        self.provider = self.config.default_provider
        
    def get_credentials(self):
        if self.provider == "aws":
            return {
                "profile": self.config.aws.profile,
                "region": self.config.aws.region
            }
        elif self.provider == "azure":
            return {
                "subscription_id": self.config.azure.subscription_id,
                "location": self.config.azure.location
            }
```

### Configuration-Driven Features

```python
# validator.py
from src.config import get_validation_config, get_terraform_config

class TerraformValidator:
    def __init__(self):
        self.validation_config = get_validation_config()
        self.terraform_config = get_terraform_config()
    
    def validate(self, terraform_code):
        results = []
        
        if self.terraform_config.validation.enable_syntax_check:
            results.append(self.check_syntax(terraform_code))
            
        if self.terraform_config.validation.enable_security_scan:
            if self.terraform_config.security.tfsec_enabled:
                results.append(self.run_tfsec(terraform_code))
            if self.terraform_config.security.checkov_enabled:
                results.append(self.run_checkov(terraform_code))
        
        if self.validation_config.strict_mode:
            self.enforce_strict_rules(results)
            
        return results
```

## 🌍 Environment Management

### Environment-Specific Configurations

When `environments=True` is enabled, configurations can be organized by environment:

```toml
# settings.toml
[default]
app_name = "Cloud Craver"
debug = false

[development]
debug = true
log_level = "DEBUG"
cloud_default_provider = "aws"

[staging]
debug = false
log_level = "INFO"
cloud_default_provider = "azure"

[production] 
debug = false
log_level = "WARNING"
cloud_default_provider = "gcp"
```

### Environment Switching

```python
from src.config import settings

# Switch environments programmatically
settings.setenv("production")

# Or use environment variable
import os
os.environ["CLOUDCRAVER_ENV"] = "production"

# Or use CLI
# cloudcraver --env production
```

## 🔐 Security Considerations

### Secrets Management

**DO NOT** store sensitive data in configuration files. Use:

1. **Environment Variables** (Recommended):
   ```bash
   export CLOUDCRAVER_CLOUD__AWS__ACCESS_KEY_ID=xxxxx
   export CLOUDCRAVER_CLOUD__AWS__SECRET_ACCESS_KEY=xxxxx
   ```

2. **Secrets File** (Local development only):
   ```toml
   # .secrets.toml (gitignored)
   [cloud.aws]
   access_key_id = "your-key"
   secret_access_key = "your-secret"
   ```

3. **External Secret Management**:
   - AWS Secrets Manager
   - Azure Key Vault  
   - HashiCorp Vault
   - Kubernetes Secrets

### Configuration Validation

```python
# Validate sensitive configuration
def validate_secrets():
    cloud_config = get_cloud_config()
    
    if cloud_config.default_provider == "aws":
        access_key = get_config_value("cloud.aws.access_key_id")
        if not access_key:
            raise ValueError("AWS access key not configured")
```

## 🧪 Testing Configuration

### Unit Testing

```python
# test_config.py
import pytest
from src.config.schema import validate_config

def test_valid_configuration():
    valid_config = {
        "app": {"name": "Test App", "version": "1.0.0"},
        "cloud": {"default_provider": "aws", "providers": ["aws"]}
    }
    result = validate_config(valid_config)
    assert result.app.name == "Test App"

def test_invalid_provider():
    invalid_config = {
        "app": {"name": "Test App", "version": "1.0.0"},
        "cloud": {"default_provider": "invalid", "providers": ["invalid"]}
    }
    with pytest.raises(ValidationError):
        validate_config(invalid_config)
```

### Integration Testing

```python
# test_integration.py
from src.config import config
from src.config.user_preferences import update_user_preference

def test_configuration_integration():
    # Test that user preferences override defaults
    original_provider = config.cloud.default_provider
    
    update_user_preference("default_provider", "azure")
    # Verify the change took effect
    
    # Cleanup
    update_user_preference("default_provider", original_provider)
```

## 📈 Performance Considerations

### Lazy Loading

Configuration is loaded lazily - only when first accessed:

```python
# This doesn't load configuration
from src.config import config

# This triggers configuration loading
app_name = config.app.name
```

### Caching

Configuration values are cached after first access:

```python
# First access - loads from files
provider1 = config.cloud.default_provider

# Subsequent access - uses cached value
provider2 = config.cloud.default_provider  # Fast!
```

### Reloading

Force reload when configuration changes:

```python
from src.config import reload_config

# Reload configuration from all sources
reload_config()
```

## 🔍 Debugging Configuration

### Debug Mode

Enable debug logging to see configuration loading:

```python
from src.config import settings
settings.configure(debug=True)
```

### Configuration Inspection

```python
# See all configuration keys
from src.config import config
print(list(config.keys()))

# Get configuration sources
from src.config import get_config_sources
print(get_config_sources())

# Check specific values
from src.config.utils import get_config_value
debug_enabled = get_config_value("app.debug", default=False)
print(f"Debug: {debug_enabled}")
```

### Common Issues

1. **Configuration not loading**:
   - Check file paths and permissions
   - Verify TOML/YAML syntax
   - Ensure files exist in expected locations

2. **Environment variables ignored**:
   - Verify `CLOUDCRAVER_` prefix
   - Use double underscores: `CLOUDCRAVER_APP__DEBUG`
   - Check variable types

3. **Validation errors**:
   - Review schema definitions
   - Check required fields
   - Verify enum values

## 🚀 Best Practices

### 1. Configuration Organization

- **Use base_config.toml** for absolute minimums
- **Use settings.toml** for application defaults  
- **Use config.yaml** for complex structured data
- **Use local_settings.toml** for development overrides
- **Use environment variables** for secrets and deployment settings

### 2. Naming Conventions

- **Files**: `snake_case` or `kebab-case`
- **Configuration keys**: `snake_case` 
- **Environment variables**: `UPPERCASE_WITH_UNDERSCORES`
- **CLI arguments**: `kebab-case` (`--log-level`)

### 3. Security

- Never commit secrets to version control
- Use environment variables for sensitive data
- Validate configuration on startup
- Use type-safe access patterns

### 4. Documentation

- Comment configuration files extensively
- Document environment variable requirements  
- Provide examples for all configuration options
- Keep this documentation updated

### 5. Testing

- Test configuration loading in CI/CD
- Validate configuration schemas  
- Test environment variable handling
- Mock configuration in unit tests

## 📚 Additional Resources

- **Dynaconf Documentation**: [https://dynaconf.readthedocs.io/](https://dynaconf.readthedocs.io/)
- **Pydantic Documentation**: [https://pydantic-docs.helpmanual.io/](https://pydantic-docs.helpmanual.io/)
- **TOML Specification**: [https://toml.io/](https://toml.io/)
- **Configuration Source Code**: `src/config/`
- **Test Examples**: `tests/test_config.py`

---

This configuration management system provides a robust foundation for Cloud Craver's settings, ensuring maintainability, flexibility, and type safety across all application components. 