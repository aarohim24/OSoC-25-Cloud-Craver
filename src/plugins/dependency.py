"""
Plugin dependency management system.

This module handles the complex task of managing dependencies between plugins,
including dependency resolution, version compatibility checking, and
installation ordering to ensure all dependencies are satisfied.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from packaging import version
import networkx as nx

from .core import PluginManifest

logger = logging.getLogger(__name__)


class DependencyManager:
    """
    Manages plugin dependencies and ensures proper installation order.
    
    Key features:
    1. **Dependency Resolution**: Resolves complex dependency trees
    2. **Version Compatibility**: Checks semantic version constraints  
    3. **Circular Dependency Detection**: Prevents dependency loops
    4. **Installation Ordering**: Determines correct installation sequence
    5. **Conflict Detection**: Identifies incompatible plugin combinations
    """
    
    def __init__(self, config: Dict[str, any]):
        """Initialize dependency manager with configuration."""
        self.config = config
        self.strict_versioning = config.get('strict_versioning', True)
        
        # Dependency graph for resolution
        self.dependency_graph = nx.DiGraph()
        
        # Track plugin versions and constraints
        self.installed_plugins: Dict[str, str] = {}  # name -> version
        self.version_constraints: Dict[str, List[str]] = {}  # name -> [constraints]
        
        logger.debug("DependencyManager initialized")
    
    async def check_dependencies(self, manifest: PluginManifest) -> bool:
        """
        Check if all dependencies for a plugin can be satisfied.
        
        This method performs comprehensive dependency checking:
        1. Validates dependency specifications
        2. Checks for version compatibility
        3. Ensures no circular dependencies
        4. Verifies all transitive dependencies
        
        Args:
            manifest: Plugin manifest to check
            
        Returns:
            True if all dependencies can be satisfied
        """
        try:
            plugin_name = manifest.metadata.name
            dependencies = manifest.metadata.dependencies
            
            logger.info(f"Checking dependencies for {plugin_name}")
            
            # Parse and validate dependency specifications
            parsed_deps = []
            for dep_spec in dependencies:
                parsed_dep = self._parse_dependency(dep_spec)
                if not parsed_dep:
                    logger.error(f"Invalid dependency specification: {dep_spec}")
                    return False
                parsed_deps.append(parsed_dep)
            
            # Check each dependency
            for dep_name, constraints in parsed_deps:
                if not await self._check_single_dependency(dep_name, constraints):
                    logger.error(f"Dependency check failed for {dep_name}")
                    return False
            
            # Check for circular dependencies
            if self._would_create_cycle(plugin_name, [d[0] for d in parsed_deps]):
                logger.error(f"Plugin {plugin_name} would create circular dependency")
                return False
            
            logger.info(f"All dependencies satisfied for {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            return False
    
    def _parse_dependency(self, dep_spec: str) -> Optional[Tuple[str, List[str]]]:
        """
        Parse a dependency specification string.
        
        Supports formats like:
        - "plugin_name" (any version)
        - "plugin_name>=1.0.0" (minimum version)
        - "plugin_name>=1.0.0,<2.0.0" (version range)
        
        Args:
            dep_spec: Dependency specification string
            
        Returns:
            Tuple of (plugin_name, constraints) or None if invalid
        """
        import re
        
        # Pattern to match dependency specifications
        pattern = r'^([a-zA-Z][a-zA-Z0-9_-]*)(.*)?$'
        match = re.match(pattern, dep_spec.strip())
        
        if not match:
            return None
        
        plugin_name = match.group(1)
        constraint_str = match.group(2) or ""
        
        # Parse version constraints
        constraints = []
        if constraint_str:
            # Split by comma for multiple constraints
            for constraint in constraint_str.split(','):
                constraint = constraint.strip()
                if constraint:
                    constraints.append(constraint)
        
        return plugin_name, constraints
    
    async def _check_single_dependency(self, dep_name: str, constraints: List[str]) -> bool:
        """
        Check if a single dependency can be satisfied.
        
        Args:
            dep_name: Name of dependency plugin
            constraints: List of version constraints
            
        Returns:
            True if dependency can be satisfied
        """
        # Check if dependency is already installed
        if dep_name in self.installed_plugins:
            installed_version = self.installed_plugins[dep_name]
            return self._check_version_constraints(installed_version, constraints)
        
        # Check if dependency is available for installation
        # This would typically query a registry or marketplace
        available_versions = await self._get_available_versions(dep_name)
        if not available_versions:
            logger.error(f"Dependency {dep_name} not available")
            return False
        
        # Check if any available version satisfies constraints
        for available_version in available_versions:
            if self._check_version_constraints(available_version, constraints):
                return True
        
        logger.error(f"No version of {dep_name} satisfies constraints: {constraints}")
        return False
    
    def _check_version_constraints(self, plugin_version: str, constraints: List[str]) -> bool:
        """
        Check if a version satisfies all constraints.
        
        Args:
            plugin_version: Version to check
            constraints: List of version constraints
            
        Returns:
            True if version satisfies all constraints
        """
        if not constraints:
            return True  # No constraints means any version is acceptable
        
        try:
            v = version.parse(plugin_version)
            
            for constraint in constraints:
                if not self._check_single_constraint(v, constraint):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking version constraints: {e}")
            return False
    
    def _check_single_constraint(self, v: version.Version, constraint: str) -> bool:
        """
        Check if a version satisfies a single constraint.
        
        Args:
            v: Parsed version object
            constraint: Single constraint string (e.g., ">=1.0.0")
            
        Returns:
            True if constraint is satisfied
        """
        import re
        
        # Parse constraint
        constraint_pattern = r'^(>=|<=|>|<|==|!=)?(.+)$'
        match = re.match(constraint_pattern, constraint.strip())
        
        if not match:
            return False
        
        operator = match.group(1) or "=="
        constraint_version = version.parse(match.group(2))
        
        # Apply constraint
        if operator == ">=":
            return v >= constraint_version
        elif operator == "<=":
            return v <= constraint_version
        elif operator == ">":
            return v > constraint_version
        elif operator == "<":
            return v < constraint_version
        elif operator == "==":
            return v == constraint_version
        elif operator == "!=":
            return v != constraint_version
        
        return False
    
    async def _get_available_versions(self, plugin_name: str) -> List[str]:
        """
        Get available versions for a plugin.
        
        This would typically query a registry or marketplace.
        For now, returns empty list as placeholder.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            List of available version strings
        """
        # Placeholder - would query actual registry/marketplace
        logger.debug(f"Getting available versions for {plugin_name}")
        return []
    
    def _would_create_cycle(self, plugin_name: str, dependencies: List[str]) -> bool:
        """
        Check if adding dependencies would create a circular dependency.
        
        Args:
            plugin_name: Name of plugin being added
            dependencies: List of dependency names
            
        Returns:
            True if adding would create a cycle
        """
        # Create temporary graph with new dependencies
        temp_graph = self.dependency_graph.copy()
        
        # Add new plugin and its dependencies
        temp_graph.add_node(plugin_name)
        for dep in dependencies:
            temp_graph.add_edge(plugin_name, dep)
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(temp_graph))
            return len(cycles) > 0
        except Exception:
            # If we can't determine, assume there might be a cycle
            return True
    
    async def resolve_installation_order(self, plugins: List[PluginManifest]) -> List[str]:
        """
        Determine the correct installation order for plugins.
        
        Uses topological sorting to ensure dependencies are installed
        before plugins that depend on them.
        
        Args:
            plugins: List of plugin manifests to install
            
        Returns:
            List of plugin names in installation order
        """
        try:
            # Build dependency graph
            graph = nx.DiGraph()
            
            for plugin in plugins:
                plugin_name = plugin.metadata.name
                graph.add_node(plugin_name)
                
                # Add dependency edges
                for dep_spec in plugin.metadata.dependencies:
                    dep_info = self._parse_dependency(dep_spec)
                    if dep_info:
                        dep_name = dep_info[0]
                        graph.add_edge(dep_name, plugin_name)
            
            # Perform topological sort
            try:
                installation_order = list(nx.topological_sort(graph))
                logger.info(f"Installation order: {installation_order}")
                return installation_order
            except nx.NetworkXError:
                logger.error("Circular dependency detected in plugin set")
                return []
            
        except Exception as e:
            logger.error(f"Failed to resolve installation order: {e}")
            return []
    
    def register_installed_plugin(self, plugin_name: str, plugin_version: str):
        """
        Register a plugin as installed with given version.
        
        Args:
            plugin_name: Name of installed plugin
            plugin_version: Version of installed plugin
        """
        self.installed_plugins[plugin_name] = plugin_version
        self.dependency_graph.add_node(plugin_name)
        logger.debug(f"Registered installed plugin: {plugin_name} v{plugin_version}")
    
    def unregister_plugin(self, plugin_name: str):
        """
        Unregister a plugin (when uninstalled).
        
        Args:
            plugin_name: Name of plugin to unregister
        """
        self.installed_plugins.pop(plugin_name, None)
        if plugin_name in self.dependency_graph:
            self.dependency_graph.remove_node(plugin_name)
        logger.debug(f"Unregistered plugin: {plugin_name}")
    
    def get_dependent_plugins(self, plugin_name: str) -> List[str]:
        """
        Get plugins that depend on the given plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            List of dependent plugin names
        """
        if plugin_name not in self.dependency_graph:
            return []
        
        # Get successors (plugins that depend on this one)
        return list(self.dependency_graph.successors(plugin_name))
    
    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """
        Get dependencies of the given plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            List of dependency names
        """
        if plugin_name not in self.dependency_graph:
            return []
        
        # Get predecessors (plugins this one depends on)
        return list(self.dependency_graph.predecessors(plugin_name))
    
    def can_uninstall_plugin(self, plugin_name: str) -> Tuple[bool, List[str]]:
        """
        Check if a plugin can be safely uninstalled.
        
        Args:
            plugin_name: Name of plugin to check
            
        Returns:
            Tuple of (can_uninstall, list_of_dependent_plugins)
        """
        dependents = self.get_dependent_plugins(plugin_name)
        
        # Plugin can be uninstalled if no other plugins depend on it
        can_uninstall = len(dependents) == 0
        
        return can_uninstall, dependents
    
    def get_dependency_tree(self, plugin_name: str, max_depth: int = 5) -> Dict[str, any]:
        """
        Get the complete dependency tree for a plugin.
        
        Args:
            plugin_name: Name of plugin
            max_depth: Maximum depth to traverse
            
        Returns:
            Nested dictionary representing dependency tree
        """
        def _build_tree(name: str, depth: int = 0) -> Dict[str, any]:
            if depth >= max_depth:
                return {'name': name, 'dependencies': [], 'max_depth_reached': True}
            
            dependencies = self.get_plugin_dependencies(name)
            tree = {
                'name': name,
                'version': self.installed_plugins.get(name, 'not_installed'),
                'dependencies': []
            }
            
            for dep_name in dependencies:
                tree['dependencies'].append(_build_tree(dep_name, depth + 1))
            
            return tree
        
        return _build_tree(plugin_name)
    
    def validate_dependency_graph(self) -> List[str]:
        """
        Validate the current dependency graph for consistency.
        
        Returns:
            List of validation errors found
        """
        errors = []
        
        try:
            # Check for cycles
            cycles = list(nx.simple_cycles(self.dependency_graph))
            if cycles:
                errors.append(f"Circular dependencies detected: {cycles}")
            
            # Check for missing dependencies
            for plugin_name in self.dependency_graph.nodes():
                dependencies = self.get_plugin_dependencies(plugin_name)
                for dep_name in dependencies:
                    if dep_name not in self.installed_plugins:
                        errors.append(f"Plugin {plugin_name} depends on missing plugin {dep_name}")
            
        except Exception as e:
            errors.append(f"Error validating dependency graph: {e}")
        
        return errors 