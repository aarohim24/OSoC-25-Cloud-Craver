"""
Plugin discovery system for finding plugins in various locations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
import zipfile
import tarfile
from dataclasses import asdict

from .core import PluginManifest, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Discovers plugins from various sources."""
    
    def __init__(self, config: Dict[str, any]):
        """
        Initialize plugin discovery.
        
        Args:
            config: Discovery configuration
        """
        self.config = config
        self.search_paths = [
            Path("plugins"),
            Path("~/.cloudcraver/plugins").expanduser(),
            Path("/usr/local/share/cloudcraver/plugins"),
        ]
        
        # Add configured search paths
        if 'search_paths' in config:
            self.search_paths.extend([Path(p) for p in config['search_paths']])
        
        self.manifest_files = ['plugin.json', 'manifest.json', 'cloudcraver.json']
        self.package_extensions = ['.zip', '.tar.gz', '.tar.bz2', '.tar.xz']
        
    async def discover(self, additional_paths: Optional[List[Path]] = None) -> List[PluginManifest]:
        """
        Discover plugins from all configured paths.
        
        Args:
            additional_paths: Additional paths to search
            
        Returns:
            List of discovered plugin manifests
        """
        all_paths = self.search_paths.copy()
        if additional_paths:
            all_paths.extend(additional_paths)
        
        manifests = []
        seen_plugins = set()
        
        for search_path in all_paths:
            if not search_path.exists():
                continue
                
            logger.debug(f"Searching for plugins in: {search_path}")
            
            # Discover directory-based plugins
            for manifest in await self._discover_in_directory(search_path):
                plugin_key = f"{manifest.metadata.name}:{manifest.metadata.version}"
                if plugin_key not in seen_plugins:
                    manifests.append(manifest)
                    seen_plugins.add(plugin_key)
            
            # Discover packaged plugins
            for manifest in await self._discover_packages(search_path):
                plugin_key = f"{manifest.metadata.name}:{manifest.metadata.version}"
                if plugin_key not in seen_plugins:
                    manifests.append(manifest)
                    seen_plugins.add(plugin_key)
        
        logger.info(f"Discovered {len(manifests)} plugins")
        return manifests
    
    async def _discover_in_directory(self, base_path: Path) -> List[PluginManifest]:
        """Discover plugins in a directory structure."""
        manifests = []
        
        if not base_path.is_dir():
            return manifests
            
        # Look for manifest files in subdirectories
        for item in base_path.iterdir():
            if item.is_dir():
                manifest = await self._load_manifest_from_directory(item)
                if manifest:
                    manifests.append(manifest)
        
        return manifests
    
    async def _discover_packages(self, base_path: Path) -> List[PluginManifest]:
        """Discover plugins in package files."""
        manifests = []
        
        if not base_path.is_dir():
            return manifests
            
        for item in base_path.iterdir():
            if item.is_file() and any(item.name.endswith(ext) for ext in self.package_extensions):
                manifest = await self._load_manifest_from_package(item)
                if manifest:
                    manifests.append(manifest)
        
        return manifests
    
    async def _load_manifest_from_directory(self, plugin_dir: Path) -> Optional[PluginManifest]:
        """Load plugin manifest from a directory."""
        try:
            # Look for manifest files
            manifest_path = None
            for manifest_file in self.manifest_files:
                candidate = plugin_dir / manifest_file
                if candidate.exists():
                    manifest_path = candidate
                    break
            
            if not manifest_path:
                logger.debug(f"No manifest file found in {plugin_dir}")
                return None
            
            logger.debug(f"Found manifest file: {manifest_path}")
            
            # Use pathlib to read the file to avoid any open() conflicts
            manifest_content = manifest_path.read_text(encoding='utf-8')
            manifest_data = json.loads(manifest_content)
            
            return self._parse_manifest(manifest_data, str(plugin_dir))
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to load manifest from {plugin_dir}: {type(e).__name__}: {e}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None
    
    async def _load_manifest_from_package(self, package_path: Path) -> Optional[PluginManifest]:
        """Load plugin manifest from a package file."""
        try:
            manifest_data = None
            
            if package_path.suffix == '.zip':
                with zipfile.ZipFile(package_path, 'r') as zf:
                    for manifest_file in self.manifest_files:
                        try:
                            with zf.open(manifest_file) as f:
                                manifest_data = json.load(f)
                                break
                        except KeyError:
                            continue
            
            elif package_path.name.endswith(('.tar.gz', '.tar.bz2', '.tar.xz')):
                mode = 'r:gz' if package_path.name.endswith('.tar.gz') else \
                       'r:bz2' if package_path.name.endswith('.tar.bz2') else 'r:xz'
                
                with tarfile.open(package_path, mode) as tf:
                    for manifest_file in self.manifest_files:
                        try:
                            member = tf.getmember(manifest_file)
                            with tf.extractfile(member) as f:
                                manifest_data = json.load(f)
                                break
                        except KeyError:
                            continue
            
            if not manifest_data:
                logger.debug(f"No manifest found in package {package_path}")
                return None
            
            return self._parse_manifest(manifest_data, str(package_path))
            
        except Exception as e:
            logger.error(f"Failed to load manifest from package {package_path}: {e}")
            return None
    
    def _parse_manifest(self, data: Dict[str, any], source_path: str) -> Optional[PluginManifest]:
        """Parse manifest data into PluginManifest object."""
        try:
            # Validate required fields
            required_fields = ['name', 'version', 'description', 'author', 'type', 'main_class']
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in manifest from {source_path}")
                    return None
            
            # Parse metadata
            metadata = PluginMetadata(
                name=data['name'],
                version=data['version'],
                description=data['description'],
                author=data['author'],
                email=data.get('email'),
                homepage=data.get('homepage'),
                repository=data.get('repository'),
                license=data.get('license'),
                keywords=data.get('keywords', []),
                categories=data.get('categories', []),
                min_core_version=data.get('min_core_version'),
                max_core_version=data.get('max_core_version'),
                python_requires=data.get('python_requires'),
                dependencies=data.get('dependencies', []),
                optional_dependencies=data.get('optional_dependencies', {}),
                entry_points=data.get('entry_points', {}),
                config_schema=data.get('config_schema')
            )
            
            # Parse plugin type
            try:
                plugin_type = PluginType(data['type'])
            except ValueError:
                logger.error(f"Invalid plugin type '{data['type']}' in {source_path}")
                return None
            
            # Create manifest
            manifest = PluginManifest(
                metadata=metadata,
                plugin_type=plugin_type,
                main_class=data['main_class'],
                module_path=data.get('module_path', data['main_class']),
                config_file=data.get('config_file'),
                assets_dir=data.get('assets_dir'),
                docs_dir=data.get('docs_dir'),
                tests_dir=data.get('tests_dir'),
                permissions=data.get('permissions', []),
                hooks=data.get('hooks', []),
                provides=data.get('provides', []),
                requires=data.get('requires', [])
            )
            
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to parse manifest from {source_path}: {e}")
            return None
    
    async def discover_by_name(self, name: str) -> Optional[PluginManifest]:
        """Discover a specific plugin by name."""
        manifests = await self.discover()
        for manifest in manifests:
            if manifest.metadata.name == name:
                return manifest
        return None
    
    async def discover_by_type(self, plugin_type: PluginType) -> List[PluginManifest]:
        """Discover plugins of a specific type."""
        manifests = await self.discover()
        return [m for m in manifests if m.plugin_type == plugin_type]
    
    async def discover_by_provider(self, provider: str) -> List[PluginManifest]:
        """Discover plugins that support a specific provider."""
        manifests = await self.discover()
        provider_plugins = []
        
        for manifest in manifests:
            if provider.lower() in [k.lower() for k in manifest.metadata.keywords]:
                provider_plugins.append(manifest)
            elif provider.lower() in [c.lower() for c in manifest.metadata.categories]:
                provider_plugins.append(manifest)
        
        return provider_plugins
    
    def add_search_path(self, path: Path):
        """Add a new search path."""
        if path not in self.search_paths:
            self.search_paths.append(path)
            logger.info(f"Added search path: {path}")
    
    def remove_search_path(self, path: Path):
        """Remove a search path."""
        if path in self.search_paths:
            self.search_paths.remove(path)
            logger.info(f"Removed search path: {path}")
    
    def get_search_paths(self) -> List[Path]:
        """Get current search paths."""
        return self.search_paths.copy()
    
    async def validate_plugin_structure(self, plugin_path: Path) -> bool:
        """Validate plugin directory structure."""
        try:
            if not plugin_path.exists():
                return False
                
            # Check for manifest file
            has_manifest = any(
                (plugin_path / mf).exists() 
                for mf in self.manifest_files
            )
            
            if not has_manifest:
                return False
            
            # Load and validate manifest
            manifest = await self._load_manifest_from_directory(plugin_path)
            if not manifest:
                return False
            
            # Check if main module exists
            main_module_path = plugin_path / f"{manifest.module_path.replace('.', '/')}.py"
            if not main_module_path.exists():
                # Try alternative paths
                alt_paths = [
                    plugin_path / f"{manifest.module_path}.py",
                    plugin_path / "main.py",
                    plugin_path / "__init__.py"
                ]
                if not any(p.exists() for p in alt_paths):
                    logger.error(f"Main module not found for plugin {manifest.metadata.name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate plugin structure at {plugin_path}: {e}")
            return False 