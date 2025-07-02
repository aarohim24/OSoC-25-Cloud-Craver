"""
Example plugins demonstrating the plugin system capabilities.

This module contains example plugins that show how to:
- Create template plugins for different cloud providers
- Build provider plugins with authentication
- Implement validator plugins for custom rules
- Add extension plugins for new functionality
"""

from .aws_s3_template import AWSS3TemplatePlugin
from .custom_validator import CustomValidatorPlugin
from .azure_provider import AzureProviderPlugin

__all__ = [
    'AWSS3TemplatePlugin',
    'CustomValidatorPlugin', 
    'AzureProviderPlugin'
] 