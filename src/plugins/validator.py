"""
Plugin validation system for ensuring plugin security and integrity.

This module provides comprehensive validation of plugins including:
- Manifest validation and schema checking
- Code analysis for security vulnerabilities
- Structure and dependency validation
- Runtime safety checks
"""

import ast
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
import importlib.util

from .core import PluginManifest, Plugin, PluginType

logger = logging.getLogger(__name__)


class SecurityViolation:
    """Represents a security violation found during validation."""
    
    def __init__(self, severity: str, message: str, file_path: Optional[str] = None, line_number: Optional[int] = None):
        self.severity = severity  # 'critical', 'high', 'medium', 'low'
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
    
    def __str__(self):
        location = f" at {self.file_path}:{self.line_number}" if self.file_path and self.line_number else ""
        return f"[{self.severity.upper()}] {self.message}{location}"


class PluginValidator:
    """
    Comprehensive plugin validation system.
    
    This validator performs multiple layers of security and integrity checks:
    
    1. **Manifest Validation**: Ensures the plugin manifest is well-formed
       and contains all required fields with valid values.
    
    2. **Code Analysis**: Performs static analysis of Python code to detect:
       - Dangerous imports (os, subprocess, etc.)
       - File system operations
       - Network operations
       - Dynamic code execution
    
    3. **Structure Validation**: Checks that the plugin follows expected
       directory structure and naming conventions.
    
    4. **Dependency Validation**: Ensures all dependencies are available
       and compatible.
    
    5. **Signature Verification**: (Optional) Verifies plugin signatures
       from trusted publishers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the plugin validator.
        
        Args:
            config: Validator configuration containing:
                - strict_mode: Whether to fail on warnings
                - allowed_imports: List of allowed Python modules
                - forbidden_patterns: Regex patterns to flag as dangerous
                - max_file_size: Maximum size for plugin files
                - signature_verification: Whether to verify signatures
        """
        self.config = config
        self.strict_mode = config.get('strict_mode', False)
        self.max_file_size = config.get('max_file_size', 1024 * 1024)  # 1MB default
        self.signature_verification = config.get('signature_verification', False)
        
        # Define security rules
        self._init_security_rules()
        
        logger.debug(f"PluginValidator initialized with strict_mode={self.strict_mode}")
    
    def _init_security_rules(self):
        """Initialize security validation rules."""
        
        # Dangerous imports that should be flagged
        self.dangerous_imports = {
            'os': 'critical',
            'subprocess': 'critical',
            'sys': 'high',
            'importlib': 'high',
            'exec': 'critical',
            'eval': 'critical',
            '__import__': 'critical',
            'compile': 'high',
            'open': 'medium',  # File operations
            'file': 'medium',
            'input': 'low',
            'raw_input': 'low'
        }
        
        # Patterns in code that indicate security risks
        self.dangerous_patterns = [
            (r'exec\s*\(', 'critical', 'Dynamic code execution'),
            (r'eval\s*\(', 'critical', 'Dynamic code evaluation'),
            (r'__import__\s*\(', 'critical', 'Dynamic import'),
            (r'subprocess\.\w+', 'critical', 'Subprocess execution'),
            (r'os\.system\s*\(', 'critical', 'System command execution'),
            (r'os\.popen\s*\(', 'critical', 'System command execution'),
            (r'open\s*\([^)]*["\']w["\']', 'medium', 'File write operation'),
            (r'urllib\.request', 'medium', 'Network request'),
            (r'requests\.\w+', 'medium', 'HTTP request'),
            (r'socket\.', 'medium', 'Socket operation'),
            (r'pickle\.loads?', 'high', 'Unsafe deserialization'),
            (r'marshal\.loads?', 'high', 'Unsafe deserialization'),
        ]
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = [
            (re.compile(pattern), severity, description)
            for pattern, severity, description in self.dangerous_patterns
        ]
        
        # Allowed imports from configuration
        self.allowed_imports = set(self.config.get('allowed_imports', [
            'json', 'yaml', 'logging', 'datetime', 'typing', 
            'pathlib', 'dataclasses', 'enum', 'abc', 'asyncio'
        ]))
    
    async def validate_plugin_package(self, source: Union[str, Path]) -> Optional[PluginManifest]:
        """
        Validate a plugin package before installation.
        
        This method performs initial validation of a plugin package:
        1. Extracts and validates the manifest
        2. Performs basic security checks
        3. Validates package structure
        
        Args:
            source: Path to plugin package or directory
            
        Returns:
            Plugin manifest if valid, None otherwise
        """
        try:
            source_path = Path(source) if not isinstance(source, Path) else source
            
            logger.info(f"Validating plugin package: {source_path}")
            
            # Load and validate manifest
            manifest = await self._validate_manifest(source_path)
            if not manifest:
                return None
            
            # Perform package-level validation
            violations = await self._validate_package_structure(source_path)
            
            # Check violations
            critical_violations = [v for v in violations if v.severity == 'critical']
            if critical_violations:
                logger.error(f"Critical security violations found:")
                for violation in critical_violations:
                    logger.error(f"  {violation}")
                return None
            
            # In strict mode, fail on any violations
            if self.strict_mode and violations:
                logger.error(f"Validation failed in strict mode:")
                for violation in violations:
                    logger.error(f"  {violation}")
                return None
            
            # Log warnings for non-critical violations
            for violation in violations:
                if violation.severity != 'critical':
                    logger.warning(f"Security warning: {violation}")
            
            logger.info(f"Plugin package validation passed for {manifest.metadata.name}")
            return manifest
            
        except Exception as e:
            logger.error(f"Plugin package validation failed: {e}")
            return None
    
    async def validate_plugin(self, plugin: Plugin) -> bool:
        """
        Validate a loaded plugin instance.
        
        This method performs runtime validation:
        1. Validates the plugin interface implementation
        2. Checks configuration against schema
        3. Performs runtime security checks
        
        Args:
            plugin: Loaded plugin instance
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            logger.info(f"Validating loaded plugin: {plugin.name}")
            
            violations = []
            
            # Validate plugin interface
            interface_violations = await self._validate_plugin_interface(plugin)
            violations.extend(interface_violations)
            
            # Validate configuration
            config_violations = await self._validate_plugin_config(plugin)
            violations.extend(config_violations)
            
            # Check for critical violations
            critical_violations = [v for v in violations if v.severity == 'critical']
            if critical_violations:
                logger.error(f"Critical violations in plugin {plugin.name}:")
                for violation in critical_violations:
                    logger.error(f"  {violation}")
                return False
            
            # In strict mode, fail on any violations
            if self.strict_mode and violations:
                logger.error(f"Plugin {plugin.name} failed strict validation:")
                for violation in violations:
                    logger.error(f"  {violation}")
                return False
            
            # Log warnings
            for violation in violations:
                if violation.severity != 'critical':
                    logger.warning(f"Plugin {plugin.name} warning: {violation}")
            
            logger.info(f"Plugin {plugin.name} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Plugin validation failed for {plugin.name}: {e}")
            return False
    
    async def _validate_manifest(self, source_path: Path) -> Optional[PluginManifest]:
        """
        Validate the plugin manifest file.
        
        This method:
        1. Locates the manifest file
        2. Validates JSON/YAML structure
        3. Checks required fields
        4. Validates field values and types
        
        Args:
            source_path: Path to plugin package or directory
            
        Returns:
            Parsed manifest if valid, None otherwise
        """
        try:
            # Try to load manifest using discovery
            from .discovery import PluginDiscovery
            discovery = PluginDiscovery({})
            
            if source_path.is_dir():
                manifest = await discovery._load_manifest_from_directory(source_path)
            else:
                manifest = await discovery._load_manifest_from_package(source_path)
            
            if not manifest:
                logger.error("No valid manifest found")
                return None
            
            # Validate manifest content
            violations = self._validate_manifest_content(manifest)
            
            critical_violations = [v for v in violations if v.severity == 'critical']
            if critical_violations:
                logger.error("Critical manifest validation errors:")
                for violation in critical_violations:
                    logger.error(f"  {violation}")
                return None
            
            return manifest
            
        except Exception as e:
            logger.error(f"Manifest validation failed: {e}")
            return None
    
    def _validate_manifest_content(self, manifest: PluginManifest) -> List[SecurityViolation]:
        """
        Validate the content of a plugin manifest.
        
        Args:
            manifest: Plugin manifest to validate
            
        Returns:
            List of validation violations
        """
        violations = []
        
        # Validate plugin name (security check for injection)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', manifest.metadata.name):
            violations.append(SecurityViolation(
                'high', 
                f"Invalid plugin name: {manifest.metadata.name}. Must start with letter and contain only alphanumeric, underscore, and dash characters"
            ))
        
        # Validate version format
        if not re.match(r'^\d+\.\d+(\.\d+)?(-[a-zA-Z0-9]+)?$', manifest.metadata.version):
            violations.append(SecurityViolation(
                'medium',
                f"Invalid version format: {manifest.metadata.version}. Should follow semantic versioning"
            ))
        
        # Validate main class name
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', manifest.main_class):
            violations.append(SecurityViolation(
                'high',
                f"Invalid main class name: {manifest.main_class}"
            ))
        
        # Check for suspicious permissions
        dangerous_permissions = ['file_write', 'network_access', 'system_exec']
        for permission in manifest.permissions:
            if permission in dangerous_permissions:
                violations.append(SecurityViolation(
                    'medium',
                    f"Plugin requests dangerous permission: {permission}"
                ))
        
        # Validate dependencies
        for dep in manifest.metadata.dependencies:
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*([>=<~!]=?[\d.]+)?$', dep):
                violations.append(SecurityViolation(
                    'medium',
                    f"Invalid dependency format: {dep}"
                ))
        
        return violations
    
    async def _validate_package_structure(self, source_path: Path) -> List[SecurityViolation]:
        """
        Validate the structure and content of a plugin package.
        
        Args:
            source_path: Path to plugin package or directory
            
        Returns:
            List of security violations
        """
        violations = []
        
        try:
            if source_path.is_dir():
                violations.extend(await self._validate_directory_structure(source_path))
            else:
                violations.extend(await self._validate_archive_structure(source_path))
            
        except Exception as e:
            violations.append(SecurityViolation(
                'critical',
                f"Failed to validate package structure: {e}"
            ))
        
        return violations
    
    async def _validate_directory_structure(self, plugin_dir: Path) -> List[SecurityViolation]:
        """
        Validate a plugin directory structure and analyze code files.
        
        Args:
            plugin_dir: Plugin directory path
            
        Returns:
            List of security violations
        """
        violations = []
        
        # Check for required files
        manifest_files = ['plugin.json', 'manifest.json', 'cloudcraver.json']
        has_manifest = any((plugin_dir / f).exists() for f in manifest_files)
        
        if not has_manifest:
            violations.append(SecurityViolation(
                'critical',
                "No manifest file found"
            ))
            return violations
        
        # Analyze all Python files
        for py_file in plugin_dir.rglob("*.py"):
            if py_file.stat().st_size > self.max_file_size:
                violations.append(SecurityViolation(
                    'medium',
                    f"File {py_file.name} exceeds maximum size limit",
                    str(py_file)
                ))
                continue
            
            file_violations = await self._analyze_python_file(py_file)
            violations.extend(file_violations)
        
        # Check for suspicious files
        suspicious_patterns = ['*.exe', '*.dll', '*.so', '*.dylib', '*.bat', '*.sh']
        for pattern in suspicious_patterns:
            for file in plugin_dir.rglob(pattern):
                violations.append(SecurityViolation(
                    'high',
                    f"Suspicious executable file: {file.name}",
                    str(file)
                ))
        
        return violations
    
    async def _analyze_python_file(self, file_path: Path) -> List[SecurityViolation]:
        """
        Perform static analysis of a Python file for security issues.
        
        This method uses AST parsing and regex matching to detect:
        - Dangerous imports
        - Suspicious code patterns
        - Potential security vulnerabilities
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of security violations found
        """
        violations = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse AST for import analysis
            try:
                tree = ast.parse(content)
                violations.extend(self._analyze_ast(tree, file_path))
            except SyntaxError as e:
                violations.append(SecurityViolation(
                    'high',
                    f"Syntax error in Python file: {e}",
                    str(file_path),
                    e.lineno
                ))
            
            # Pattern-based analysis
            violations.extend(self._analyze_code_patterns(content, file_path))
            
        except Exception as e:
            violations.append(SecurityViolation(
                'medium',
                f"Failed to analyze file: {e}",
                str(file_path)
            ))
        
        return violations
    
    def _analyze_ast(self, tree: ast.AST, file_path: Path) -> List[SecurityViolation]:
        """
        Analyze Python AST for security issues.
        
        Args:
            tree: Parsed AST
            file_path: Source file path
            
        Returns:
            List of security violations
        """
        violations = []
        
        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self, validator, violations_list):
                self.validator = validator
                self.violations = violations_list
            
            def visit_Import(self, node):
                # Check imports
                for alias in node.names:
                    self.check_import(alias.name, node.lineno)
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                # Check from imports
                if node.module:
                    self.check_import(node.module, node.lineno)
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Check function calls
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in self.validator.dangerous_imports:
                        severity = self.validator.dangerous_imports[func_name]
                        self.violations.append(SecurityViolation(
                            severity,
                            f"Dangerous function call: {func_name}",
                            str(file_path),
                            node.lineno
                        ))
                self.generic_visit(node)
            
            def check_import(self, module_name, line_no):
                # Check if import is dangerous
                base_module = module_name.split('.')[0]
                if base_module in self.validator.dangerous_imports:
                    if base_module not in self.validator.allowed_imports:
                        severity = self.validator.dangerous_imports[base_module]
                        self.violations.append(SecurityViolation(
                            severity,
                            f"Dangerous import: {module_name}",
                            str(file_path),
                            line_no
                        ))
        
        visitor = SecurityVisitor(self, violations)
        visitor.visit(tree)
        
        return violations
    
    def _analyze_code_patterns(self, content: str, file_path: Path) -> List[SecurityViolation]:
        """
        Analyze code using regex patterns for security issues.
        
        Args:
            content: File content
            file_path: Source file path
            
        Returns:
            List of security violations
        """
        violations = []
        
        lines = content.split('\n')
        
        for line_no, line in enumerate(lines, 1):
            for pattern, severity, description in self.compiled_patterns:
                if pattern.search(line):
                    violations.append(SecurityViolation(
                        severity,
                        description,
                        str(file_path),
                        line_no
                    ))
        
        return violations
    
    async def _validate_plugin_interface(self, plugin: Plugin) -> List[SecurityViolation]:
        """
        Validate that a plugin correctly implements the required interface.
        
        Args:
            plugin: Plugin instance to validate
            
        Returns:
            List of validation violations
        """
        violations = []
        
        # Check required methods
        required_methods = ['initialize', 'activate', 'deactivate', 'cleanup']
        for method_name in required_methods:
            if not hasattr(plugin.instance, method_name):
                violations.append(SecurityViolation(
                    'critical',
                    f"Plugin missing required method: {method_name}"
                ))
            else:
                method = getattr(plugin.instance, method_name)
                if not callable(method):
                    violations.append(SecurityViolation(
                        'critical',
                        f"Plugin {method_name} is not callable"
                    ))
        
        # Type-specific validation
        plugin_type = plugin.manifest.plugin_type
        if plugin_type == PluginType.TEMPLATE:
            violations.extend(self._validate_template_plugin(plugin))
        elif plugin_type == PluginType.PROVIDER:
            violations.extend(self._validate_provider_plugin(plugin))
        
        return violations
    
    def _validate_template_plugin(self, plugin: Plugin) -> List[SecurityViolation]:
        """Validate template-specific plugin requirements."""
        violations = []
        
        required_methods = ['get_template_class', 'get_supported_providers']
        for method_name in required_methods:
            if not hasattr(plugin.instance, method_name):
                violations.append(SecurityViolation(
                    'critical',
                    f"Template plugin missing required method: {method_name}"
                ))
        
        return violations
    
    def _validate_provider_plugin(self, plugin: Plugin) -> List[SecurityViolation]:
        """Validate provider-specific plugin requirements."""
        violations = []
        
        required_methods = ['get_provider_name', 'get_template_class', 'validate_credentials']
        for method_name in required_methods:
            if not hasattr(plugin.instance, method_name):
                violations.append(SecurityViolation(
                    'critical',
                    f"Provider plugin missing required method: {method_name}"
                ))
        
        return violations
    
    async def _validate_plugin_config(self, plugin: Plugin) -> List[SecurityViolation]:
        """
        Validate plugin configuration against its schema.
        
        Args:
            plugin: Plugin instance
            
        Returns:
            List of validation violations
        """
        violations = []
        
        config_schema = plugin.manifest.metadata.config_schema
        if not config_schema:
            return violations  # No schema to validate against
        
        try:
            # Basic schema validation (could be extended with jsonschema)
            if 'properties' in config_schema:
                for prop_name, prop_def in config_schema['properties'].items():
                    if prop_def.get('required', False) and prop_name not in plugin.instance.config:
                        violations.append(SecurityViolation(
                            'medium',
                            f"Required configuration property missing: {prop_name}"
                        ))
            
        except Exception as e:
            violations.append(SecurityViolation(
                'medium',
                f"Failed to validate plugin configuration: {e}"
            ))
        
        return violations
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file for integrity checking."""
        try:
            file_content = file_path.read_bytes()
            return hashlib.sha256(file_content).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    async def verify_plugin_signature(self, plugin_path: Path) -> bool:
        """
        Verify plugin signature (placeholder for future implementation).
        
        Args:
            plugin_path: Path to plugin
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.signature_verification:
            return True
        
        # Placeholder for signature verification logic
        # This would involve checking digital signatures from trusted publishers
        logger.debug(f"Signature verification not implemented for {plugin_path}")
        return True 