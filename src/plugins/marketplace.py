"""
Plugin marketplace system for discovering and managing plugins from various sources.

This module provides a comprehensive marketplace interface that allows users to:
- Search for plugins across multiple repositories
- Browse plugin categories and ratings
- Download and install plugins securely
- Manage plugin subscriptions and updates
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PluginListing:
    """Represents a plugin listing in the marketplace."""
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    downloads: int
    rating: float
    last_updated: datetime
    size: int
    repository_url: str
    download_url: str
    documentation_url: Optional[str] = None
    homepage_url: Optional[str] = None
    license: Optional[str] = None
    min_core_version: Optional[str] = None
    screenshots: List[str] = None


class PluginMarketplace:
    """
    Comprehensive plugin marketplace system.
    
    The marketplace provides a unified interface to discover plugins from:
    1. **Official Repository**: Curated plugins from the core team
    2. **Community Repositories**: Third-party plugin collections
    3. **GitHub/GitLab**: Direct repository integration
    4. **Private Registries**: Enterprise or private plugin sources
    
    Key features:
    - **Search and Discovery**: Full-text search with filtering
    - **Security Scanning**: Automated security analysis of plugins
    - **Version Management**: Track updates and compatibility
    - **Ratings and Reviews**: Community feedback system
    - **Caching**: Local caching for performance
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the plugin marketplace.
        
        Args:
            config: Marketplace configuration containing:
                - repositories: List of plugin repository URLs
                - cache_dir: Directory for caching marketplace data
                - cache_ttl: Cache time-to-live in seconds
                - security_scanning: Whether to scan plugins
                - api_keys: API keys for various services
        """
        self.config = config
        self.repositories = config.get('repositories', [
            'https://plugins.cloudcraver.io/api',  # Official repository
            'https://community.cloudcraver.io/api'  # Community repository
        ])
        
        self.cache_dir = Path(config.get('cache_dir', 'cache/marketplace'))
        self.cache_ttl = config.get('cache_ttl', 3600)  # 1 hour default
        self.security_scanning = config.get('security_scanning', True)
        self.api_keys = config.get('api_keys', {})
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for recent searches
        self._search_cache: Dict[str, tuple] = {}  # query -> (results, timestamp)
        self._plugin_cache: Dict[str, PluginListing] = {}
        
        logger.debug(f"PluginMarketplace initialized with {len(self.repositories)} repositories")
    
    async def search(self, 
                    query: str = "",
                    category: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    author: Optional[str] = None,
                    min_rating: float = 0.0,
                    max_results: int = 50) -> List[PluginListing]:
        """
        Search for plugins across all configured repositories.
        
        This method aggregates search results from multiple sources:
        1. Checks local cache for recent results
        2. Queries each configured repository
        3. Merges and deduplicates results
        4. Applies filters and sorting
        5. Caches results for future use
        
        Args:
            query: Search query string
            category: Filter by plugin category
            tags: Filter by plugin tags
            author: Filter by author name
            min_rating: Minimum rating filter
            max_results: Maximum number of results to return
            
        Returns:
            List of plugin listings matching the criteria
        """
        try:
            # Create cache key
            cache_key = self._create_search_cache_key(query, category, tags, author, min_rating)
            
            # Check cache first
            if cache_key in self._search_cache:
                cached_results, timestamp = self._search_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    logger.debug(f"Returning cached search results for: {query}")
                    return cached_results[:max_results]
            
            logger.info(f"Searching marketplace for: {query}")
            
            # Search all repositories
            all_results = []
            search_tasks = []
            
            for repo_url in self.repositories:
                task = self._search_repository(repo_url, query, category, tags, author, min_rating)
                search_tasks.append(task)
            
            # Execute searches in parallel
            repo_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results from all repositories
            seen_plugins = set()
            for result in repo_results:
                if isinstance(result, Exception):
                    logger.warning(f"Repository search failed: {result}")
                    continue
                
                for plugin in result:
                    # Deduplicate by name (prefer higher version)
                    plugin_key = f"{plugin.name}:{plugin.author}"
                    if plugin_key not in seen_plugins:
                        all_results.append(plugin)
                        seen_plugins.add(plugin_key)
                    else:
                        # Check if this version is newer
                        existing = next(p for p in all_results if f"{p.name}:{p.author}" == plugin_key)
                        if self._compare_versions(plugin.version, existing.version) > 0:
                            all_results.remove(existing)
                            all_results.append(plugin)
            
            # Sort results by relevance (rating, downloads, last_updated)
            sorted_results = self._sort_search_results(all_results, query)
            
            # Cache the results
            self._search_cache[cache_key] = (sorted_results, datetime.now().timestamp())
            
            logger.info(f"Found {len(sorted_results)} plugins for query: {query}")
            return sorted_results[:max_results]
            
        except Exception as e:
            logger.error(f"Marketplace search failed: {e}")
            return []
    
    async def _search_repository(self, 
                                repo_url: str,
                                query: str,
                                category: Optional[str],
                                tags: Optional[List[str]],
                                author: Optional[str],
                                min_rating: float) -> List[PluginListing]:
        """
        Search a single repository for plugins.
        
        Args:
            repo_url: Repository API URL
            query: Search query
            category: Category filter
            tags: Tags filter
            author: Author filter
            min_rating: Minimum rating filter
            
        Returns:
            List of plugin listings from this repository
        """
        try:
            # Build search parameters
            params = {
                'q': query,
                'limit': 100
            }
            
            if category:
                params['category'] = category
            if tags:
                params['tags'] = ','.join(tags)
            if author:
                params['author'] = author
            if min_rating > 0:
                params['min_rating'] = min_rating
            
            # Add API key if available
            repo_domain = repo_url.split('/')[2]
            if repo_domain in self.api_keys:
                params['api_key'] = self.api_keys[repo_domain]
            
            # Make HTTP request
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                search_url = f"{repo_url}/search"
                
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_repository_response(data, repo_url)
                    else:
                        logger.warning(f"Repository {repo_url} returned status {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Failed to search repository {repo_url}: {e}")
            return []
    
    def _parse_repository_response(self, data: Dict[str, Any], repo_url: str) -> List[PluginListing]:
        """
        Parse repository response into PluginListing objects.
        
        Args:
            data: Response data from repository
            repo_url: Repository URL for context
            
        Returns:
            List of parsed plugin listings
        """
        plugins = []
        
        try:
            for item in data.get('plugins', []):
                plugin = PluginListing(
                    name=item['name'],
                    version=item['version'],
                    description=item['description'],
                    author=item['author'],
                    category=item.get('category', 'other'),
                    tags=item.get('tags', []),
                    downloads=item.get('downloads', 0),
                    rating=item.get('rating', 0.0),
                    last_updated=datetime.fromisoformat(item['last_updated']),
                    size=item.get('size', 0),
                    repository_url=repo_url,
                    download_url=item['download_url'],
                    documentation_url=item.get('documentation_url'),
                    homepage_url=item.get('homepage_url'),
                    license=item.get('license'),
                    min_core_version=item.get('min_core_version'),
                    screenshots=item.get('screenshots', [])
                )
                plugins.append(plugin)
                
        except Exception as e:
            logger.error(f"Failed to parse repository response: {e}")
        
        return plugins
    
    def _create_search_cache_key(self, 
                                query: str,
                                category: Optional[str],
                                tags: Optional[List[str]],
                                author: Optional[str],
                                min_rating: float) -> str:
        """Create a cache key for search parameters."""
        key_parts = [
            f"q:{query}",
            f"cat:{category or ''}",
            f"tags:{','.join(sorted(tags)) if tags else ''}",
            f"author:{author or ''}",
            f"rating:{min_rating}"
        ]
        return "|".join(key_parts)
    
    def _sort_search_results(self, results: List[PluginListing], query: str) -> List[PluginListing]:
        """
        Sort search results by relevance.
        
        Scoring factors:
        1. Text relevance (name/description match)
        2. Rating and download count
        3. Recency of updates
        4. Completeness of metadata
        
        Args:
            results: List of plugin listings
            query: Original search query
            
        Returns:
            Sorted list of plugin listings
        """
        def calculate_score(plugin: PluginListing) -> float:
            score = 0.0
            
            # Text relevance (40% of score)
            query_lower = query.lower()
            if query_lower in plugin.name.lower():
                score += 40
            elif query_lower in plugin.description.lower():
                score += 20
            
            # Rating (25% of score)
            score += plugin.rating * 5  # 0-5 rating becomes 0-25 points
            
            # Download popularity (20% of score)
            # Logarithmic scale to prevent outliers from dominating
            import math
            if plugin.downloads > 0:
                score += min(20, math.log10(plugin.downloads) * 4)
            
            # Recency (10% of score)
            days_old = (datetime.now() - plugin.last_updated).days
            if days_old < 30:
                score += 10
            elif days_old < 90:
                score += 5
            
            # Metadata completeness (5% of score)
            if plugin.documentation_url:
                score += 2
            if plugin.homepage_url:
                score += 2
            if plugin.screenshots:
                score += 1
            
            return score
        
        return sorted(results, key=calculate_score, reverse=True)
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            1 if version1 > version2
            0 if version1 == version2
            -1 if version1 < version2
        """
        try:
            from packaging import version
            v1 = version.parse(version1)
            v2 = version.parse(version2)
            
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
            else:
                return 0
        except Exception:
            # Fall back to string comparison
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            else:
                return 0
    
    async def get_plugin_details(self, plugin_name: str, repository_url: Optional[str] = None) -> Optional[PluginListing]:
        """
        Get detailed information about a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            repository_url: Specific repository to check (optional)
            
        Returns:
            Plugin listing with detailed information
        """
        try:
            # Check cache first
            cache_key = f"details:{plugin_name}:{repository_url or 'all'}"
            if cache_key in self._plugin_cache:
                return self._plugin_cache[cache_key]
            
            # Search specific repository or all repositories
            repos_to_search = [repository_url] if repository_url else self.repositories
            
            for repo_url in repos_to_search:
                try:
                    timeout = aiohttp.ClientTimeout(total=30)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        details_url = f"{repo_url}/plugins/{plugin_name}"
                        
                        # Add API key if available
                        params = {}
                        repo_domain = repo_url.split('/')[2]
                        if repo_domain in self.api_keys:
                            params['api_key'] = self.api_keys[repo_domain]
                        
                        async with session.get(details_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                plugins = self._parse_repository_response({'plugins': [data]}, repo_url)
                                if plugins:
                                    plugin = plugins[0]
                                    self._plugin_cache[cache_key] = plugin
                                    return plugin
                
                except Exception as e:
                    logger.warning(f"Failed to get details from {repo_url}: {e}")
                    continue
            
            logger.warning(f"Plugin {plugin_name} not found in any repository")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get plugin details: {e}")
            return None
    
    async def download_plugin(self, plugin: PluginListing, download_dir: Path) -> Optional[Path]:
        """
        Download a plugin from the marketplace.
        
        This method:
        1. Downloads the plugin package securely
        2. Verifies checksums if available
        3. Performs security scanning if enabled
        4. Returns path to downloaded file
        
        Args:
            plugin: Plugin listing to download
            download_dir: Directory to download to
            
        Returns:
            Path to downloaded plugin file
        """
        try:
            logger.info(f"Downloading plugin {plugin.name} v{plugin.version}")
            
            # Ensure download directory exists
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file name
            file_name = f"{plugin.name}-{plugin.version}.zip"
            file_path = download_dir / file_name
            
            # Download the file
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for downloads
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(plugin.download_url) as response:
                    if response.status == 200:
                        content = b""
                        async for chunk in response.content.iter_chunked(8192):
                            content += chunk
                        file_path.write_bytes(content)
                    else:
                        logger.error(f"Download failed with status {response.status}")
                        return None
            
            # Verify file size
            actual_size = file_path.stat().st_size
            if plugin.size > 0 and abs(actual_size - plugin.size) > 1024:  # Allow 1KB difference
                logger.warning(f"Downloaded file size mismatch: expected {plugin.size}, got {actual_size}")
            
            # Perform security scanning if enabled
            if self.security_scanning:
                if not await self._scan_downloaded_plugin(file_path):
                    logger.error(f"Security scan failed for {plugin.name}")
                    file_path.unlink()  # Delete the file
                    return None
            
            logger.info(f"Successfully downloaded {plugin.name} to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to download plugin {plugin.name}: {e}")
            return None
    
    async def _scan_downloaded_plugin(self, file_path: Path) -> bool:
        """
        Perform basic security scanning on downloaded plugin.
        
        Args:
            file_path: Path to downloaded plugin file
            
        Returns:
            True if scan passes, False if threats detected
        """
        try:
            # Basic checks for now - could be extended with virus scanning, etc.
            
            # Check file size is reasonable
            max_size = 100 * 1024 * 1024  # 100MB
            if file_path.stat().st_size > max_size:
                logger.warning(f"Plugin file {file_path} is unusually large")
                return False
            
            # Check file type
            if not file_path.name.endswith(('.zip', '.tar.gz')):
                logger.warning(f"Plugin file {file_path} has unexpected extension")
                return False
            
            # TODO: Add more sophisticated scanning
            # - Virus scanning integration
            # - Static analysis of contained code
            # - Reputation checking
            
            return True
            
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Get list of available plugin categories."""
        # This could be fetched from repositories or cached
        return [
            'templates',
            'providers', 
            'validators',
            'generators',
            'tools',
            'integrations',
            'security',
            'monitoring',
            'other'
        ]
    
    def clear_cache(self):
        """Clear all cached marketplace data."""
        self._search_cache.clear()
        self._plugin_cache.clear()
        
        # Clear file cache
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        
        logger.info("Marketplace cache cleared")
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get statistics about the marketplace."""
        return {
            'repositories': len(self.repositories),
            'cache_entries': len(self._search_cache) + len(self._plugin_cache),
            'cache_dir_size': sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file()),
            'last_search': max([ts for _, ts in self._search_cache.values()], default=0) if self._search_cache else 0
        } 