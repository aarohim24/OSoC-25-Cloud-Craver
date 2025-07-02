"""
Example AWS S3 Template Plugin

This plugin demonstrates how to create a template plugin that generates
AWS CloudFormation templates for S3 buckets with various configurations.
"""

import json
import logging
from typing import Dict, List, Type, Any

from ..core import TemplatePlugin, PluginManifest, PluginMetadata, PluginType
from ...templates.base import BaseTemplate, TemplateMetadata

logger = logging.getLogger(__name__)


class S3BucketTemplate(BaseTemplate):
    """
    AWS S3 Bucket CloudFormation template implementation.
    
    This template can generate S3 buckets with:
    - Versioning configuration
    - Encryption settings
    - Public access blocking
    - Lifecycle policies
    - Bucket policies
    """
    
    def __init__(self, name: str, metadata: TemplateMetadata, variables: Dict[str, Any] = None):
        super().__init__(name, metadata, variables)
        
        # Set default variables for S3 bucket
        self._variables.setdefault('bucket_name', f'{name}-bucket')
        self._variables.setdefault('versioning_enabled', True)
        self._variables.setdefault('encryption_enabled', True)
        self._variables.setdefault('public_access_blocked', True)
        self._variables.setdefault('deletion_protection', False)
    
    def generate(self) -> str:
        """
        Generate CloudFormation template for S3 bucket.
        
        Returns:
            CloudFormation template as JSON string
        """
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"S3 Bucket: {self.metadata.description}",
            "Parameters": self._generate_parameters(),
            "Resources": self._generate_resources(),
            "Outputs": self._generate_outputs()
        }
        
        self._output = json.dumps(template, indent=2)
        return self._output
    
    def _generate_parameters(self) -> Dict[str, Any]:
        """Generate CloudFormation parameters."""
        return {
            "BucketName": {
                "Type": "String",
                "Default": self._variables['bucket_name'],
                "Description": "Name of the S3 bucket"
            },
            "VersioningEnabled": {
                "Type": "String",
                "Default": "true" if self._variables['versioning_enabled'] else "false",
                "AllowedValues": ["true", "false"],
                "Description": "Enable versioning on the bucket"
            }
        }
    
    def _generate_resources(self) -> Dict[str, Any]:
        """Generate CloudFormation resources."""
        bucket_resource = {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": {"Ref": "BucketName"}
            }
        }
        
        # Add versioning configuration
        if self._variables['versioning_enabled']:
            bucket_resource["Properties"]["VersioningConfiguration"] = {
                "Status": "Enabled"
            }
        
        # Add encryption
        if self._variables['encryption_enabled']:
            bucket_resource["Properties"]["BucketEncryption"] = {
                "ServerSideEncryptionConfiguration": [{
                    "ServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }
        
        # Add public access block
        if self._variables['public_access_blocked']:
            bucket_resource["Properties"]["PublicAccessBlockConfiguration"] = {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        
        # Add deletion protection
        if self._variables['deletion_protection']:
            bucket_resource["DeletionPolicy"] = "Retain"
        
        return {
            "S3Bucket": bucket_resource
        }
    
    def _generate_outputs(self) -> Dict[str, Any]:
        """Generate CloudFormation outputs."""
        return {
            "BucketName": {
                "Description": "Name of the created S3 bucket",
                "Value": {"Ref": "S3Bucket"},
                "Export": {
                    "Name": {"Fn::Sub": "${AWS::StackName}-BucketName"}
                }
            },
            "BucketArn": {
                "Description": "ARN of the created S3 bucket",
                "Value": {"Fn::GetAtt": ["S3Bucket", "Arn"]},
                "Export": {
                    "Name": {"Fn::Sub": "${AWS::StackName}-BucketArn"}
                }
            }
        }
    
    def validate(self) -> bool:
        """
        Validate the S3 bucket template.
        
        Performs basic validation of template structure and parameters.
        """
        try:
            # Check required variables
            required_vars = ['bucket_name']
            for var in required_vars:
                if var not in self._variables:
                    logger.error(f"Required variable missing: {var}")
                    return False
            
            # Validate bucket name format
            bucket_name = self._variables['bucket_name']
            if not self._is_valid_bucket_name(bucket_name):
                logger.error(f"Invalid bucket name: {bucket_name}")
                return False
            
            # Generate template to check for structural issues
            template_content = self.generate()
            if not template_content:
                logger.error("Failed to generate template content")
                return False
            
            # Parse JSON to validate structure
            try:
                json.loads(template_content)
            except json.JSONDecodeError as e:
                logger.error(f"Generated template is not valid JSON: {e}")
                return False
            
            logger.info(f"S3 bucket template validation passed for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            return False
    
    def _is_valid_bucket_name(self, name: str) -> bool:
        """
        Validate S3 bucket name according to AWS rules.
        
        AWS S3 bucket naming rules:
        - Must be 3-63 characters long
        - Can contain lowercase letters, numbers, and hyphens
        - Must start and end with lowercase letter or number
        - Cannot contain consecutive periods
        """
        import re
        
        if not (3 <= len(name) <= 63):
            return False
        
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name):
            return False
        
        if '..' in name:
            return False
        
        return True
    
    def render(self) -> str:
        """
        Render the final template.
        
        For CloudFormation templates, rendering is the same as generation.
        """
        if not self._output:
            self.generate()
        
        return self._output


class AWSS3TemplatePlugin(TemplatePlugin):
    """
    Plugin that provides AWS S3 bucket templates.
    
    This plugin demonstrates how to:
    1. Extend the TemplatePlugin base class
    2. Provide a custom template implementation
    3. Define supported cloud providers
    4. Handle plugin lifecycle events
    """
    
    def __init__(self, manifest: PluginManifest, config: Dict[str, Any] = None):
        """
        Initialize the AWS S3 template plugin.
        
        Args:
            manifest: Plugin manifest containing metadata
            config: Plugin configuration dictionary
        """
        super().__init__(manifest, config)
        
        # Plugin-specific configuration
        self.default_region = config.get('default_region', 'us-east-1') if config else 'us-east-1'
        self.enable_logging = config.get('enable_logging', True) if config else True
        
        logger.info(f"AWS S3 Template Plugin initialized with region: {self.default_region}")
    
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        This method is called during plugin loading to set up
        any necessary resources or connections.
        """
        try:
            logger.info("Initializing AWS S3 Template Plugin")
            
            # Register hook for template creation
            self.register_hook('template_create', self._on_template_create)
            
            # Register hook for validation
            self.register_hook('template_validate', self._on_template_validate)
            
            logger.info("AWS S3 Template Plugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 Template Plugin: {e}")
            return False
    
    async def activate(self) -> bool:
        """
        Activate the plugin.
        
        This method is called to make the plugin active and ready for use.
        """
        try:
            logger.info("Activating AWS S3 Template Plugin")
            
            # Perform any activation-specific setup
            if self.enable_logging:
                logger.info("AWS S3 template logging enabled")
            
            logger.info("AWS S3 Template Plugin activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate AWS S3 Template Plugin: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """
        Deactivate the plugin.
        
        This method is called to temporarily disable the plugin.
        """
        try:
            logger.info("Deactivating AWS S3 Template Plugin")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate AWS S3 Template Plugin: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Clean up plugin resources.
        
        This method is called when the plugin is being unloaded.
        """
        try:
            logger.info("Cleaning up AWS S3 Template Plugin")
            
            # Clean up any resources, connections, etc.
            # For this simple plugin, there's nothing to clean up
            
            logger.info("AWS S3 Template Plugin cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup AWS S3 Template Plugin: {e}")
            return False
    
    def get_template_class(self) -> Type[BaseTemplate]:
        """
        Return the template class this plugin provides.
        
        Returns:
            S3BucketTemplate class
        """
        return S3BucketTemplate
    
    def get_supported_providers(self) -> List[str]:
        """
        Return list of supported cloud providers.
        
        Returns:
            List containing 'aws' as this plugin supports AWS
        """
        return ['aws']
    
    def create_template(self, name: str, **kwargs) -> S3BucketTemplate:
        """
        Factory method to create S3 bucket templates.
        
        Args:
            name: Template name
            **kwargs: Additional template variables
            
        Returns:
            Configured S3BucketTemplate instance
        """
        metadata = TemplateMetadata(
            version="1.0.0",
            description=f"AWS S3 bucket template: {name}",
            tags=["aws", "s3", "storage"]
        )
        
        # Merge default config with provided kwargs
        variables = {
            'default_region': self.default_region,
            **kwargs
        }
        
        return S3BucketTemplate(name, metadata, variables)
    
    async def _on_template_create(self, template_name: str, template_type: str):
        """Hook called when a template is created."""
        if template_type == 's3':
            logger.info(f"Creating S3 template: {template_name}")
    
    async def _on_template_validate(self, template):
        """Hook called during template validation."""
        if isinstance(template, S3BucketTemplate):
            logger.info(f"Validating S3 template: {template.name}")
            
            # Additional plugin-specific validation
            bucket_name = template.get_variable('bucket_name')
            if bucket_name and not bucket_name.startswith(self.config.get('bucket_prefix', '')):
                logger.warning(f"S3 bucket {bucket_name} does not follow naming convention")


# Plugin manifest for this example
PLUGIN_MANIFEST = PluginManifest(
    metadata=PluginMetadata(
        name="aws-s3-template",
        version="1.0.0",
        description="AWS S3 bucket template plugin with advanced configuration options",
        author="CloudCraver Team",
        email="plugins@cloudcraver.io",
        license="MIT",
        keywords=["aws", "s3", "storage", "template"],
        categories=["templates", "aws"],
        dependencies=[],
        min_core_version="1.0.0"
    ),
    plugin_type=PluginType.TEMPLATE,
    main_class="AWSS3TemplatePlugin",
    module_path="aws_s3_template",
    hooks=["template_create", "template_validate"],
    provides=["s3_template"],
    permissions=["file_read", "temp_write"]
) 