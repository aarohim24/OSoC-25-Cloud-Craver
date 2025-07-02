"""
CLI commands for plugin management.

This module provides command-line interface for all plugin operations
including installation, management, and marketplace interactions.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich import print as rich_print

try:
    from plugins.core import PluginManager
    from plugins.core import PluginType
except ImportError:
    # Handle case where plugins module is not available
    PluginManager = None
    PluginType = None

# For now, create a simple CLI config getter
def get_cli_manager():
    """Simple CLI manager for plugin commands."""
    return {}

logger = logging.getLogger(__name__)
console = Console()


@click.group('plugin')
@click.pass_context
def plugin_cli(ctx):
    """Plugin management commands."""
    if PluginManager is None:
        raise click.ClickException("Plugin system not available")
    
    # Get plugin configuration
    plugin_config = {
        'discovery': {'search_paths': ['plugins', str(Path.home() / '.cloudcraver' / 'plugins')]},
        'loader': {'isolation': True, 'temp_dir': str(Path.home() / '.cloudcraver' / 'cache' / 'temp')},
        'validator': {'strict_mode': False},
        'security': {'enabled': True, 'max_cpu_time': 30},
        'dependencies': {'strict_versioning': True},
        'marketplace': {'repositories': ['https://plugins.cloudcraver.io/api']},
        'versioning': {'auto_update': False}
    }
    
    data_dir = Path.home() / '.cloudcraver'
    cache_dir = Path.home() / '.cloudcraver' / 'cache'
    
    # Ensure directories exist
    data_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / 'temp').mkdir(exist_ok=True)
    
    ctx.ensure_object(dict)
    ctx.obj['plugin_manager'] = PluginManager(plugin_config, data_dir, cache_dir)


@plugin_cli.command('list')
@click.option('--type', 'plugin_type', type=click.Choice(['template', 'provider', 'validator', 'generator', 'hook', 'extension']),
              help='Filter by plugin type')
@click.option('--enabled-only', is_flag=True, help='Show only enabled plugins')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def list_plugins(ctx, plugin_type: Optional[str], enabled_only: bool, output_format: str):
    """List installed plugins."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _list_plugins():
        try:
            # Get registry for listing plugins
            plugins = await plugin_manager.registry.list_plugins(
                plugin_type=plugin_type,
                enabled_only=enabled_only
            )
            
            if output_format == 'json':
                plugin_data = []
                for plugin_name in plugins:
                    plugin_info = await plugin_manager.registry.get_plugin(plugin_name)
                    if plugin_info:
                        plugin_data.append({
                            'name': plugin_name,
                            'version': plugin_info['manifest']['metadata']['version'],
                            'type': plugin_info['manifest']['plugin_type'],
                            'enabled': plugin_info['enabled'],
                            'status': plugin_info['status']
                        })
                
                rich_print(json.dumps(plugin_data, indent=2))
            else:
                # Create rich table
                table = Table(title="Installed Plugins")
                table.add_column("Name", style="cyan")
                table.add_column("Version", style="magenta")
                table.add_column("Type", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Enabled", style="blue")
                
                for plugin_name in plugins:
                    plugin_info = await plugin_manager.registry.get_plugin(plugin_name)
                    if plugin_info:
                        manifest = plugin_info['manifest']
                        table.add_row(
                            plugin_name,
                            manifest['metadata']['version'],
                            manifest['plugin_type'],
                            plugin_info['status'],
                            "✓" if plugin_info['enabled'] else "✗"
                        )
                
                console.print(table)
                
        except Exception as e:
            console.print(f"[red]Error listing plugins: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_list_plugins())


@plugin_cli.command('install')
@click.argument('source', type=str)
@click.option('--force', is_flag=True, help='Force installation (overwrite existing)')
@click.option('--no-deps', is_flag=True, help='Skip dependency installation')
@click.pass_context
def install_plugin(ctx, source: str, force: bool, no_deps: bool):
    """Install a plugin from various sources."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _install_plugin():
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Installing plugin...", total=100)
                
                progress.update(task, advance=20)
                console.print(f"[cyan]Installing plugin from: {source}[/cyan]")
                
                # Install plugin
                progress.update(task, advance=40)
                plugin_name = await plugin_manager.install_plugin(source, force)
                
                if plugin_name:
                    progress.update(task, advance=40)
                    console.print("[green]✓ Plugin installed successfully[/green]")
                    
                    # Load the plugin using the actual plugin name from manifest
                    if await plugin_manager.load_plugin(plugin_name):
                        console.print("[green]✓ Plugin loaded and activated[/green]")
                    else:
                        console.print("[yellow]⚠ Plugin installed but failed to load[/yellow]")
                else:
                    console.print("[red]✗ Plugin installation failed[/red]")
                    raise click.ClickException("Installation failed")
                    
        except Exception as e:
            console.print(f"[red]Error installing plugin: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_install_plugin())


@plugin_cli.command('uninstall')
@click.argument('plugin_name', type=str)
@click.option('--force', is_flag=True, help='Force uninstallation')
@click.pass_context
def uninstall_plugin(ctx, plugin_name: str, force: bool):
    """Uninstall a plugin."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _uninstall_plugin():
        try:
            # Check if plugin has dependents
            dependents = await plugin_manager.dependency_manager.get_dependent_plugins(plugin_name)
            if dependents and not force:
                console.print(f"[yellow]Plugin {plugin_name} has dependents: {', '.join(dependents)}[/yellow]")
                console.print("[yellow]Use --force to uninstall anyway[/yellow]")
                return
            
            # Unload plugin first
            if await plugin_manager.unload_plugin(plugin_name):
                console.print(f"[cyan]Plugin {plugin_name} unloaded[/cyan]")
            
            # Unregister from registry
            if await plugin_manager.registry.unregister(plugin_name):
                console.print(f"[green]✓ Plugin {plugin_name} uninstalled successfully[/green]")
            else:
                console.print(f"[red]✗ Failed to uninstall plugin {plugin_name}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error uninstalling plugin: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_uninstall_plugin())


@plugin_cli.command('enable')
@click.argument('plugin_name', type=str)
@click.pass_context
def enable_plugin(ctx, plugin_name: str):
    """Enable a plugin."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _enable_plugin():
        try:
            if await plugin_manager.registry.enable_plugin(plugin_name):
                console.print(f"[green]✓ Plugin {plugin_name} enabled[/green]")
                
                # Try to load the plugin
                if await plugin_manager.load_plugin(plugin_name):
                    console.print(f"[green]✓ Plugin {plugin_name} loaded[/green]")
            else:
                console.print(f"[red]✗ Failed to enable plugin {plugin_name}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error enabling plugin: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_enable_plugin())


@plugin_cli.command('disable')
@click.argument('plugin_name', type=str)
@click.pass_context
def disable_plugin(ctx, plugin_name: str):
    """Disable a plugin."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _disable_plugin():
        try:
            # Unload plugin first
            await plugin_manager.unload_plugin(plugin_name)
            
            if await plugin_manager.registry.disable_plugin(plugin_name):
                console.print(f"[green]✓ Plugin {plugin_name} disabled[/green]")
            else:
                console.print(f"[red]✗ Failed to disable plugin {plugin_name}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error disabling plugin: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_disable_plugin())


@plugin_cli.command('search')
@click.argument('query', type=str)
@click.option('--category', help='Filter by category')
@click.option('--type', 'plugin_type', help='Filter by plugin type')
@click.option('--limit', type=int, default=20, help='Maximum number of results')
@click.pass_context
def search_marketplace(ctx, query: str, category: Optional[str], plugin_type: Optional[str], limit: int):
    """Search the plugin marketplace."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _search_marketplace():
        try:
            console.print(f"[cyan]Searching marketplace for: {query}[/cyan]")
            
            # Search marketplace
            results = await plugin_manager.search_marketplace(query)
            
            if not results:
                console.print("[yellow]No plugins found[/yellow]")
                return
            
            # Create results table
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="magenta")
            table.add_column("Author", style="green")
            table.add_column("Description", style="white")
            table.add_column("Downloads", style="yellow")
            
            for result in results[:limit]:
                # Simplified result structure for demonstration
                table.add_row(
                    result.get('name', 'Unknown'),
                    result.get('version', 'Unknown'),
                    result.get('author', 'Unknown'),
                    result.get('description', 'No description')[:50] + "...",
                    str(result.get('downloads', 0))
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error searching marketplace: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_search_marketplace())


@plugin_cli.command('info')
@click.argument('plugin_name', type=str)
@click.pass_context
def plugin_info(ctx, plugin_name: str):
    """Show detailed information about a plugin."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _plugin_info():
        try:
            plugin_info = await plugin_manager.registry.get_plugin(plugin_name)
            
            if not plugin_info:
                console.print(f"[red]Plugin {plugin_name} not found[/red]")
                return
            
            manifest = plugin_info['manifest']
            metadata = manifest['metadata']
            
            # Create info display
            console.print(f"\n[bold cyan]{metadata['name']}[/bold cyan] v{metadata['version']}")
            console.print(f"[dim]{metadata['description']}[/dim]\n")
            
            console.print(f"[bold]Author:[/bold] {metadata['author']}")
            if metadata.get('email'):
                console.print(f"[bold]Email:[/bold] {metadata['email']}")
            if metadata.get('license'):
                console.print(f"[bold]License:[/bold] {metadata['license']}")
            
            console.print(f"[bold]Type:[/bold] {manifest['plugin_type']}")
            console.print(f"[bold]Status:[/bold] {plugin_info['status']}")
            console.print(f"[bold]Enabled:[/bold] {'Yes' if plugin_info['enabled'] else 'No'}")
            
            if metadata.get('keywords'):
                console.print(f"[bold]Keywords:[/bold] {', '.join(metadata['keywords'])}")
            
            if metadata.get('dependencies'):
                console.print(f"[bold]Dependencies:[/bold] {', '.join(metadata['dependencies'])}")
            
            console.print(f"[bold]Install Path:[/bold] {plugin_info['install_path']}")
            console.print(f"[bold]Installed:[/bold] {plugin_info['installed_at']}")
            
            if plugin_info.get('errors'):
                console.print(f"\n[bold red]Errors:[/bold red]")
                for error in plugin_info['errors']:
                    console.print(f"  [red]• {error['message']}[/red]")
                    
        except Exception as e:
            console.print(f"[red]Error getting plugin info: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_plugin_info())


@plugin_cli.command('status')
@click.pass_context
def plugin_status(ctx):
    """Show plugin system status."""
    plugin_manager = ctx.obj['plugin_manager']
    
    try:
        status = plugin_manager.get_status()
        
        console.print("[bold cyan]Plugin System Status[/bold cyan]\n")
        
        console.print(f"[bold]Total Plugins:[/bold] {status['total_plugins']}")
        console.print(f"[bold]Active Plugins:[/bold] {status['active_plugins']}")
        
        console.print("\n[bold]Plugins by Type:[/bold]")
        for plugin_type, count in status['plugins_by_type'].items():
            if count > 0:
                console.print(f"  {plugin_type}: {count}")
        
        if status['plugins']:
            console.print("\n[bold]Plugin Details:[/bold]")
            for name, info in status['plugins'].items():
                status_color = "green" if info['enabled'] else "yellow"
                console.print(f"  [{status_color}]{name}[/{status_color}] v{info['version']} ({info['stage']})")
                if info['error']:
                    console.print(f"    [red]Error: {info['error']}[/red]")
                    
    except Exception as e:
        console.print(f"[red]Error getting plugin status: {e}[/red]")
        raise click.ClickException(str(e))


@plugin_cli.command('validate')
@click.argument('plugin_path', type=click.Path(exists=True))
@click.pass_context
def validate_plugin(ctx, plugin_path: str):
    """Validate a plugin package."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _validate_plugin():
        try:
            console.print(f"[cyan]Validating plugin: {plugin_path}[/cyan]")
            
            manifest = await plugin_manager.validator.validate_plugin_package(plugin_path)
            
            if manifest:
                console.print("[green]✓ Plugin validation passed[/green]")
                console.print(f"[bold]Plugin:[/bold] {manifest.metadata.name} v{manifest.metadata.version}")
                console.print(f"[bold]Type:[/bold] {manifest.plugin_type.value}")
                console.print(f"[bold]Author:[/bold] {manifest.metadata.author}")
            else:
                console.print("[red]✗ Plugin validation failed[/red]")
                
        except Exception as e:
            console.print(f"[red]Error validating plugin: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_validate_plugin())


@plugin_cli.command('update')
@click.argument('plugin_name', type=str, required=False)
@click.option('--all', is_flag=True, help='Update all plugins')
@click.option('--check-only', is_flag=True, help='Only check for updates')
@click.pass_context
def update_plugin(ctx, plugin_name: Optional[str], all: bool, check_only: bool):
    """Update plugins to latest versions."""
    plugin_manager = ctx.obj['plugin_manager']
    
    async def _update_plugin():
        try:
            if check_only:
                # Check for updates
                if all:
                    updates = await plugin_manager.check_updates()
                else:
                    updates = await plugin_manager.check_updates([plugin_name] if plugin_name else [])
                
                if updates:
                    console.print("[bold cyan]Available Updates:[/bold cyan]")
                    for name, version in updates.items():
                        console.print(f"  {name}: {version}")
                else:
                    console.print("[green]All plugins are up to date[/green]")
            else:
                # Perform updates
                if all:
                    console.print("[cyan]Updating all plugins...[/cyan]")
                    # Implementation would iterate through all plugins
                elif plugin_name:
                    console.print(f"[cyan]Updating plugin: {plugin_name}[/cyan]")
                    success = await plugin_manager.update_plugin(plugin_name)
                    if success:
                        console.print(f"[green]✓ Plugin {plugin_name} updated successfully[/green]")
                    else:
                        console.print(f"[red]✗ Failed to update plugin {plugin_name}[/red]")
                else:
                    console.print("[red]Please specify a plugin name or use --all[/red]")
                    
        except Exception as e:
            console.print(f"[red]Error updating plugin: {e}[/red]")
            raise click.ClickException(str(e))
    
    asyncio.run(_update_plugin())


# Integration with main CLI
def add_plugin_commands(main_cli):
    """Add plugin commands to the main CLI."""
    main_cli.add_command(plugin_cli) 