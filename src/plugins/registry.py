"""
Plugin registry system for managing installed plugins and their metadata.

The registry acts as a central database for all installed plugins, tracking:
- Plugin metadata and versions
- Installation paths and status
- Dependencies and relationships
- Installation history and updates
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .core import PluginManifest, PluginMetadata

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for managing plugin metadata and installation information.
    
    The registry maintains a persistent JSON database that stores:
    1. Plugin metadata (name, version, author, etc.)
    2. Installation information (path, install date, status)
    3. Dependency relationships between plugins
    4. Update history and version tracking
    
    This enables features like:
    - Listing installed plugins
    - Checking for conflicts and dependencies
    - Managing plugin updates
    - Tracking plugin usage and status
    """
    
    def __init__(self, registry_file: Path):
        """
        Initialize the plugin registry.
        
        Args:
            registry_file: Path to the registry JSON file
        """
        self.registry_file = registry_file
        self.registry_data: Dict[str, Any] = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'plugins': {},
            'index': {
                'by_type': {},
                'by_author': {},
                'by_provider': {},
                'dependencies': {}
            }
        }
        
        # Ensure registry directory exists
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing registry
        self._load_registry()
        
        logger.debug(f"PluginRegistry initialized with {len(self.registry_data['plugins'])} plugins")
    
    def _load_registry(self):
        """
        Load the registry from disk.
        
        This method safely loads the registry file, handling:
        1. Missing files (creates new registry)
        2. Corrupted JSON (backs up and creates new)
        3. Version migration (if registry format changes)
        """
        try:
            if self.registry_file.exists():
                registry_content = self.registry_file.read_text(encoding='utf-8')
                data = json.loads(registry_content)
                
                # Validate registry structure
                if self._validate_registry_structure(data):
                    self.registry_data = data
                    logger.debug(f"Loaded registry with {len(data.get('plugins', {}))} plugins")
                else:
                    logger.warning("Invalid registry structure, creating backup and starting fresh")
                    self._backup_registry()
                    self._save_registry()
            else:
                logger.info("No existing registry found, creating new one")
                self._save_registry()
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load registry: {e}")
            logger.info("Creating backup and starting with fresh registry")
            self._backup_registry()
            self._save_registry()
    
    def _validate_registry_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the registry has the expected structure.
        
        Args:
            data: Registry data to validate
            
        Returns:
            True if structure is valid, False otherwise
        """
        required_keys = ['version', 'plugins', 'index']
        return all(key in data for key in required_keys)
    
    def _backup_registry(self):
        """Create a backup of the current registry file."""
        if self.registry_file.exists():
            backup_file = self.registry_file.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            try:
                backup_file.write_text(self.registry_file.read_text())
                logger.info(f"Created registry backup at {backup_file}")
            except Exception as e:
                logger.error(f"Failed to create registry backup: {e}")
    
    def _save_registry(self):
        """
        Save the registry to disk.
        
        This method atomically saves the registry by:
        1. Writing to a temporary file first
        2. Moving the temporary file to the final location
        3. This prevents corruption if the process is interrupted
        """
        try:
            temp_file = self.registry_file.with_suffix('.tmp')
            
            registry_content = json.dumps(self.registry_data, indent=2, ensure_ascii=False)
            temp_file.write_text(registry_content, encoding='utf-8')
            
            # Atomic move to final location
            temp_file.replace(self.registry_file)
            
            logger.debug("Registry saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            raise
    
    async def register(self, manifest: PluginManifest, install_path: Path) -> bool:
        """
        Register a new plugin in the registry.
        
        This method:
        1. Validates the plugin manifest
        2. Checks for conflicts with existing plugins
        3. Adds the plugin to the registry
        4. Updates search indexes
        5. Saves the registry to disk
        
        Args:
            manifest: Plugin manifest
            install_path: Path where plugin is installed
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            plugin_name = manifest.metadata.name
            plugin_version = manifest.metadata.version
            
            logger.info(f"Registering plugin {plugin_name} v{plugin_version}")
            
            # Check if plugin already exists
            if plugin_name in self.registry_data['plugins']:
                existing = self.registry_data['plugins'][plugin_name]
                existing_version = existing['manifest']['metadata']['version']
                logger.warning(f"Plugin {plugin_name} already registered (v{existing_version})")
                
                # Compare versions
                if existing_version == plugin_version:
                    logger.info("Same version already registered, updating path")
                else:
                    logger.info(f"Updating from v{existing_version} to v{plugin_version}")
            
            # Create plugin entry
            plugin_entry = {
                'manifest': self._manifest_to_dict(manifest),
                'install_path': str(install_path),
                'installed_at': datetime.now().isoformat(),
                'status': 'installed',
                'enabled': True,
                'load_count': 0,
                'last_loaded': None,
                'errors': []
            }
            
            # Add to registry
            self.registry_data['plugins'][plugin_name] = plugin_entry
            
            # Update indexes
            self._update_indexes(manifest)
            
            # Save to disk
            self._save_registry()
            
            logger.info(f"Successfully registered plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            return False
    
    def _manifest_to_dict(self, manifest: PluginManifest) -> Dict[str, Any]:
        """
        Convert a PluginManifest to a dictionary for JSON storage.
        
        Args:
            manifest: Plugin manifest to convert
            
        Returns:
            Dictionary representation of the manifest
        """
        # Convert manifest to dictionary using dataclasses.asdict
        manifest_dict = asdict(manifest)
        
        # Convert enum to string
        manifest_dict['plugin_type'] = manifest.plugin_type.value
        
        # Convert datetime objects to ISO strings
        metadata = manifest_dict['metadata']
        if 'created_at' in metadata:
            metadata['created_at'] = metadata['created_at'].isoformat()
        if 'updated_at' in metadata:
            metadata['updated_at'] = metadata['updated_at'].isoformat()
        
        return manifest_dict
    
    def _update_indexes(self, manifest: PluginManifest):
        """
        Update search indexes when a plugin is registered.
        
        The indexes enable fast lookups by:
        - Plugin type (template, provider, etc.)
        - Author name
        - Supported cloud providers
        - Dependencies
        
        Args:
            manifest: Plugin manifest to index
        """
        plugin_name = manifest.metadata.name
        plugin_type = manifest.plugin_type.value
        author = manifest.metadata.author
        
        # Index by type
        if plugin_type not in self.registry_data['index']['by_type']:
            self.registry_data['index']['by_type'][plugin_type] = []
        if plugin_name not in self.registry_data['index']['by_type'][plugin_type]:
            self.registry_data['index']['by_type'][plugin_type].append(plugin_name)
        
        # Index by author
        if author not in self.registry_data['index']['by_author']:
            self.registry_data['index']['by_author'][author] = []
        if plugin_name not in self.registry_data['index']['by_author'][author]:
            self.registry_data['index']['by_author'][author].append(plugin_name)
        
        # Index by provider (based on keywords/categories)
        providers = []
        for keyword in manifest.metadata.keywords:
            if keyword.lower() in ['aws', 'azure', 'gcp', 'google', 'microsoft']:
                providers.append(keyword.lower())
        for category in manifest.metadata.categories:
            if category.lower() in ['aws', 'azure', 'gcp', 'google', 'microsoft']:
                providers.append(category.lower())
        
        for provider in providers:
            if provider not in self.registry_data['index']['by_provider']:
                self.registry_data['index']['by_provider'][provider] = []
            if plugin_name not in self.registry_data['index']['by_provider'][provider]:
                self.registry_data['index']['by_provider'][provider].append(plugin_name)
        
        # Index dependencies
        if manifest.metadata.dependencies:
            self.registry_data['index']['dependencies'][plugin_name] = manifest.metadata.dependencies
    
    async def unregister(self, plugin_name: str) -> bool:
        """
        Unregister a plugin from the registry.
        
        This method:
        1. Removes the plugin from the main registry
        2. Updates all search indexes
        3. Checks for dependent plugins and warns
        4. Saves the updated registry
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if plugin_name not in self.registry_data['plugins']:
                logger.warning(f"Plugin {plugin_name} not found in registry")
                return True
            
            logger.info(f"Unregistering plugin {plugin_name}")
            
            # Check for dependent plugins
            dependents = self._find_dependents(plugin_name)
            if dependents:
                logger.warning(f"Plugin {plugin_name} has dependents: {dependents}")
                # Could make this configurable to force removal or prevent it
            
            # Get plugin info before removal
            plugin_info = self.registry_data['plugins'][plugin_name]
            manifest_dict = plugin_info['manifest']
            
            # Remove from main registry
            del self.registry_data['plugins'][plugin_name]
            
            # Remove from indexes
            self._remove_from_indexes(plugin_name, manifest_dict)
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Successfully unregistered plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister plugin {plugin_name}: {e}")
            return False
    
    def _find_dependents(self, plugin_name: str) -> List[str]:
        """
        Find plugins that depend on the given plugin.
        
        Args:
            plugin_name: Name of plugin to check
            
        Returns:
            List of plugin names that depend on the given plugin
        """
        dependents = []
        
        for name, deps in self.registry_data['index']['dependencies'].items():
            if plugin_name in deps:
                dependents.append(name)
        
        return dependents
    
    def _remove_from_indexes(self, plugin_name: str, manifest_dict: Dict[str, Any]):
        """
        Remove a plugin from all search indexes.
        
        Args:
            plugin_name: Name of plugin to remove
            manifest_dict: Plugin manifest dictionary
        """
        # Remove from type index
        plugin_type = manifest_dict['plugin_type']
        if plugin_type in self.registry_data['index']['by_type']:
            if plugin_name in self.registry_data['index']['by_type'][plugin_type]:
                self.registry_data['index']['by_type'][plugin_type].remove(plugin_name)
        
        # Remove from author index
        author = manifest_dict['metadata']['author']
        if author in self.registry_data['index']['by_author']:
            if plugin_name in self.registry_data['index']['by_author'][author]:
                self.registry_data['index']['by_author'][author].remove(plugin_name)
        
        # Remove from provider indexes
        for provider_list in self.registry_data['index']['by_provider'].values():
            if plugin_name in provider_list:
                provider_list.remove(plugin_name)
        
        # Remove from dependencies
        if plugin_name in self.registry_data['index']['dependencies']:
            del self.registry_data['index']['dependencies'][plugin_name]
    
    async def get_plugin(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered plugin.
        
        Args:
            plugin_name: Name of plugin to get
            
        Returns:
            Plugin information dictionary, or None if not found
        """
        return self.registry_data['plugins'].get(plugin_name)
    
    async def list_plugins(self, 
                          plugin_type: Optional[str] = None,
                          author: Optional[str] = None,
                          provider: Optional[str] = None,
                          enabled_only: bool = False) -> List[str]:
        """
        List registered plugins with optional filtering.
        
        Args:
            plugin_type: Filter by plugin type
            author: Filter by author
            provider: Filter by supported provider
            enabled_only: Only return enabled plugins
            
        Returns:
            List of plugin names matching the criteria
        """
        plugins = []
        
        # Start with all plugins or filter by criteria
        if plugin_type:
            plugins = self.registry_data['index']['by_type'].get(plugin_type, [])
        elif author:
            plugins = self.registry_data['index']['by_author'].get(author, [])
        elif provider:
            plugins = self.registry_data['index']['by_provider'].get(provider.lower(), [])
        else:
            plugins = list(self.registry_data['plugins'].keys())
        
        # Apply enabled filter if requested
        if enabled_only:
            plugins = [
                name for name in plugins 
                if self.registry_data['plugins'][name].get('enabled', True)
            ]
        
        return plugins
    
    async def update_plugin_status(self, plugin_name: str, status: str, error: Optional[str] = None):
        """
        Update the status of a plugin in the registry.
        
        Args:
            plugin_name: Name of plugin to update
            status: New status (installed, loaded, active, error, etc.)
            error: Error message if status is 'error'
        """
        if plugin_name not in self.registry_data['plugins']:
            logger.warning(f"Plugin {plugin_name} not found in registry")
            return
        
        plugin_entry = self.registry_data['plugins'][plugin_name]
        plugin_entry['status'] = status
        
        if status == 'loaded':
            plugin_entry['load_count'] = plugin_entry.get('load_count', 0) + 1
            plugin_entry['last_loaded'] = datetime.now().isoformat()
        
        if error:
            if 'errors' not in plugin_entry:
                plugin_entry['errors'] = []
            plugin_entry['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'message': error
            })
        
        self._save_registry()
        logger.debug(f"Updated plugin {plugin_name} status to {status}")
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin in the registry."""
        if plugin_name not in self.registry_data['plugins']:
            return False
        
        self.registry_data['plugins'][plugin_name]['enabled'] = True
        self._save_registry()
        logger.info(f"Enabled plugin {plugin_name}")
        return True
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin in the registry."""
        if plugin_name not in self.registry_data['plugins']:
            return False
        
        self.registry_data['plugins'][plugin_name]['enabled'] = False
        self._save_registry()
        logger.info(f"Disabled plugin {plugin_name}")
        return True
    
    async def get_dependencies(self, plugin_name: str) -> List[str]:
        """
        Get the dependencies of a plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            List of dependency names
        """
        return self.registry_data['index']['dependencies'].get(plugin_name, [])
    
    async def get_dependents(self, plugin_name: str) -> List[str]:
        """
        Get plugins that depend on the given plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            List of dependent plugin names
        """
        return self._find_dependents(plugin_name)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the plugin registry.
        
        Returns:
            Dictionary with registry statistics
        """
        plugins = self.registry_data['plugins']
        
        stats = {
            'total_plugins': len(plugins),
            'enabled_plugins': len([p for p in plugins.values() if p.get('enabled', True)]),
            'plugins_by_type': {},
            'plugins_by_author': {},
            'total_load_count': sum(p.get('load_count', 0) for p in plugins.values()),
            'plugins_with_errors': len([p for p in plugins.values() if p.get('errors')])
        }
        
        # Count by type
        for plugin_type, plugin_list in self.registry_data['index']['by_type'].items():
            stats['plugins_by_type'][plugin_type] = len(plugin_list)
        
        # Count by author
        for author, plugin_list in self.registry_data['index']['by_author'].items():
            stats['plugins_by_author'][author] = len(plugin_list)
        
        return stats
    
    def export_registry(self, export_path: Path) -> bool:
        """
        Export the registry to a file for backup or migration.
        
        Args:
            export_path: Path to export the registry to
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            export_content = json.dumps(self.registry_data, indent=2, ensure_ascii=False)
            export_path.write_text(export_content, encoding='utf-8')
            
            logger.info(f"Registry exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export registry: {e}")
            return False 