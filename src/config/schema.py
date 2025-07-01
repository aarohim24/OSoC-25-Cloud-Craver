"""
Configuration schema validation using Pydantic.

This module defines the schema for validating configuration files
and provides type-safe access to configuration values.
"""

from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, root_validator
from pathlib import Path
import os


class AppConfig(BaseModel):
    """Application configuration schema."""
    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    description: Optional[str] = Field(None, description="Application description")
    debug: bool = Field(False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field("INFO")
    output_format: Literal["rich", "json", "text"] = Field("rich")


class CloudRegionsConfig(BaseModel):
    """Cloud provider default regions configuration."""
    aws: str = Field("us-east-1", description="Default AWS region")
    azure: str = Field("East US", description="Default Azure region") 
    gcp: str = Field("us-central1", description="Default GCP region")


class AWSConfig(BaseModel):
    """AWS-specific configuration."""
    profile: str = Field("default", description="AWS profile to use")
    region: str = Field("us-east-1", description="Default AWS region")
    output_format: Literal["json", "text", "table"] = Field("json")


class AzureConfig(BaseModel):
    """Azure-specific configuration."""
    subscription_id: Optional[str] = Field(None, description="Azure subscription ID")
    resource_group_prefix: str = Field("rg-cloudcraver", description="Resource group prefix")
    location: str = Field("East US", description="Default Azure location")


class GCPConfig(BaseModel):
    """GCP-specific configuration."""
    project_id: Optional[str] = Field(None, description="GCP project ID")
    region: str = Field("us-central1", description="Default GCP region")
    zone: str = Field("us-central1-a", description="Default GCP zone")


class CloudConfig(BaseModel):
    """Cloud provider configuration schema."""
    default_provider: Literal["aws", "azure", "gcp"] = Field("aws")
    providers: List[Literal["aws", "azure", "gcp"]] = Field(["aws"])
    default_regions: CloudRegionsConfig = Field(default_factory=CloudRegionsConfig)
    aws: AWSConfig = Field(default_factory=AWSConfig)
    azure: AzureConfig = Field(default_factory=AzureConfig)
    gcp: GCPConfig = Field(default_factory=GCPConfig)
    
    @validator('providers')
    def validate_providers(cls, v):
        """Ensure at least one provider is specified."""
        if not v:
            raise ValueError("At least one cloud provider must be specified")
        return v
    
    @root_validator
    def validate_default_provider_in_providers(cls, values):
        """Ensure default provider is in the providers list."""
        default_provider = values.get('default_provider')
        providers = values.get('providers', [])
        
        if default_provider and default_provider not in providers:
            raise ValueError(f"Default provider '{default_provider}' must be in providers list")
        
        return values


class UserPreferencesConfig(BaseModel):
    """User preferences configuration schema."""
    default_provider: Optional[Literal["aws", "azure", "gcp"]] = Field(None)
    default_region: Optional[str] = Field(None)
    auto_save: bool = Field(True)
    confirm_destructive_actions: bool = Field(True)
    theme: Literal["auto", "light", "dark"] = Field("auto")
    editor: str = Field("vim")


class UserRecentConfig(BaseModel):
    """User recent items configuration schema."""
    providers: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list) 
    templates: List[str] = Field(default_factory=list)


class UserConfig(BaseModel):
    """User configuration schema."""
    preferences: UserPreferencesConfig = Field(default_factory=UserPreferencesConfig)
    recent: UserRecentConfig = Field(default_factory=UserRecentConfig)


class TerraformValidationConfig(BaseModel):
    """Terraform validation configuration schema."""
    enable_syntax_check: bool = Field(True)
    enable_security_scan: bool = Field(True)
    enable_cost_estimation: bool = Field(False)
    enable_drift_detection: bool = Field(False)


class TerraformSecurityConfig(BaseModel):
    """Terraform security scanning configuration schema."""
    tfsec_enabled: bool = Field(True)
    checkov_enabled: bool = Field(True)
    terrascan_enabled: bool = Field(False)
    custom_rules_enabled: bool = Field(True)


