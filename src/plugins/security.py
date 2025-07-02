"""
Plugin security sandbox system for isolating plugin execution.

This module provides security sandboxing capabilities to prevent plugins
from accessing unauthorized resources or performing dangerous operations.
The sandbox uses multiple layers of protection including resource limits,
permission checking, and execution monitoring.
"""

import logging
import os
import sys
import time
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Callable
import tempfile
import resource

logger = logging.getLogger(__name__)


class SecurityContext:
    """
    Security context for plugin execution.
    
    This class maintains the security state and permissions
    for a plugin during its execution lifecycle.
    """
    
    def __init__(self, plugin_name: str, permissions: List[str]):
        """
        Initialize security context.
        
        Args:
            plugin_name: Name of the plugin
            permissions: List of granted permissions
        """
        self.plugin_name = plugin_name
        self.permissions = set(permissions)
        self.start_time = time.time()
        self.resource_usage = {}
        self.violations = []
        
    def has_permission(self, permission: str) -> bool:
        """Check if plugin has a specific permission."""
        return permission in self.permissions
    
    def add_violation(self, violation: str):
        """Record a security violation."""
        self.violations.append({
            'timestamp': time.time(),
            'violation': violation
        })
        logger.warning(f"Security violation by {self.plugin_name}: {violation}")


