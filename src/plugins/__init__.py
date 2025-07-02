"""
Cloud Craver Plugin System

This module provides a comprehensive plugin system for extending Cloud Craver
with custom templates, providers, and functionality.
"""

from .core import (
    PluginManager,
    Plugin,
    PluginInterface,
    PluginLifecycleStage,
    PluginType
)
from .discovery import PluginDiscovery
from .loader import PluginLoader
from .registry import PluginRegistry
from .validator import PluginValidator
from .security import PluginSandbox
from .dependency import DependencyManager
from .marketplace import PluginMarketplace
from .versioning import VersionManager

__all__ = [
    'PluginManager',
    'Plugin',
    'PluginInterface', 
    'PluginLifecycleStage',
    'PluginType',
    'PluginDiscovery',
    'PluginLoader',
    'PluginRegistry',
    'PluginValidator',
    'PluginSandbox',
    'DependencyManager',
    'PluginMarketplace',
    'VersionManager'
]

__version__ = '1.0.0' 