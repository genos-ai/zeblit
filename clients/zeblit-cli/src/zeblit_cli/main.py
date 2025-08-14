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

console = Console()


def setup_logging(debug: bool = False, verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
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
    command_str = " ".join(command)
    from zeblit_cli.commands.container import run_command_cmd
    asyncio.run(run_command_cmd(command_str, working_dir))


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
        
    if debug_mode:
        # Show full traceback in debug mode
        import traceback
        console.print("[red]Error:[/red]", style="bold")
        console.print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    else:
        # Show user-friendly error message
        console.print(f"[red]Error:[/red] {exc_value}")
        console.print("[dim]Use --debug for more details[/dim]")
    
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
