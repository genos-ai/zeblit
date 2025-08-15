"""
Main CLI entry point for Zeblit.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial CLI implementation.
"""

import asyncio
import logging
import sys
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from zeblit_cli.config.settings import get_settings, get_config_manager
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient
from zeblit_cli.commands.auth import auth_commands
from zeblit_cli.commands.project import project_commands
from zeblit_cli.commands.chat import chat_commands
from zeblit_cli.commands.container import container_commands
from zeblit_cli.commands.files import file_commands
from zeblit_cli.commands.console import console_commands
from zeblit_cli.commands.schedule import schedule_commands
from zeblit_cli.utils import (
    show_error, 
    show_warning, 
    show_success,
    project_id_completion,
    template_completion,
    setup_completion
)

console = Console()


def setup_logging(debug: bool = False, verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    
    # Create a separate console for logging to avoid Click conflicts
    from rich.console import Console
    log_console = Console(stderr=True)
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=log_console)]
    )
    
    # Reduce noise from dependencies
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, debug: bool, verbose: bool):
    """
    Zeblit CLI - Command-line client for the Zeblit AI Development Platform.
    
    A thin client that demonstrates backend-first architecture by consuming
    the unified Zeblit API with zero business logic in the client.
    
    Examples:
        zeblit auth login
        zeblit create my-app --template=python-web
        zeblit chat "Build a todo API"
        zeblit run "python main.py"
    """
    # Setup logging
    setup_logging(debug, verbose)
    
    # Load settings
    settings = get_settings()
    if debug:
        settings.debug = True
    if verbose:
        settings.preferences.verbose_output = True
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['settings'] = settings
    ctx.obj['debug'] = debug
    ctx.obj['verbose'] = verbose


# Add command groups
cli.add_command(auth_commands, name="auth")
cli.add_command(project_commands, name="project")
cli.add_command(chat_commands, name="chat") 
cli.add_command(container_commands, name="container")
cli.add_command(file_commands, name="files")
cli.add_command(console_commands, name="console")
cli.add_command(schedule_commands, name="schedule")


# Convenience aliases for common commands
@cli.command()
@click.argument("name")
@click.option("--template", "-t", help="Project template to use")
@click.option("--description", "-d", help="Project description")
@click.pass_context
def create(ctx, name: str, template: Optional[str], description: Optional[str]):
    """Create a new project (alias for 'project create')."""
    # Call the project create command
    from zeblit_cli.commands.project import create_project_cmd
    asyncio.run(create_project_cmd(name, template, description))


@cli.command()
@click.pass_context
def list(ctx):
    """List projects (alias for 'project list')."""
    from zeblit_cli.commands.project import list_projects_cmd
    asyncio.run(list_projects_cmd())


@cli.command()
@click.argument("project_id")
@click.pass_context
def use(ctx, project_id: str):
    """Set active project (alias for 'project use')."""
    from zeblit_cli.commands.project import use_project_cmd
    asyncio.run(use_project_cmd(project_id))


@cli.command()
@click.argument("command", nargs=-1, required=True)
@click.option("--working-dir", "-w", help="Working directory for command execution")
@click.pass_context
def run(ctx, command: tuple, working_dir: Optional[str]):
    """Execute command in project container (alias for 'container run')."""
    command_list = list(command)
    from zeblit_cli.commands.container import run_command_cmd
    asyncio.run(run_command_cmd(command_list, working_dir, None))


@cli.command()
@click.pass_context
def status(ctx):
    """Show current project and container status."""
    from zeblit_cli.commands.project import status_cmd
    asyncio.run(status_cmd())


@cli.command()
@click.pass_context
def logs(ctx):
    """Show recent container logs (alias for 'container logs')."""
    from zeblit_cli.commands.container import logs_cmd
    asyncio.run(logs_cmd())


@cli.command()
@click.option("--project", "-p", help="Project ID")
@click.pass_context
def console(ctx, project: Optional[str]):
    """Stream real-time console output (alias for 'console stream')."""
    from zeblit_cli.commands.console import stream_console_cmd
    asyncio.run(stream_console_cmd(project, follow=True))


@cli.command("setup-completion")
@click.pass_context
def setup_completion_cmd(ctx):
    """Setup tab completion for your shell."""
    if setup_completion():
        show_success("Tab completion has been set up successfully!")
    else:
        show_error("Failed to setup tab completion")


@cli.command("cache")
@click.option("--clear", is_flag=True, help="Clear all cached data")
@click.option("--stats", is_flag=True, help="Show cache statistics")
@click.option("--cleanup", is_flag=True, help="Remove expired cache entries")
@click.pass_context
def cache_cmd(ctx, clear: bool, stats: bool, cleanup: bool):
    """Manage offline cache."""
    from zeblit_cli.utils import api_cache
    
    if clear:
        if api_cache.cache.clear():
            show_success("Cache cleared successfully")
        else:
            show_error("Failed to clear cache")
    elif cleanup:
        api_cache.cleanup()
        show_success("Expired cache entries cleaned up")
    elif stats:
        api_cache.show_cache_info()
    else:
        # Show cache info by default
        api_cache.show_cache_info()


# Global error handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    
    try:
        settings = get_settings()
        debug_mode = settings.debug
    except:
        debug_mode = False
    
    # Import API error types
    try:
        from zeblit_cli.api.client import APIError
    except ImportError:
        APIError = None
    
    # Handle specific error types
    if APIError and isinstance(exc_value, APIError):
        if hasattr(exc_value, 'status_code') and exc_value.status_code:
            if exc_value.status_code == 401:
                show_error(
                    "Authentication failed",
                    "Your API key may be expired or invalid",
                    "Run 'zeblit auth login' to authenticate again"
                )
            elif exc_value.status_code == 403:
                show_error(
                    "Access denied",
                    str(exc_value),
                    "Check your permissions for this resource"
                )
            elif exc_value.status_code == 404:
                show_error(
                    "Resource not found",
                    str(exc_value),
                    "Check the resource ID and try again"
                )
            elif exc_value.status_code >= 500:
                show_error(
                    "Server error",
                    str(exc_value),
                    "The server is experiencing issues. Please try again later."
                )
            else:
                show_error(f"API Error ({exc_value.status_code})", str(exc_value))
        else:
            show_error("API Error", str(exc_value))
    elif issubclass(exc_type, ConnectionError):
        show_error(
            "Connection failed",
            "Unable to connect to the Zeblit server",
            "Check your internet connection and the server URL in config"
        )
    elif issubclass(exc_type, FileNotFoundError):
        show_error(
            "File not found",
            str(exc_value),
            "Check the file path and try again"
        )
    elif issubclass(exc_type, PermissionError):
        show_error(
            "Permission denied",
            str(exc_value),
            "Check file permissions or run with appropriate privileges"
        )
    else:
        # Generic error handling
        if debug_mode:
            # Show full traceback in debug mode
            import traceback
            console.print("[red]Error:[/red]", style="bold")
            console.print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        else:
            # Show user-friendly error message
            show_error(str(exc_value), suggestion="Use --debug for more details")
    
    sys.exit(1)


def main():
    """Main entry point."""
    # Set global exception handler
    sys.excepthook = handle_exception
    
    # Check for basic setup
    config_manager = get_config_manager()
    if not config_manager.config_exists():
        console.print(
            "[yellow]Welcome to Zeblit CLI![/yellow]\n"
            "First time setup: run '[bold]zeblit auth login[/bold]' to get started."
        )
    
    # Run CLI
    cli()


if __name__ == "__main__":
    main()
