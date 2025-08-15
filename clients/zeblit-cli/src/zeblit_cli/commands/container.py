"""
Container management commands for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial container commands.
"""

import asyncio
import logging
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient, APIError

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def container_commands():
    """Container management commands."""
    pass


@container_commands.command("start")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def start_container(project: Optional[str]):
    """Start the project container."""
    asyncio.run(start_container_cmd(project))


async def start_container_cmd(project_id: Optional[str]):
    """Start container command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified[/red]")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            console.print("🚀 Starting container...")
            result = await api_client.start_container(project_id)
            
            console.print("✅ [green]Container started successfully![/green]")
            if result.get("container_id"):
                console.print(f"Container ID: {result['container_id'][:12]}...")
            
    except Exception as e:
        console.print(f"[red]Error starting container:[/red] {str(e)}")


@container_commands.command("stop")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def stop_container(project: Optional[str]):
    """Stop the project container."""
    asyncio.run(stop_container_cmd(project))


async def stop_container_cmd(project_id: Optional[str]):
    """Stop container command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified[/red]")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            console.print("🛑 Stopping container...")
            await api_client.stop_container(project_id)
            
            console.print("✅ [green]Container stopped[/green]")
            
    except Exception as e:
        console.print(f"[red]Error stopping container:[/red] {str(e)}")


@container_commands.command("status")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def container_status(project: Optional[str]):
    """Check container status."""
    asyncio.run(container_status_cmd(project))


async def container_status_cmd(project_id: Optional[str]):
    """Container status command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified[/red]")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            status = await api_client.get_container_status(project_id)
            
            container_status = status.get("status", "unknown")
            if container_status == "running":
                console.print("🟢 [green]Container is running[/green]")
            elif container_status == "stopped":
                console.print("🔴 [red]Container is stopped[/red]")
            else:
                console.print(f"🟡 Container status: {container_status}")
            
            if status.get("container_id"):
                console.print(f"ID: {status['container_id'][:12]}...")
            
    except Exception as e:
        console.print(f"[red]Error getting container status:[/red] {str(e)}")


@container_commands.command("run")
@click.argument("command", nargs=-1, required=True)
@click.option("--working-dir", "-w", help="Working directory")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def run_command(command: tuple, working_dir: Optional[str], project: Optional[str]):
    """Execute a command in the container."""
    command_list = list(command)
    asyncio.run(run_command_cmd(command_list, working_dir, project))


async def run_command_cmd(command: list, working_dir: Optional[str], project_id: Optional[str]):
    """Run command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified[/red]")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            console.print(f"⚡ Executing: [bold]{' '.join(command)}[/bold]")
            
            result = await api_client.execute_command(project_id, command, working_dir)
            
            # Display output
            output = result.get("output", "")
            exit_code = result.get("exit_code", 0)
            
            if output:
                console.print("\n[bold]Output:[/bold]")
                console.print(output.rstrip())
            
            if exit_code == 0:
                console.print("✅ [green]Command completed successfully[/green]")
            else:
                console.print(f"❌ [red]Command failed with exit code {exit_code}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error executing command:[/red] {str(e)}")


@container_commands.command("logs")
@click.option("--lines", "-n", default=100, help="Number of log lines to show")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def container_logs(lines: int, project: Optional[str]):
    """Show container logs."""
    asyncio.run(logs_cmd(lines, project))


async def logs_cmd(lines: int = 100, project_id: Optional[str] = None):
    """Container logs command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified[/red]")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            result = await api_client.get_container_logs(project_id, lines)
            
            logs = result.get("logs", "")
            if logs:
                panel = Panel(
                    logs,
                    title="📋 Container Logs",
                    border_style="blue"
                )
                console.print(panel)
            else:
                console.print("📝 No logs available")
            
    except Exception as e:
        console.print(f"[red]Error getting logs:[/red] {str(e)}")
