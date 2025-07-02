"""
Example Custom Validator Plugin

This demonstrates how to create validator plugins that can analyze
templates and configurations for custom business rules and best practices.
"""

import re
import json
import logging
from typing import Dict, Any, List

from ..core import ValidatorPlugin, PluginManifest, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class CustomValidatorPlugin(ValidatorPlugin):
    """
    Custom validator plugin that enforces organizational policies.
    
    This plugin demonstrates how to:
    1. Create custom validation rules
    2. Analyze template content
    3. Generate validation reports
    4. Integrate with the plugin system
    """
    
    def __init__(self, manifest: PluginManifest, config: Dict[str, Any] = None):
        super().__init__(manifest, config)
        
        # Load validation rules from config
        self.rules = config.get('rules', {}) if config else {}
        self.strict_mode = config.get('strict_mode', False) if config else False
        
        # Default rules
        self.default_rules = {
            'naming_convention': {
                'enabled': True,
                'pattern': r'^[a-z][a-z0-9-]*[a-z0-9]$',
                'message': 'Resource names must be lowercase with hyphens'
            },
            'required_tags': {
                'enabled': True,
                'tags': ['Environment', 'Project', 'Owner'],
                'message': 'All resources must have required tags'
            },
            'encryption_required': {
                'enabled': True,
                'message': 'All storage resources must have encryption enabled'
            }
        }
        
        # Merge default rules with config
        for rule_name, rule_config in self.default_rules.items():
            if rule_name not in self.rules:
                self.rules[rule_name] = rule_config
    
    async def initialize(self) -> bool:
        """Initialize the validator plugin."""
        try:
            logger.info("Initializing Custom Validator Plugin")
            
            # Register validation hooks
            self.register_hook('validate_template', self._validate_template_hook)
            self.register_hook('validate_resource', self._validate_resource_hook)
            
            logger.info(f"Custom Validator Plugin initialized with {len(self.rules)} rules")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Custom Validator Plugin: {e}")
            return False
    
    async def activate(self) -> bool:
        """Activate the validator plugin."""
        logger.info("Custom Validator Plugin activated")
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate the validator plugin."""
        logger.info("Custom Validator Plugin deactivated")
        return True
    
    async def cleanup(self) -> bool:
        """Clean up validator resources."""
        logger.info("Custom Validator Plugin cleanup completed")
        return True
    
    def validate(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main validation method that analyzes content against custom rules.
        
        Args:
            content: Template or configuration content to validate
            context: Validation context with metadata
            
        Returns:
            Validation results dictionary
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': [],
            'summary': {}
        }
        
        try:
            # Determine content type
            content_type = context.get('type', 'unknown')
            
            if content_type == 'cloudformation':
                results = self._validate_cloudformation(content, context)
            elif content_type == 'terraform':
                results = self._validate_terraform(content, context)
            elif content_type == 'azure_arm':
                results = self._validate_azure_arm(content, context)
            else:
                # Generic validation
                results = self._validate_generic(content, context)
            
            # Set overall validity
            results['valid'] = len(results['errors']) == 0 and (
                not self.strict_mode or len(results['warnings']) == 0
            )
            
            # Generate summary
            results['summary'] = {
                'total_rules_checked': len(self.rules),
                'errors_found': len(results['errors']),
                'warnings_found': len(results['warnings']),
                'validation_passed': results['valid']
            }
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            results['valid'] = False
            results['errors'].append(f"Validation error: {str(e)}")
        
        return results
    
    def _validate_cloudformation(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CloudFormation templates."""
        results = {'errors': [], 'warnings': [], 'info': []}
        
        try:
            # Parse JSON/YAML content
            if content.strip().startswith('{'):
                template = json.loads(content)
            else:
                import yaml
                template = yaml.safe_load(content)
            
            # Validate template structure
            if 'Resources' not in template:
                results['errors'].append("CloudFormation template missing Resources section")
                return results
            
            # Validate each resource
            for resource_name, resource_config in template['Resources'].items():
                resource_results = self._validate_resource(resource_name, resource_config, 'aws')
                results['errors'].extend(resource_results['errors'])
                results['warnings'].extend(resource_results['warnings'])
                results['info'].extend(resource_results['info'])
            
        except Exception as e:
            results['errors'].append(f"Failed to parse CloudFormation template: {e}")
        
        return results
    
    def _validate_terraform(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Terraform configurations."""
        results = {'errors': [], 'warnings': [], 'info': []}
        
        # Simple regex-based parsing for demonstration
        # In production, would use proper HCL parser
        
        # Check for required provider configuration
        if 'provider ' not in content:
            results['warnings'].append("No provider configuration found")
        
        # Check for resource definitions
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*{'
        resources = re.findall(resource_pattern, content)
        
        if not resources:
            results['warnings'].append("No resources defined in Terraform configuration")
        
        # Validate each resource
        for resource_type, resource_name in resources:
            resource_results = self._validate_terraform_resource(resource_name, resource_type, content)
            results['errors'].extend(resource_results['errors'])
            results['warnings'].extend(resource_results['warnings'])
        
        return results
    
    def _validate_azure_arm(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Azure ARM templates."""
        results = {'errors': [], 'warnings': [], 'info': []}
        
        try:
            template = json.loads(content)
            
            # Check required ARM template fields
            required_fields = ['$schema', 'contentVersion', 'resources']
            for field in required_fields:
                if field not in template:
                    results['errors'].append(f"ARM template missing required field: {field}")
            
            # Validate resources
            if 'resources' in template:
                for resource in template['resources']:
                    if 'type' in resource and 'name' in resource:
                        resource_results = self._validate_resource(
                            resource['name'], 
                            resource, 
                            'azure'
                        )
                        results['errors'].extend(resource_results['errors'])
                        results['warnings'].extend(resource_results['warnings'])
        
        except Exception as e:
            results['errors'].append(f"Failed to parse ARM template: {e}")
        
        return results
    
    def _validate_generic(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic validation for unknown content types."""
        results = {'errors': [], 'warnings': [], 'info': []}
        
        # Basic content checks
        if len(content.strip()) == 0:
            results['errors'].append("Content is empty")
            return results
        
        # Check for potential security issues
        security_patterns = [
            (r'password\s*=\s*["\'][^"\']*["\']', 'warning', 'Hardcoded password detected'),
            (r'api[_-]?key\s*=\s*["\'][^"\']*["\']', 'warning', 'Hardcoded API key detected'),
            (r'secret\s*=\s*["\'][^"\']*["\']', 'warning', 'Hardcoded secret detected')
        ]
        
        for pattern, severity, message in security_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                if severity == 'error':
                    results['errors'].append(message)
                else:
                    results['warnings'].append(message)
        
        return results
    
    def _validate_resource(self, resource_name: str, resource_config: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Validate a single resource against custom rules."""
        results = {'errors': [], 'warnings': [], 'info': []}
        
        # Check naming convention
        if self.rules.get('naming_convention', {}).get('enabled', False):
            pattern = self.rules['naming_convention']['pattern']
            if not re.match(pattern, resource_name):
                message = self.rules['naming_convention']['message']
                results['errors'].append(f"Resource '{resource_name}': {message}")
        
        # Check required tags
        if self.rules.get('required_tags', {}).get('enabled', False):
            required_tags = self.rules['required_tags']['tags']
            resource_tags = self._extract_tags(resource_config, provider)
            
            missing_tags = []
            for tag in required_tags:
                if tag not in resource_tags:
                    missing_tags.append(tag)
            
            if missing_tags:
                message = self.rules['required_tags']['message']
                results['warnings'].append(
                    f"Resource '{resource_name}': {message}. Missing: {', '.join(missing_tags)}"
                )
        
        # Check encryption requirement
        if self.rules.get('encryption_required', {}).get('enabled', False):
            if self._is_storage_resource(resource_config, provider):
                if not self._has_encryption_enabled(resource_config, provider):
                    message = self.rules['encryption_required']['message']
                    results['errors'].append(f"Resource '{resource_name}': {message}")
        
        return results
    
    def _validate_terraform_resource(self, resource_name: str, resource_type: str, content: str) -> Dict[str, Any]:
        """Validate Terraform resource specifically."""
        results = {'errors': [], 'warnings': [], 'info': []}
        
        # Extract resource block
        resource_pattern = rf'resource\s+"{re.escape(resource_type)}"\s+"{re.escape(resource_name)}"\s*{{([^}}]*)}}'
        match = re.search(resource_pattern, content, re.DOTALL)
        
        if not match:
            results['errors'].append(f"Could not find resource block for {resource_type}.{resource_name}")
            return results
        
        resource_block = match.group(1)
        
        # Check for required attributes based on resource type
        if 'aws_s3_bucket' in resource_type:
            if 'server_side_encryption_configuration' not in resource_block:
                results['warnings'].append(f"S3 bucket '{resource_name}' should have encryption enabled")
        
        elif 'aws_instance' in resource_type:
            if 'associate_public_ip_address = true' in resource_block:
                results['warnings'].append(f"EC2 instance '{resource_name}' has public IP - security risk")
        
        return results
    
    def _extract_tags(self, resource_config: Dict[str, Any], provider: str) -> Dict[str, str]:
        """Extract tags from resource configuration."""
        tags = {}
        
        if provider == 'aws':
            # CloudFormation format
            if 'Properties' in resource_config and 'Tags' in resource_config['Properties']:
                for tag in resource_config['Properties']['Tags']:
                    if isinstance(tag, dict) and 'Key' in tag and 'Value' in tag:
                        tags[tag['Key']] = tag['Value']
        
        elif provider == 'azure':
            # ARM template format
            if 'tags' in resource_config:
                tags = resource_config['tags']
        
        return tags
    
    def _is_storage_resource(self, resource_config: Dict[str, Any], provider: str) -> bool:
        """Check if resource is a storage resource that requires encryption."""
        if provider == 'aws':
            resource_type = resource_config.get('Type', '')
            storage_types = ['AWS::S3::Bucket', 'AWS::RDS::DBInstance', 'AWS::EBS::Volume']
            return any(storage_type in resource_type for storage_type in storage_types)
        
        elif provider == 'azure':
            resource_type = resource_config.get('type', '')
            storage_types = ['Microsoft.Storage/storageAccounts', 'Microsoft.Sql/servers']
            return any(storage_type in resource_type for storage_type in storage_types)
        
        return False
    
    def _has_encryption_enabled(self, resource_config: Dict[str, Any], provider: str) -> bool:
        """Check if resource has encryption enabled."""
        if provider == 'aws':
            properties = resource_config.get('Properties', {})
            
            # Check S3 bucket encryption
            if 'BucketEncryption' in properties:
                return True
            
            # Check RDS encryption
            if 'StorageEncrypted' in properties:
                return properties['StorageEncrypted']
        
        elif provider == 'azure':
            properties = resource_config.get('properties', {})
            
            # Check storage account encryption
            if 'encryption' in properties:
                return properties['encryption'].get('services', {}).get('blob', {}).get('enabled', False)
        
        return False
    
    async def _validate_template_hook(self, template):
        """Hook for template validation events."""
        logger.info(f"Validating template with custom rules: {template.name if hasattr(template, 'name') else 'unknown'}")
    
    async def _validate_resource_hook(self, resource_name, resource_config):
        """Hook for resource validation events."""
        logger.debug(f"Validating resource: {resource_name}")


# Plugin manifest
PLUGIN_MANIFEST = PluginManifest(
    metadata=PluginMetadata(
        name="custom-validator",
        version="1.0.0", 
        description="Custom validator plugin for organizational policies and best practices",
        author="CloudCraver Team",
        email="plugins@cloudcraver.io",
        license="MIT",
        keywords=["validator", "policies", "compliance", "security"],
        categories=["validator", "security"],
        dependencies=[],
        min_core_version="1.0.0"
    ),
    plugin_type=PluginType.VALIDATOR,
    main_class="CustomValidatorPlugin",
    module_path="custom_validator",
    hooks=["validate_template", "validate_resource"],
    provides=["custom_validation"],
    permissions=["file_read"]
)