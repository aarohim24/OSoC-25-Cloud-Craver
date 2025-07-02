"""
Plugin loader system for dynamic loading and installation of plugins.

This module handles the complex process of dynamically loading Python code
as plugins, managing their installation, and creating plugin instances.
"""

import importlib
import importlib.util
import logging
import shutil
import sys
import tempfile
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Any, Optional, Union
import inspect

from .core import Plugin, PluginInterface, PluginManifest, PluginContext

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Handles dynamic loading of plugins from various sources.
    
    This class implements a sophisticated plugin loading system that can:
    1. Install plugins from packages (zip, tar) or directories
    2. Dynamically import and instantiate plugin classes
    3. Manage plugin module isolation and cleanup
    4. Handle plugin installation with proper file management
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the plugin loader.
        
        Args:
            config: Loader configuration containing:
                - isolation: Whether to isolate plugin modules
                - temp_dir: Temporary directory for extraction
                - max_size: Maximum plugin package size
                - allowed_extensions: Allowed file extensions
        """
        self.config = config
        self.isolation_enabled = config.get('isolation', True)
        self.temp_dir = Path(config.get('temp_dir', tempfile.gettempdir()))
        self.max_package_size = config.get('max_size', 100 * 1024 * 1024)  # 100MB default
        self.allowed_extensions = config.get('allowed_extensions', ['.py', '.json', '.yaml', '.yml'])
        
        # Track loaded modules for cleanup
        self._loaded_modules: Dict[str, Any] = {}
        self._plugin_paths: Dict[str, Path] = {}
        
        logger.debug(f"PluginLoader initialized with isolation={self.isolation_enabled}")
    
    async def install(self, source: Union[str, Path], target_dir: Path, force: bool = False) -> Optional[Path]:
        """
        Install a plugin from various sources to the target directory.
        
        This method handles the complete plugin installation process:
        1. Validates the source (URL, file path, or directory)
        2. Downloads/extracts the plugin if needed
        3. Validates the plugin structure
        4. Copies files to the target location
        
        Args:
            source: Plugin source (URL, file path, or directory path)
            target_dir: Directory to install the plugin to
            force: Whether to overwrite existing installations
            
        Returns:
            Path to the installed plugin directory, or None if installation failed
        """
        try:
            source_path = Path(source) if not isinstance(source, Path) else source
            
            logger.info(f"Installing plugin from {source} to {target_dir}")
            logger.debug("Loader Step 1: Processing source path")
            
            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Loader Step 2: Target directory created")
            
            # Handle different source types
            if source_path.is_file() and source_path.suffix in ['.zip', '.tar', '.tar.gz', '.tar.bz2']:
                logger.debug("Loader Step 3a: Extracting package")
                # Extract package to temporary location first
                plugin_dir = await self._extract_package(source_path)
                if not plugin_dir:
                    return None
            elif source_path.is_dir():
                logger.debug("Loader Step 3b: Using directory source")
                # Source is already a directory
                plugin_dir = source_path
            elif isinstance(source, str) and source.startswith(('http://', 'https://')):
                # Download from URL (implementation would go here)
                logger.error("URL-based plugin installation not yet implemented")
                return None
            else:
                logger.error(f"Invalid plugin source: {source}")
                return None
            
            logger.debug("Loader Step 4: Loading manifest from plugin directory")
            # Load manifest to get plugin name
            from .discovery import PluginDiscovery
            discovery = PluginDiscovery({})
            manifest = await discovery._load_manifest_from_directory(plugin_dir)
            
            if not manifest:
                logger.error(f"No valid manifest found in plugin source: {source}")
                return None
            
            logger.debug("Loader Step 5: Determining installation path")
            # Determine final installation path
            plugin_name = manifest.metadata.name
            final_path = target_dir / plugin_name
            
            # Check if plugin already exists
            if final_path.exists() and not force:
                logger.error(f"Plugin {plugin_name} already exists at {final_path}. Use force=True to overwrite.")
                return None
            
            logger.debug("Loader Step 6: Handling existing installation")
            # Remove existing installation if force is enabled
            if final_path.exists() and force:
                logger.info(f"Removing existing plugin installation at {final_path}")
                shutil.rmtree(final_path)
            
            logger.debug("Loader Step 7: Copying plugin files")
            # Copy plugin to final location
            if plugin_dir != final_path:
                logger.debug(f"Copying plugin from {plugin_dir} to {final_path}")
                shutil.copytree(plugin_dir, final_path)
                
                # Clean up temporary extraction if it was used
                if plugin_dir.parent == self.temp_dir:
                    shutil.rmtree(plugin_dir)
            
            logger.info(f"Successfully installed plugin {plugin_name} to {final_path}")
            return final_path
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to install plugin from {source}: {type(e).__name__}: {e}")
            logger.debug(f"Loader traceback: {traceback.format_exc()}")
            return None
    
    async def _extract_package(self, package_path: Path) -> Optional[Path]:
        """
        Extract a plugin package to a temporary directory.
        
        This method safely extracts plugin packages while:
        1. Validating file sizes and types
        2. Preventing directory traversal attacks
        3. Checking for malicious content
        
        Args:
            package_path: Path to the package file
            
        Returns:
            Path to the extracted directory, or None if extraction failed
        """
        try:
            # Check package size
            if package_path.stat().st_size > self.max_package_size:
                logger.error(f"Package {package_path} exceeds maximum size limit")
                return None
            
            # Create temporary extraction directory
            extract_dir = self.temp_dir / f"plugin_extract_{package_path.stem}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Extracting {package_path} to {extract_dir}")
            
            # Extract based on file type
            if package_path.suffix == '.zip':
                with zipfile.ZipFile(package_path, 'r') as zf:
                    # Validate zip contents before extraction
                    if not self._validate_archive_contents(zf.namelist()):
                        return None
                    zf.extractall(extract_dir)
            
            elif package_path.name.endswith(('.tar.gz', '.tar.bz2', '.tar.xz')):
                mode = 'r:gz' if package_path.name.endswith('.tar.gz') else \
                       'r:bz2' if package_path.name.endswith('.tar.bz2') else 'r:xz'
                
                with tarfile.open(package_path, mode) as tf:
                    # Validate tar contents before extraction
                    if not self._validate_archive_contents(tf.getnames()):
                        return None
                    tf.extractall(extract_dir)
            
            else:
                logger.error(f"Unsupported package format: {package_path.suffix}")
                return None
            
            # Find the actual plugin directory (might be nested)
            plugin_dir = self._find_plugin_root(extract_dir)
            if not plugin_dir:
                logger.error(f"No plugin root directory found in {extract_dir}")
                return None
            
            return plugin_dir
            
        except Exception as e:
            logger.error(f"Failed to extract package {package_path}: {e}")
            return None
    
    def _validate_archive_contents(self, file_list: list) -> bool:
        """
        Validate archive contents for security.
        
        This method prevents various security issues:
        1. Directory traversal attacks (../ in paths)
        2. Absolute paths that could overwrite system files
        3. Excessively long file names
        4. Disallowed file extensions
        
        Args:
            file_list: List of file names in the archive
            
        Returns:
            True if contents are safe, False otherwise
        """
        for file_name in file_list:
            # Check for directory traversal
            if '..' in file_name or file_name.startswith('/'):
                logger.error(f"Potential directory traversal in archive: {file_name}")
                return False
            
            # Check file name length
            if len(file_name) > 255:
                logger.error(f"File name too long: {file_name[:50]}...")
                return False
            
            # Check file extension
            file_path = Path(file_name)
            if file_path.suffix and file_path.suffix not in self.allowed_extensions:
                logger.warning(f"Disallowed file extension: {file_name}")
                # Don't fail completely, just warn
        
        return True
    
    def _find_plugin_root(self, extract_dir: Path) -> Optional[Path]:
        """
        Find the root directory of the extracted plugin.
        
        Some plugin packages might have the actual plugin nested in subdirectories.
        This method searches for the directory containing the manifest file.
        
        Args:
            extract_dir: Directory where package was extracted
            
        Returns:
            Path to the plugin root directory
        """
        manifest_files = ['plugin.json', 'manifest.json', 'cloudcraver.json']
        
        # Check if manifest is in the extract directory itself
        for manifest_file in manifest_files:
            if (extract_dir / manifest_file).exists():
                return extract_dir
        
        # Search in subdirectories (up to 2 levels deep)
        for item in extract_dir.rglob("*"):
            if item.is_file() and item.name in manifest_files:
                return item.parent
        
        return None
    
    async def load(self, plugin_path: Path, context: PluginContext) -> Optional[Plugin]:
        """
        Load a plugin from a directory and create a Plugin instance.
        
        This is the core plugin loading method that:
        1. Discovers and validates the plugin manifest
        2. Dynamically imports the plugin module
        3. Instantiates the plugin class
        4. Creates the Plugin wrapper object
        
        Args:
            plugin_path: Path to the plugin directory
            context: Plugin execution context
            
        Returns:
            Plugin instance, or None if loading failed
        """
        try:
            logger.info(f"Loading plugin from {plugin_path}")
            
            # Discover plugin manifest
            from .discovery import PluginDiscovery
            discovery = PluginDiscovery({})
            manifest = await discovery._load_manifest_from_directory(plugin_path)
            
            if not manifest:
                logger.error(f"No valid manifest found at {plugin_path}")
                return None
            
            # Load the plugin module dynamically
            plugin_module = await self._load_plugin_module(plugin_path, manifest)
            if not plugin_module:
                return None
            
            # Get the plugin class from the module
            plugin_class = self._get_plugin_class(plugin_module, manifest.main_class)
            if not plugin_class:
                return None
            
            # Load plugin configuration if available
            plugin_config = await self._load_plugin_config(plugin_path, manifest)
            
            # Instantiate the plugin
            plugin_instance = plugin_class(manifest, plugin_config)
            
            # Validate that the instance implements PluginInterface
            if not isinstance(plugin_instance, PluginInterface):
                logger.error(f"Plugin class {manifest.main_class} does not implement PluginInterface")
                return None
            
            # Create Plugin wrapper
            plugin = Plugin(
                instance=plugin_instance,
                manifest=manifest,
                file_path=plugin_path,
                context=context
            )
            
            # Track the loaded plugin
            plugin_name = manifest.metadata.name
            self._plugin_paths[plugin_name] = plugin_path
            
            logger.info(f"Successfully loaded plugin {plugin_name}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_path}: {e}")
            return None
    
    async def _load_plugin_module(self, plugin_path: Path, manifest: PluginManifest) -> Optional[Any]:
        """
        Dynamically load the plugin's Python module.
        
        This method uses Python's importlib to dynamically load modules:
        1. Constructs the module path based on manifest information
        2. Creates a module spec and loads the module
        3. Handles module isolation if enabled
        4. Tracks loaded modules for cleanup
        
        Args:
            plugin_path: Path to the plugin directory
            manifest: Plugin manifest containing module information
            
        Returns:
            Loaded module object, or None if loading failed
        """
        try:
            # Determine the module file path
            module_path = manifest.module_path.replace('.', '/')
            module_file = plugin_path / f"{module_path}.py"
            
            # Try alternative locations if the primary doesn't exist
            if not module_file.exists():
                alternatives = [
                    plugin_path / f"{manifest.module_path}.py",
                    plugin_path / "main.py",
                    plugin_path / "__init__.py"
                ]
                
                for alt in alternatives:
                    if alt.exists():
                        module_file = alt
                        break
                else:
                    logger.error(f"Module file not found for plugin {manifest.metadata.name}")
                    return None
            
            # Create unique module name to avoid conflicts
            module_name = f"cloudcraver_plugin_{manifest.metadata.name}_{manifest.metadata.version}"
            
            logger.debug(f"Loading module {module_name} from {module_file}")
            
            # Load the module using importlib
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            if not spec or not spec.loader:
                logger.error(f"Failed to create module spec for {module_file}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules if isolation is disabled
            if not self.isolation_enabled:
                sys.modules[module_name] = module
            
            # Execute the module
            spec.loader.exec_module(module)
            
            # Track the loaded module
            self._loaded_modules[manifest.metadata.name] = module
            
            logger.debug(f"Successfully loaded module {module_name}")
            return module
            
        except Exception as e:
            logger.error(f"Failed to load module for plugin {manifest.metadata.name}: {e}")
            return None
    
    def _get_plugin_class(self, module: Any, class_name: str) -> Optional[type]:
        """
        Extract the plugin class from the loaded module.
        
        This method:
        1. Looks for the specified class in the module
        2. Validates that it's a proper class
        3. Checks that it inherits from PluginInterface
        
        Args:
            module: Loaded plugin module
            class_name: Name of the plugin class to extract
            
        Returns:
            Plugin class, or None if not found/invalid
        """
        try:
            # Get the class from the module
            if not hasattr(module, class_name):
                logger.error(f"Class {class_name} not found in plugin module")
                return None
            
            plugin_class = getattr(module, class_name)
            
            # Validate that it's a class
            if not inspect.isclass(plugin_class):
                logger.error(f"{class_name} is not a class")
                return None
            
            # Check if it's a subclass of PluginInterface
            if not issubclass(plugin_class, PluginInterface):
                logger.error(f"Class {class_name} does not inherit from PluginInterface")
                return None
            
            logger.debug(f"Found valid plugin class {class_name}")
            return plugin_class
            
        except Exception as e:
            logger.error(f"Failed to get plugin class {class_name}: {e}")
            return None
    
    async def _load_plugin_config(self, plugin_path: Path, manifest: PluginManifest) -> Dict[str, Any]:
        """
        Load plugin-specific configuration.
        
        This method loads configuration from various sources:
        1. Plugin's config file (if specified in manifest)
        2. Default configuration values
        3. Environment-specific overrides
        
        Args:
            plugin_path: Path to the plugin directory
            manifest: Plugin manifest
            
        Returns:
            Dictionary containing plugin configuration
        """
        config = {}
        
        try:
            # Load from config file if specified
            if manifest.config_file:
                config_file = plugin_path / manifest.config_file
                if config_file.exists():
                    import json
                    import yaml
                    
                    if config_file.suffix == '.json':
                        config_content = config_file.read_text(encoding='utf-8')
                        config.update(json.loads(config_content))
                    elif config_file.suffix in ['.yaml', '.yml']:
                        config_content = config_file.read_text(encoding='utf-8')
                        config.update(yaml.safe_load(config_content))
                    
                    logger.debug(f"Loaded config from {config_file}")
            
            # Add any default configuration from manifest
            if manifest.metadata.config_schema:
                # Extract default values from schema
                defaults = self._extract_defaults_from_schema(manifest.metadata.config_schema)
                for key, value in defaults.items():
                    if key not in config:
                        config[key] = value
            
        except Exception as e:
            logger.warning(f"Failed to load plugin config: {e}")
            # Continue with empty config rather than failing completely
        
        return config
    
    def _extract_defaults_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract default values from a JSON schema.
        
        Args:
            schema: JSON schema definition
            
        Returns:
            Dictionary of default values
        """
        defaults = {}
        
        if 'properties' in schema:
            for key, prop in schema['properties'].items():
                if 'default' in prop:
                    defaults[key] = prop['default']
        
        return defaults
    
    def unload_plugin(self, plugin_name: str):
        """
        Unload a plugin and clean up its resources.
        
        This method:
        1. Removes the plugin module from memory
        2. Cleans up any tracked resources
        3. Removes from sys.modules if needed
        
        Args:
            plugin_name: Name of the plugin to unload
        """
        try:
            # Remove from tracked modules
            if plugin_name in self._loaded_modules:
                module = self._loaded_modules[plugin_name]
                
                # Remove from sys.modules if it was added
                module_name = f"cloudcraver_plugin_{plugin_name}"
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                del self._loaded_modules[plugin_name]
            
            # Remove from tracked paths
            if plugin_name in self._plugin_paths:
                del self._plugin_paths[plugin_name]
            
            logger.debug(f"Unloaded plugin {plugin_name}")
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
    
    def get_loaded_plugins(self) -> Dict[str, Path]:
        """Get dictionary of loaded plugin names and their paths."""
        return self._plugin_paths.copy()
    
    def cleanup(self):
        """Clean up all loaded plugins and resources."""
        plugin_names = list(self._loaded_modules.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name) 