class TerraformConfig(BaseModel):
    """Terraform configuration schema."""
    version: str = Field("latest")
    auto_init: bool = Field(True)
    auto_plan: bool = Field(False)
    auto_apply: bool = Field(False)
    state_backend: Literal["local", "s3", "azurerm", "gcs"] = Field("local")
    validation: TerraformValidationConfig = Field(default_factory=TerraformValidationConfig)
    security: TerraformSecurityConfig = Field(default_factory=TerraformSecurityConfig)


class NamingConventionsConfig(BaseModel):
    """Naming conventions validation configuration schema."""
    enabled: bool = Field(True)
    resource_name_pattern: str = Field("^[a-z][a-z0-9-]*[a-z0-9]$")
    tag_requirements: List[str] = Field(["Environment", "Project", "Owner"])


class TaggingStandardsConfig(BaseModel):
    """Tagging standards validation configuration schema."""
    enabled: bool = Field(True)
    required_tags: List[str] = Field(["Environment", "Project", "Owner", "CostCenter"])
    allowed_environments: List[str] = Field(["dev", "staging", "prod"])


class ValidationConfig(BaseModel):
    """Validation configuration schema."""
    strict_mode: bool = Field(False)
    fail_on_warnings: bool = Field(False)
    generate_reports: bool = Field(True)
    report_format: Literal["json", "html", "text"] = Field("json")
    naming_conventions: NamingConventionsConfig = Field(default_factory=NamingConventionsConfig)
    tagging_standards: TaggingStandardsConfig = Field(default_factory=TaggingStandardsConfig)


class PathsConfig(BaseModel):
    """Paths configuration schema."""
    templates_dir: str = Field("templates")
    output_dir: str = Field("output")
    cache_dir: str = Field(".cache")
    logs_dir: str = Field("logs")
    
    @validator('templates_dir', 'output_dir', 'cache_dir', 'logs_dir')
    def validate_paths(cls, v):
        """Ensure paths are valid."""
        if not v:
            raise ValueError("Path cannot be empty")
        return v


class GenerationConfig(BaseModel):
    """Template generation configuration schema."""
    default_template_engine: Literal["jinja2"] = Field("jinja2")
    include_comments: bool = Field(True)
    include_examples: bool = Field(True)
    generate_readme: bool = Field(True)
    generate_variables_file: bool = Field(True)
    generate_outputs_file: bool = Field(True)


class CLIConfig(BaseModel):
    """CLI configuration schema."""
    show_progress: bool = Field(True)
    colored_output: bool = Field(True)
    interactive_mode: bool = Field(True)
    confirm_actions: bool = Field(True)


class CloudCraverConfig(BaseModel):
    """Main configuration schema for Cloud Craver application."""
    app: AppConfig = Field(default_factory=AppConfig)
    cloud: CloudConfig = Field(default_factory=CloudConfig)
    user: UserConfig = Field(default_factory=UserConfig)
    terraform: TerraformConfig = Field(default_factory=TerraformConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields
        validate_assignment = True  # Validate on assignment
        use_enum_values = True  # Use enum values instead of enum objects


def validate_config(config_dict: Dict) -> CloudCraverConfig:
    """
    Validate configuration dictionary against schema.
    
    Args:
        config_dict: Configuration dictionary to validate
        
    Returns:
        Validated configuration object
        
    Raises:
        ValidationError: If configuration is invalid
    """
    return CloudCraverConfig(**config_dict)


def get_config_schema() -> Dict:
    """
    Get the JSON schema for the configuration.
    
    Returns:
        JSON schema dictionary
    """
    return CloudCraverConfig.schema()


# Export validation functions
__all__ = [
    'CloudCraverConfig',
    'validate_config', 
    'get_config_schema',
    'AppConfig',
    'CloudConfig',
    'UserConfig',
    'TerraformConfig',
    'ValidationConfig',
    'PathsConfig',
    'GenerationConfig',
    'CLIConfig'
] 