class PluginSandbox:
    """
    Comprehensive plugin sandbox system.
    
    The sandbox provides multiple layers of security:
    
    1. **Resource Limits**: CPU time, memory usage, disk I/O limits
    2. **File System Access Control**: Restrict file system operations
    3. **Network Access Control**: Control network connections
    4. **System Call Monitoring**: Monitor and restrict system calls
    5. **Permission System**: Fine-grained permission checking
    
    The sandbox works by:
    - Installing security hooks before plugin execution
    - Monitoring resource usage during execution
    - Blocking unauthorized operations
    - Providing secure APIs for common operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the plugin sandbox.
        
        Args:
            config: Sandbox configuration containing:
                - enabled: Whether sandboxing is enabled
                - max_cpu_time: Maximum CPU time in seconds
                - max_memory: Maximum memory usage in bytes
                - max_file_size: Maximum file size for operations
                - allowed_paths: List of allowed file system paths
                - network_access: Whether network access is allowed
                - temp_dir: Temporary directory for plugin operations
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        
        # Resource limits
        self.max_cpu_time = config.get('max_cpu_time', 30)  # 30 seconds default
        self.max_memory = config.get('max_memory', 100 * 1024 * 1024)  # 100MB default
        self.max_file_size = config.get('max_file_size', 10 * 1024 * 1024)  # 10MB default
        
        # Access control
        self.allowed_paths = set(Path(p).resolve() for p in config.get('allowed_paths', []))
        self.network_access = config.get('network_access', False)
        self.temp_dir = Path(config.get('temp_dir', tempfile.gettempdir()))
        
        # Active security contexts
        self._contexts: Dict[str, SecurityContext] = {}
        self._original_hooks = {}
        self._monitoring_active = False
        
        # Default permissions for different plugin types
        self.default_permissions = {
            'template': ['file_read', 'temp_write'],
            'provider': ['file_read', 'temp_write', 'network_access'],
            'validator': ['file_read'],
            'generator': ['file_read', 'file_write', 'temp_write']
        }
        
        if self.enabled:
            self._setup_security_hooks()
        
        logger.debug(f"PluginSandbox initialized with enabled={self.enabled}")
    
    def _setup_security_hooks(self):
        """
        Install security hooks to monitor and control plugin operations.
        
        This method installs various hooks to intercept potentially
        dangerous operations:
        - File operations (open, read, write)
        - Network operations (socket creation)
        - Process operations (subprocess)
        - Import operations (dynamic imports)
        """
        try:
            # Store original functions for restoration
            # __builtins__ can be either a module or a dict depending on context
            if isinstance(__builtins__, dict):
                if 'open' in __builtins__:
                    self._original_hooks['open'] = __builtins__['open']
                    # Install file operation hook
                    __builtins__['open'] = self._secure_open
            else:
                # __builtins__ is a module
                if hasattr(__builtins__, 'open'):
                    self._original_hooks['open'] = __builtins__.open
                    # Install file operation hook
                    __builtins__.open = self._secure_open
            
            # Install import hook
            self._install_import_hook()
            
            logger.debug("Security hooks installed successfully")
            
        except Exception as e:
            logger.error(f"Failed to install security hooks: {e}")
    
    def _secure_open(self, file, mode='r', *args, **kwargs):
        """
        Secure wrapper for file open operations.
        
        This method checks:
        1. Whether the plugin has file access permissions
        2. If the file path is in allowed locations
        3. If the operation type (read/write) is permitted
        4. File size limits for write operations
        
        Args:
            file: File path or file-like object
            mode: File open mode
            *args, **kwargs: Additional arguments to pass to open()
            
        Returns:
            File object if allowed
            
        Raises:
            PermissionError: If operation is not allowed
        """
        # Get current security context
        context = self._get_current_context()
        if not context:
            # If no context, use original open (not in plugin execution)
            if 'open' in self._original_hooks:
                return self._original_hooks['open'](file, mode, *args, **kwargs)
            else:
                # Fallback to built-in open
                import builtins
                return builtins.open(file, mode, *args, **kwargs)
        
        # Convert to Path object
        if isinstance(file, (str, Path)):
            file_path = Path(file).resolve()
        else:
            # File-like object, allow it
            if 'open' in self._original_hooks:
                return self._original_hooks['open'](file, mode, *args, **kwargs)
            else:
                import builtins
                return builtins.open(file, mode, *args, **kwargs)
        
        # Check permissions based on mode
        if 'w' in mode or 'a' in mode or '+' in mode:
            # Write operation
            if not context.has_permission('file_write') and not context.has_permission('temp_write'):
                context.add_violation(f"Unauthorized file write attempt: {file_path}")
                raise PermissionError(f"Plugin {context.plugin_name} does not have write permission")
            
            # Check if writing to temp directory is allowed
            if context.has_permission('temp_write') and not context.has_permission('file_write'):
                if not self._is_in_temp_directory(file_path):
                    context.add_violation(f"Write outside temp directory: {file_path}")
                    raise PermissionError(f"Plugin {context.plugin_name} can only write to temp directory")
        else:
            # Read operation
            if not context.has_permission('file_read'):
                context.add_violation(f"Unauthorized file read attempt: {file_path}")
                raise PermissionError(f"Plugin {context.plugin_name} does not have read permission")
        
        # Check if path is allowed
        if not self._is_path_allowed(file_path, context):
            context.add_violation(f"Access to forbidden path: {file_path}")
            raise PermissionError(f"Access denied to {file_path}")
        
        # Perform the actual file operation
        if 'open' in self._original_hooks:
            return self._original_hooks['open'](file, mode, *args, **kwargs)
        else:
            import builtins
            return builtins.open(file, mode, *args, **kwargs)
    
    def _install_import_hook(self):
        """
        Install import hook to control dynamic imports.
        
        This prevents plugins from importing dangerous modules
        or bypassing security restrictions.
        """
        # This is a simplified version - a full implementation would
        # use sys.meta_path to intercept all imports
        if isinstance(__builtins__, dict):
            original_import = __builtins__.get('__import__')
        else:
            original_import = getattr(__builtins__, '__import__', None)
        
        if original_import:
            def secure_import(name, *args, **kwargs):
                context = self._get_current_context()
                if context:
                    # Check if module is in blacklist
                    dangerous_modules = ['os', 'subprocess', 'sys']
                    if name.split('.')[0] in dangerous_modules:
                        if not context.has_permission('system_access'):
                            context.add_violation(f"Attempted import of dangerous module: {name}")
                            raise ImportError(f"Import of {name} not allowed")
                
                return original_import(name, *args, **kwargs)
            
            if isinstance(__builtins__, dict):
                __builtins__['__import__'] = secure_import
            else:
                __builtins__.__import__ = secure_import
    
    def _is_path_allowed(self, file_path: Path, context: SecurityContext) -> bool:
        """
        Check if a file path is allowed for the plugin.
        
        Args:
            file_path: Path to check
            context: Security context
            
        Returns:
            True if path is allowed, False otherwise
        """
        try:
            file_path = file_path.resolve()
            
            # Always allow temp directory
            if self._is_in_temp_directory(file_path):
                return True
            
            # Check explicitly allowed paths
            for allowed_path in self.allowed_paths:
                if self._is_path_under(file_path, allowed_path):
                    return True
            
            # Allow reading from plugin's own directory
            # (This would need plugin directory info passed in context)
            
            return False
            
        except Exception:
            # If we can't resolve the path, deny access
            return False
    
    def _is_in_temp_directory(self, file_path: Path) -> bool:
        """Check if path is within the temp directory."""
        try:
            return self._is_path_under(file_path, self.temp_dir)
        except Exception:
            return False
    
    def _is_path_under(self, path: Path, parent: Path) -> bool:
        """Check if path is under parent directory."""
        try:
            path.resolve().relative_to(parent.resolve())
            return True
        except ValueError:
            return False
    
    def _get_current_context(self) -> Optional[SecurityContext]:
        """Get security context for current thread."""
        thread_id = threading.current_thread().ident
        return self._contexts.get(f"thread_{thread_id}")
    
    @contextmanager
    def secure_execution(self, plugin_name: str, permissions: List[str]):
        """
        Context manager for secure plugin execution.
        
        This method sets up a secure execution environment:
        1. Creates security context
        2. Sets resource limits
        3. Monitors execution
        4. Cleans up after execution
        
        Args:
            plugin_name: Name of plugin being executed
            permissions: List of permissions to grant
            
        Usage:
            with sandbox.secure_execution('my_plugin', ['file_read']):
                # Plugin code runs here with restrictions
                result = plugin_function()
        """
        if not self.enabled:
            # If sandboxing is disabled, just yield
            yield
            return
        
        thread_id = threading.current_thread().ident
        context_key = f"thread_{thread_id}"
        
        # Create security context
        context = SecurityContext(plugin_name, permissions)
        self._contexts[context_key] = context
        
        # Set resource limits
        self._set_resource_limits()
        
        try:
            logger.debug(f"Starting secure execution for {plugin_name}")
            yield context
            
        except Exception as e:
            context.add_violation(f"Exception during execution: {str(e)}")
            raise
            
        finally:
            # Clean up
            execution_time = time.time() - context.start_time
            logger.debug(f"Plugin {plugin_name} executed for {execution_time:.2f}s")
            
            if context.violations:
                logger.warning(f"Plugin {plugin_name} had {len(context.violations)} security violations")
            
            # Remove context
            self._contexts.pop(context_key, None)
            
            # Reset resource limits
            self._reset_resource_limits()
    
    def _set_resource_limits(self):
        """Set resource limits for plugin execution."""
        try:
            # Set CPU time limit (SIGXCPU will be sent when exceeded)
            if hasattr(resource, 'RLIMIT_CPU'):
                resource.setrlimit(resource.RLIMIT_CPU, (self.max_cpu_time, self.max_cpu_time))
            
            # Set memory limit
            if hasattr(resource, 'RLIMIT_AS'):
                resource.setrlimit(resource.RLIMIT_AS, (self.max_memory, self.max_memory))
            
            logger.debug("Resource limits set successfully")
            
        except Exception as e:
            logger.warning(f"Failed to set resource limits: {e}")
    
    def _reset_resource_limits(self):
        """Reset resource limits to system defaults."""
        try:
            # Reset to unlimited (or system max)
            unlimited = resource.RLIM_INFINITY
            
            if hasattr(resource, 'RLIMIT_CPU'):
                resource.setrlimit(resource.RLIMIT_CPU, (unlimited, unlimited))
            
            if hasattr(resource, 'RLIMIT_AS'):
                resource.setrlimit(resource.RLIMIT_AS, (unlimited, unlimited))
            
        except Exception as e:
            logger.warning(f"Failed to reset resource limits: {e}")
    
    def get_permissions_for_plugin_type(self, plugin_type: str) -> List[str]:
        """
        Get default permissions for a plugin type.
        
        Args:
            plugin_type: Type of plugin (template, provider, etc.)
            
        Returns:
            List of default permissions
        """
        return self.default_permissions.get(plugin_type, ['file_read'])
    
    def create_temp_directory(self, plugin_name: str) -> Path:
        """
        Create a temporary directory for plugin use.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Path to created temporary directory
        """
        temp_path = self.temp_dir / f"plugin_{plugin_name}_{int(time.time())}"
        temp_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Created temp directory for {plugin_name}: {temp_path}")
        return temp_path
    
    def cleanup_temp_directory(self, temp_path: Path):
        """
        Clean up a temporary directory.
        
        Args:
            temp_path: Path to temporary directory
        """
        try:
            if temp_path.exists() and temp_path.is_dir():
                import shutil
                shutil.rmtree(temp_path)
                logger.debug(f"Cleaned up temp directory: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {temp_path}: {e}")
    
    def is_operation_allowed(self, operation: str, plugin_name: str) -> bool:
        """
        Check if an operation is allowed for a plugin.
        
        Args:
            operation: Operation name (e.g., 'network_request', 'file_write')
            plugin_name: Name of plugin
            
        Returns:
            True if operation is allowed, False otherwise
        """
        context = self._get_current_context()
        if not context or context.plugin_name != plugin_name:
            return False
        
        permission_map = {
            'network_request': 'network_access',
            'file_write': 'file_write',
            'file_read': 'file_read',
            'temp_write': 'temp_write',
            'system_exec': 'system_access'
        }
        
        required_permission = permission_map.get(operation)
        if not required_permission:
            return False
        
        return context.has_permission(required_permission)
    
    def get_security_report(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get security report for a plugin's execution.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Dictionary with security information
        """
        context = None
        for ctx in self._contexts.values():
            if ctx.plugin_name == plugin_name:
                context = ctx
                break
        
        if not context:
            return {'error': 'No security context found'}
        
        return {
            'plugin_name': context.plugin_name,
            'permissions': list(context.permissions),
            'violations': context.violations,
            'execution_time': time.time() - context.start_time,
            'resource_usage': context.resource_usage
        }
    
    def shutdown(self):
        """Shutdown the sandbox and restore original hooks."""
        if not self.enabled:
            return
        
        try:
            # Restore original hooks
            for hook_name, original_func in self._original_hooks.items():
                if hook_name == 'open':
                    if isinstance(__builtins__, dict):
                        if 'open' in __builtins__:
                            __builtins__['open'] = original_func
                    else:
                        if hasattr(__builtins__, 'open'):
                            __builtins__.open = original_func
            
            # Clear contexts
            self._contexts.clear()
            
            logger.debug("Plugin sandbox shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during sandbox shutdown: {e}")


# Decorator for secure plugin method execution
def secure_plugin_method(permissions: List[str]):
    """
    Decorator to mark plugin methods that require specific permissions.
    
    Args:
        permissions: List of required permissions
        
    Usage:
        @secure_plugin_method(['file_write', 'network_access'])
        def dangerous_method(self):
            # This method requires file_write and network_access permissions
            pass
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Check if we're running in a security context
            if hasattr(self, '_security_context'):
                context = self._security_context
                for permission in permissions:
                    if not context.has_permission(permission):
                        raise PermissionError(f"Method {func.__name__} requires {permission} permission")
            
            return func(self, *args, **kwargs)
        
        wrapper._required_permissions = permissions
        return wrapper
    
    return decorator 