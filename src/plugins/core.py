"""
Core plugin system interfaces and base classes.
"""

import abc
import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union, Callable
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class PluginLifecycleStage(Enum):
    """Plugin lifecycle stages."""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    CONFIGURED = "configured"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ERROR = "error"
    UNINSTALLED = "uninstalled"


class PluginType(Enum):
    """Plugin types for categorization."""
    TEMPLATE = "template"
    PROVIDER = "provider" 
    VALIDATOR = "validator"
    GENERATOR = "generator"
    HOOK = "hook"
    EXTENSION = "extension"
    MIDDLEWARE = "middleware"


@dataclass
class PluginMetadata:
    """Plugin metadata information."""
    name: str
    version: str
    description: str
    author: str
    email: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    min_core_version: Optional[str] = None
    max_core_version: Optional[str] = None
    python_requires: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    entry_points: Dict[str, str] = field(default_factory=dict)
    config_schema: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PluginManifest:
    """Plugin manifest containing all plugin information."""
    metadata: PluginMetadata
    plugin_type: PluginType
    main_class: str
    module_path: str
    config_file: Optional[str] = None
    assets_dir: Optional[str] = None
    docs_dir: Optional[str] = None
    tests_dir: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)


class PluginInterface(abc.ABC):
    """Base interface that all plugins must implement."""
    
    def __init__(self, manifest: PluginManifest, config: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin with manifest and configuration.
        
        Args:
            manifest: Plugin manifest containing metadata
            config: Plugin configuration dictionary
        """
        self.manifest = manifest
        self.config = config or {}
        self.plugin_id = str(uuid.uuid4())
        self.stage = PluginLifecycleStage.UNLOADED
        self._hooks: Dict[str, List[Callable]] = {}
        
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def activate(self) -> bool:
        """
        Activate the plugin.
        
        Returns:
            True if activation successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def deactivate(self) -> bool:
        """
        Deactivate the plugin.
        
        Returns:
            True if deactivation successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def cleanup(self) -> bool:
        """
        Clean up plugin resources.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        pass
    
    def get_name(self) -> str:
        """Get plugin name."""
        return self.manifest.metadata.name
    
    def get_version(self) -> str:
        """Get plugin version."""
        return self.manifest.metadata.version
    
    def get_type(self) -> PluginType:
        """Get plugin type."""
        return self.manifest.plugin_type
    
    def get_stage(self) -> PluginLifecycleStage:
        """Get current lifecycle stage."""
        return self.stage
    
    def set_stage(self, stage: PluginLifecycleStage):
        """Set lifecycle stage."""
        old_stage = self.stage
        self.stage = stage
        logger.debug(f"Plugin {self.get_name()} stage changed from {old_stage} to {stage}")
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
    
    def get_hooks(self, hook_name: str) -> List[Callable]:
        """Get registered hooks for a given name."""
        return self._hooks.get(hook_name, [])
    
    async def emit_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Emit a hook and collect results."""
        results = []
        for callback in self.get_hooks(hook_name):
            try:
                if inspect.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {hook_name} callback failed: {e}")
        return results


class TemplatePlugin(PluginInterface):
    """Base class for template plugins."""
    
    @abc.abstractmethod
    def get_template_class(self) -> Type:
        """Return the template class this plugin provides."""
        pass
    
    @abc.abstractmethod
    def get_supported_providers(self) -> List[str]:
        """Return list of supported cloud providers."""
        pass


class ProviderPlugin(PluginInterface):
    """Base class for provider plugins."""
    
    @abc.abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @abc.abstractmethod
    def get_template_class(self) -> Type:
        """Return the template class for this provider."""
        pass
    
    @abc.abstractmethod
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate provider credentials."""
        pass


class ValidatorPlugin(PluginInterface):
    """Base class for validator plugins."""
    
    @abc.abstractmethod
    def validate(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate content and return validation results.
        
        Args:
            content: Content to validate
            context: Validation context
            
        Returns:
            Dictionary with validation results
        """
        pass


class HookPlugin(PluginInterface):
    """Base class for hook plugins that extend core functionality."""
    
    @abc.abstractmethod
    def get_hook_points(self) -> List[str]:
        """Return list of hook points this plugin supports."""
        pass


@dataclass
class PluginContext:
    """Context passed to plugins during lifecycle operations."""
    core_version: str
    config_manager: Any
    logger: logging.Logger
    data_dir: Path
    cache_dir: Path
    temp_dir: Path
    environment: str = "production"
    
    
class Plugin:
    """Container for plugin instance and metadata."""
    
    def __init__(
        self,
        instance: PluginInterface,
        manifest: PluginManifest,
        file_path: Path,
        context: PluginContext
    ):
        """
        Initialize plugin container.
        
        Args:
            instance: Plugin instance
            manifest: Plugin manifest
            file_path: Path to plugin file
            context: Plugin context
        """
        self.instance = instance
        self.manifest = manifest
        self.file_path = file_path
        self.context = context
        self.enabled = False
        self.load_time: Optional[datetime] = None
        self.error: Optional[Exception] = None
        
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.manifest.metadata.name
    
    @property
    def version(self) -> str:
        """Get plugin version."""
        return self.manifest.metadata.version
    
    @property
    def stage(self) -> PluginLifecycleStage:
        """Get plugin stage."""
        return self.instance.stage
    
    async def load(self) -> bool:
        """Load the plugin."""
        try:
            self.instance.set_stage(PluginLifecycleStage.LOADED)
            self.load_time = datetime.now()
            return True
        except Exception as e:
            self.error = e
            self.instance.set_stage(PluginLifecycleStage.ERROR)
            logger.error(f"Failed to load plugin {self.name}: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        try:
            result = await self.instance.initialize()
            if result:
                self.instance.set_stage(PluginLifecycleStage.INITIALIZED)
            return result
        except Exception as e:
            self.error = e
            self.instance.set_stage(PluginLifecycleStage.ERROR)
            logger.error(f"Failed to initialize plugin {self.name}: {e}")
            return False
    
    async def activate(self) -> bool:
        """Activate the plugin."""
        try:
            result = await self.instance.activate()
            if result:
                self.instance.set_stage(PluginLifecycleStage.ACTIVE)
                self.enabled = True
            return result
        except Exception as e:
            self.error = e
            self.instance.set_stage(PluginLifecycleStage.ERROR)
            logger.error(f"Failed to activate plugin {self.name}: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Deactivate the plugin."""
        try:
            result = await self.instance.deactivate()
            if result:
                self.instance.set_stage(PluginLifecycleStage.SUSPENDED)
                self.enabled = False
            return result
        except Exception as e:
            self.error = e
            self.instance.set_stage(PluginLifecycleStage.ERROR)
            logger.error(f"Failed to deactivate plugin {self.name}: {e}")
            return False
    
    async def unload(self) -> bool:
        """Unload the plugin."""
        try:
            await self.instance.cleanup()
            self.instance.set_stage(PluginLifecycleStage.UNLOADED)
            self.enabled = False
            return True
        except Exception as e:
            self.error = e
            self.instance.set_stage(PluginLifecycleStage.ERROR)
            logger.error(f"Failed to unload plugin {self.name}: {e}")
            return False


class PluginManager:
    """Main plugin manager that orchestrates all plugin operations."""
    
    def __init__(self, config: Dict[str, Any], data_dir: Path, cache_dir: Path):
        """
        Initialize plugin manager.
        
        Args:
            config: Plugin system configuration
            data_dir: Data directory path
            cache_dir: Cache directory path
        """
        # Import components dynamically to avoid circular imports
        import importlib
        
        discovery_mod = importlib.import_module('plugins.discovery')
        loader_mod = importlib.import_module('plugins.loader')
        registry_mod = importlib.import_module('plugins.registry')
        validator_mod = importlib.import_module('plugins.validator')
        security_mod = importlib.import_module('plugins.security')
        dependency_mod = importlib.import_module('plugins.dependency')
        marketplace_mod = importlib.import_module('plugins.marketplace')
        versioning_mod = importlib.import_module('plugins.versioning')
        
        self.config = config
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        
        # Initialize components
        self.discovery = discovery_mod.PluginDiscovery(config.get('discovery', {}))
        self.loader = loader_mod.PluginLoader(config.get('loader', {}))
        self.registry = registry_mod.PluginRegistry(data_dir / 'plugins' / 'registry.json')
        self.validator = validator_mod.PluginValidator(config.get('validator', {}))
        self.sandbox = security_mod.PluginSandbox(config.get('security', {}))
        self.dependency_manager = dependency_mod.DependencyManager(config.get('dependencies', {}))
        self.marketplace = marketplace_mod.PluginMarketplace(config.get('marketplace', {}))
        self.version_manager = versioning_mod.VersionManager(config.get('versioning', {}))
        
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Plugin]] = {}
        
        # Create plugin context
        self.context = PluginContext(
            core_version="1.0.0",  # This should come from main app
            config_manager=None,   # This should be injected
            logger=logger,
            data_dir=data_dir,
            cache_dir=cache_dir,
            temp_dir=cache_dir / 'temp'
        )
        
    async def discover_plugins(self, search_paths: Optional[List[Path]] = None) -> List[PluginManifest]:
        """Discover available plugins."""
        return await self.discovery.discover(search_paths)
    
    async def install_plugin(self, source: Union[str, Path], force: bool = False) -> Optional[str]:
        """Install a plugin from various sources. Returns plugin name on success, None on failure."""
        try:
            # Validate plugin before installation
            logger.debug("Step 1: Validating plugin package")
            manifest = await self.validator.validate_plugin_package(source)
            if not manifest:
                logger.error("Plugin validation failed")
                return None
            logger.debug("Step 1 completed: Plugin validation passed")
            
            # Check dependencies
            logger.debug("Step 2: Checking dependencies")
            if not await self.dependency_manager.check_dependencies(manifest):
                logger.error(f"Dependency check failed for plugin {manifest.metadata.name}")
                return None
            logger.debug("Step 2 completed: Dependency check passed")
            
            # Install plugin
            logger.debug("Step 3: Installing plugin files")
            plugin_path = await self.loader.install(source, self.data_dir / 'plugins', force)
            if not plugin_path:
                logger.error("Plugin file installation failed")
                return None
            logger.debug(f"Step 3 completed: Plugin installed to {plugin_path}")
            
            # Register plugin
            logger.debug("Step 4: Registering plugin in registry")
            await self.registry.register(manifest, plugin_path)
            logger.debug("Step 4 completed: Plugin registered successfully")
            
            plugin_name = manifest.metadata.name
            logger.info(f"Successfully installed plugin {plugin_name}")
            return plugin_name
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to install plugin: {type(e).__name__}: {e}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None
    
    async def load_plugin(self, name: str) -> bool:
        """Load a specific plugin."""
        try:
            if name in self.plugins:
                logger.warning(f"Plugin {name} already loaded")
                return True
            
            # Get plugin info from registry
            plugin_info = await self.registry.get_plugin(name)
            if not plugin_info:
                logger.error(f"Plugin {name} not found in registry")
                return False
            
            # Load plugin
            plugin = await self.loader.load(Path(plugin_info['install_path']), self.context)
            if not plugin:
                return False
            
            # Validate plugin
            if not await self.validator.validate_plugin(plugin):
                logger.error(f"Plugin {name} failed validation")
                return False
            
            # Initialize and activate
            if await plugin.load() and await plugin.initialize() and await plugin.activate():
                self.plugins[name] = plugin
                self._register_hooks(plugin)
                logger.info(f"Successfully loaded plugin {name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            return False
    
    async def unload_plugin(self, name: str) -> bool:
        """Unload a specific plugin."""
        try:
            if name not in self.plugins:
                logger.warning(f"Plugin {name} not loaded")
                return True
            
            plugin = self.plugins[name]
            await plugin.deactivate()
            await plugin.unload()
            
            self._unregister_hooks(plugin)
            del self.plugins[name]
            
            logger.info(f"Successfully unloaded plugin {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {name}: {e}")
            return False
    
    async def load_all_plugins(self) -> int:
        """Load all registered plugins."""
        registered_plugins = await self.registry.list_plugins()
        loaded_count = 0
        
        for plugin_name in registered_plugins:
            if await self.load_plugin(plugin_name):
                loaded_count += 1
        
        logger.info(f"Loaded {loaded_count} out of {len(registered_plugins)} plugins")
        return loaded_count
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name."""
        return self.plugins.get(name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all loaded plugins of a specific type."""
        return [p for p in self.plugins.values() if p.manifest.plugin_type == plugin_type]
    
    def get_template_plugins(self) -> List[Plugin]:
        """Get all template plugins."""
        return self.get_plugins_by_type(PluginType.TEMPLATE)
    
    def get_provider_plugins(self) -> List[Plugin]:
        """Get all provider plugins."""
        return self.get_plugins_by_type(PluginType.PROVIDER)
    
    async def emit_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Emit a hook to all registered plugins."""
        results = []
        for plugin in self.hooks.get(hook_name, []):
            try:
                plugin_results = await plugin.instance.emit_hook(hook_name, *args, **kwargs)
                results.extend(plugin_results)
            except Exception as e:
                logger.error(f"Plugin {plugin.name} hook {hook_name} failed: {e}")
        return results
    
    def _register_hooks(self, plugin: Plugin):
        """Register plugin hooks."""
        for hook_name in plugin.manifest.hooks:
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            self.hooks[hook_name].append(plugin)
    
    def _unregister_hooks(self, plugin: Plugin):
        """Unregister plugin hooks."""
        for hook_name in plugin.manifest.hooks:
            if hook_name in self.hooks:
                self.hooks[hook_name] = [p for p in self.hooks[hook_name] if p != plugin]
    
    async def check_updates(self) -> Dict[str, str]:
        """Check for plugin updates."""
        return await self.version_manager.check_updates(list(self.plugins.keys()))
    
    async def update_plugin(self, name: str) -> bool:
        """Update a specific plugin."""
        return await self.version_manager.update_plugin(name)
    
    async def search_marketplace(self, query: str) -> List[Dict[str, Any]]:
        """Search the plugin marketplace."""
        return await self.marketplace.search(query)
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin system status."""
        return {
            'total_plugins': len(self.plugins),
            'active_plugins': len([p for p in self.plugins.values() if p.enabled]),
            'plugins_by_type': {
                pt.value: len(self.get_plugins_by_type(pt)) 
                for pt in PluginType
            },
            'plugins': {
                name: {
                    'version': plugin.version,
                    'stage': plugin.stage.value,
                    'enabled': plugin.enabled,
                    'error': str(plugin.error) if plugin.error else None
                }
                for name, plugin in self.plugins.items()
            }
        } 