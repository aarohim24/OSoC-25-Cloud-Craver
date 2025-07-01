"""
CLI configuration module for handling command-line arguments.

This module provides functionality for parsing CLI arguments and
integrating them with the Dynaconf configuration system.
"""

import argparse
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

from . import config


class CLIConfigManager:
    """Manages CLI arguments and their integration with configuration."""
    
    def __init__(self):
        """Initialize CLI config manager."""
        self.parser = self._create_parser()
        self.args = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all configuration options."""
        parser = argparse.ArgumentParser(
            prog="cloudcraver",
            description="Cloud Craver - Infrastructure Template Generator and Validator",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  cloudcraver generate --provider aws --region us-east-1
  cloudcraver validate --config-file custom.toml
  cloudcraver --debug --log-level DEBUG validate
            """
        )
        
        # Global configuration options
        parser.add_argument(
            "--config-file", 
            type=str,
            help="Path to custom configuration file"
        )
        
        parser.add_argument(
            "--config-dir",
            type=str, 
            help="Path to configuration directory"
        )
        
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode"
        )
        
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Set logging level"
        )
        
        parser.add_argument(
            "--output-format",
            choices=["rich", "json", "text"],
            help="Set output format"
        )
        
        # Cloud provider options
        parser.add_argument(
            "--provider",
            choices=["aws", "azure", "gcp"],
            help="Cloud provider to use"
        )
        
        parser.add_argument(
            "--region",
            type=str,
            help="Cloud provider region"
        )
        
        parser.add_argument(
            "--profile",
            type=str,
            help="Cloud provider profile/subscription"
        )
        
        # User preference options
        parser.add_argument(
            "--auto-save",
            action="store_true",
            help="Enable auto-save for user preferences"
        )
        
        parser.add_argument(
            "--no-auto-save",
            action="store_true", 
            help="Disable auto-save for user preferences"
        )
        
        parser.add_argument(
            "--theme",
            choices=["auto", "light", "dark"],
            help="UI theme"
        )
        
        parser.add_argument(
            "--editor",
            type=str,
            help="Default editor for configuration files"
        )
        
        # Validation options
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Enable strict validation mode"
        )
        
        parser.add_argument(
            "--fail-on-warnings",
            action="store_true",
            help="Fail validation on warnings"
        )
        
        parser.add_argument(
            "--enable-security-scan",
            action="store_true",
            help="Enable security scanning"
        )
        
        parser.add_argument(
            "--disable-security-scan",
            action="store_true",
            help="Disable security scanning"
        )
        
        # Terraform options
        parser.add_argument(
            "--terraform-version",
            type=str,
            help="Terraform version to use"
        )
        
        parser.add_argument(
            "--auto-init",
            action="store_true",
            help="Enable Terraform auto-init"
        )
        
        parser.add_argument(
            "--no-auto-init",
            action="store_true",
            help="Disable Terraform auto-init"
        )
        
        parser.add_argument(
            "--state-backend",
            choices=["local", "s3", "azurerm", "gcs"],
            help="Terraform state backend"
        )
        
        # Path options
        parser.add_argument(
            "--output-dir",
            type=str,
            help="Output directory for generated files"
        )
        
        parser.add_argument(
            "--templates-dir",
            type=str,
            help="Templates directory"
        )
        
        parser.add_argument(
            "--cache-dir",
            type=str,
            help="Cache directory"
        )
        
        # CLI options
        parser.add_argument(
            "--no-progress",
            action="store_true",
            help="Disable progress bars"
        )
        
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable colored output"
        )
        
        parser.add_argument(
            "--batch",
            action="store_true",
            help="Run in non-interactive batch mode"
        )
        
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Automatically answer yes to prompts"
        )
        
        # Environment selection
        parser.add_argument(
            "--env",
            type=str,
            help="Environment to use (development, production, etc.)"
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command-line arguments.
        
        Args:
            args: Optional list of arguments to parse (defaults to sys.argv)
            
        Returns:
            Parsed arguments namespace
        """
        self.args = self.parser.parse_args(args)
        return self.args
    
    def get_config_overrides(self) -> Dict[str, Any]:
        """
        Get configuration overrides from CLI arguments.
        
        Returns:
            Dictionary of configuration overrides
        """
        if self.args is None:
            return {}
        
        overrides = {}
        
        # App configuration overrides
        if self.args.debug:
            overrides["app.debug"] = True
        if self.args.log_level:
            overrides["app.log_level"] = self.args.log_level
        if self.args.output_format:
            overrides["app.output_format"] = self.args.output_format
        
        # Cloud configuration overrides
        if self.args.provider:
            overrides["cloud.default_provider"] = self.args.provider
        if self.args.region:
            overrides["cloud.default_regions." + (self.args.provider or "aws")] = self.args.region
        if self.args.profile:
            provider = self.args.provider or "aws"
            if provider == "aws":
                overrides["cloud.aws.profile"] = self.args.profile
            elif provider == "azure":
                overrides["cloud.azure.subscription_id"] = self.args.profile
            elif provider == "gcp":
                overrides["cloud.gcp.project_id"] = self.args.profile
        
        # User preferences overrides
        if self.args.auto_save:
            overrides["user.preferences.auto_save"] = True
        if self.args.no_auto_save:
            overrides["user.preferences.auto_save"] = False
        if self.args.theme:
            overrides["user.preferences.theme"] = self.args.theme
        if self.args.editor:
            overrides["user.preferences.editor"] = self.args.editor
        
        # Validation overrides
        if self.args.strict:
            overrides["validation.strict_mode"] = True
        if self.args.fail_on_warnings:
            overrides["validation.fail_on_warnings"] = True
        if self.args.enable_security_scan:
            overrides["terraform.validation.enable_security_scan"] = True
        if self.args.disable_security_scan:
            overrides["terraform.validation.enable_security_scan"] = False
        
        # Terraform overrides
        if self.args.terraform_version:
            overrides["terraform.version"] = self.args.terraform_version
        if self.args.auto_init:
            overrides["terraform.auto_init"] = True
        if self.args.no_auto_init:
            overrides["terraform.auto_init"] = False
        if self.args.state_backend:
            overrides["terraform.state_backend"] = self.args.state_backend
        
        # Path overrides
        if self.args.output_dir:
            overrides["paths.output_dir"] = self.args.output_dir
        if self.args.templates_dir:
            overrides["paths.templates_dir"] = self.args.templates_dir
        if self.args.cache_dir:
            overrides["paths.cache_dir"] = self.args.cache_dir
        
        # CLI overrides
        if self.args.no_progress:
            overrides["cli.show_progress"] = False
        if self.args.no_color:
            overrides["cli.colored_output"] = False
        if self.args.batch:
            overrides["cli.interactive_mode"] = False
        if self.args.yes:
            overrides["cli.confirm_actions"] = False
        
        return overrides
    
    def apply_cli_overrides(self):
        """Apply CLI argument overrides to the configuration."""
        overrides = self.get_config_overrides()
        
        # Apply environment if specified
        if self.args and self.args.env:
            config.settings.setenv(self.args.env)
        
        # Apply each override
        for key, value in overrides.items():
            config.settings.set(key, value)
    
    def load_custom_config_file(self):
        """Load custom configuration file if specified."""
        if self.args and self.args.config_file:
            config_path = Path(self.args.config_file)
            if config_path.exists():
                # Add the custom config file to settings
                config.settings.load_file(path=str(config_path))
            else:
                print(f"Warning: Configuration file not found: {config_path}")
        
        if self.args and self.args.config_dir:
            config_dir = Path(self.args.config_dir)
            if config_dir.exists():
                # Update the search paths
                config.settings.configure(root_path=str(config_dir))
            else:
                print(f"Warning: Configuration directory not found: {config_dir}")
    
    def get_help(self) -> str:
        """Get help text for CLI configuration."""
        return self.parser.format_help()
    
    def validate_args(self) -> List[str]:
        """
        Validate CLI arguments for conflicts and requirements.
        
        Returns:
            List of validation errors (empty if valid)
        """
        if self.args is None:
            return []
        
        errors = []
        
        # Check for conflicting auto-save options
        if self.args.auto_save and self.args.no_auto_save:
            errors.append("Cannot specify both --auto-save and --no-auto-save")
        
        # Check for conflicting auto-init options
        if self.args.auto_init and self.args.no_auto_init:
            errors.append("Cannot specify both --auto-init and --no-auto-init")
        
        # Check for conflicting security scan options
        if self.args.enable_security_scan and self.args.disable_security_scan:
            errors.append("Cannot specify both --enable-security-scan and --disable-security-scan")
        
        # Validate paths exist if specified
        if self.args.config_file and not Path(self.args.config_file).exists():
            errors.append(f"Configuration file does not exist: {self.args.config_file}")
        
        if self.args.config_dir and not Path(self.args.config_dir).is_dir():
            errors.append(f"Configuration directory does not exist: {self.args.config_dir}")
        
        return errors


# Global CLI manager instance
_cli_manager = None


def get_cli_manager() -> CLIConfigManager:
    """Get the global CLI manager instance."""
    global _cli_manager
    if _cli_manager is None:
        _cli_manager = CLIConfigManager()
    return _cli_manager


def parse_cli_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments and apply them to configuration."""
    manager = get_cli_manager()
    parsed_args = manager.parse_args(args)
    
    # Validate arguments
    errors = manager.validate_args()
    if errors:
        for error in errors:
            print(f"Error: {error}")
        sys.exit(1)
    
    # Load custom config files first
    manager.load_custom_config_file()
    
    # Apply CLI overrides
    manager.apply_cli_overrides()
    
    return parsed_args


def get_cli_overrides() -> Dict[str, Any]:
    """Get CLI configuration overrides."""
    return get_cli_manager().get_config_overrides()


# Export public functions
__all__ = [
    'CLIConfigManager',
    'get_cli_manager',
    'parse_cli_args',
    'get_cli_overrides'
] 