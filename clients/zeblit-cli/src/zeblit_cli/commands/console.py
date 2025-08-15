"""
Console and real-time output commands for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial console commands.
"""

import asyncio
import logging
from typing import Optional
import json

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient, APIError

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def console_commands():
    """Real-time console and output commands."""
    pass


@console_commands.command("stream")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
@click.option("--follow", "-f", is_flag=True, help="Follow the console output")
def stream_console(project: Optional[str], follow: bool):
    """Stream real-time console output from the container."""
    asyncio.run(stream_console_cmd(project, follow))


async def stream_console_cmd(project_id: Optional[str], follow: bool):
    """Stream console command implementation."""
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
            
            console.print("🔄 [blue]Connecting to console stream...[/blue]")
            console.print("Press [bold]Ctrl+C[/bold] to stop streaming")
            console.print()
            
            try:
                async for message in api_client.connect_console_websocket(project_id):
                    await handle_console_message(message)
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Stream stopped by user[/yellow]")
            except Exception as e:
                console.print(f"\n[red]Stream error:[/red] {str(e)}")
            
    except Exception as e:
        console.print(f"[red]Error starting console stream:[/red] {str(e)}")


async def handle_console_message(message: dict):
    """Handle incoming console message."""
    msg_type = message.get("type", "unknown")
    payload = message.get("payload", {})
    
    if msg_type == "console_output":
        # Console output message
        output_type = payload.get("type", "stdout")
        content = payload.get("content", "")
        timestamp = payload.get("timestamp", "")
        
        # Format timestamp
        if timestamp:
            time_str = timestamp.split("T")[1].split(".")[0] if "T" in timestamp else timestamp
        else:
            time_str = ""
        
        # Style based on output type
        if output_type == "stderr":
            style = "red"
            prefix = "❌"
        elif output_type == "stdout":
            style = "white"
            prefix = "📝"
        else:
            style = "dim"
            prefix = "ℹ️"
        
        # Display message
        if time_str:
            console.print(f"[dim]{time_str}[/dim] {prefix} [{style}]{content}[/{style}]")
        else:
            console.print(f"{prefix} [{style}]{content}[/{style}]")
    
    elif msg_type == "container_status":
        # Container status update
        status = payload.get("status", "unknown")
        
        if status == "started":
            console.print("🟢 [green]Container started[/green]")
        elif status == "stopped":
            console.print("🔴 [red]Container stopped[/red]")
        else:
            console.print(f"🟡 Container status: {status}")
    
    elif msg_type == "agent_activity":
        # Agent activity notification
        agent = payload.get("agent", "Unknown")
        activity = payload.get("activity", "")
        
        console.print(f"🤖 [blue]{agent}:[/blue] {activity}")
    
    elif msg_type == "error":
        # Error message
        error = payload.get("error", "Unknown error")
        console.print(f"❌ [red]Error:[/red] {error}")
    
    elif msg_type == "connected":
        # Connection confirmation
        console.print("✅ [green]Connected to console stream[/green]")
    
    else:
        # Unknown message type
        try:
            settings = get_settings()
            if settings.preferences.verbose_output:
                console.print(f"🔍 [dim]Unknown message: {msg_type}[/dim]")
        except:
            pass  # Ignore if settings unavailable


@console_commands.command("clear")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def clear_console(project: Optional[str]):
    """Clear the console output history."""
    asyncio.run(clear_console_cmd(project))


async def clear_console_cmd(project_id: Optional[str]):
    """Clear console command implementation."""
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
            
            # Call the console clear API
            response = await api_client._request("DELETE", f"/projects/{project_id}/console/clear")
            
            if response.get("success", True):
                console.print("🧹 [green]Console cleared successfully[/green]")
            else:
                console.print("[red]Failed to clear console[/red]")
            
    except Exception as e:
        console.print(f"[red]Error clearing console:[/red] {str(e)}")


@console_commands.command("history")
@click.option("--lines", "-n", default=100, help="Number of recent lines to show")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def console_history(lines: int, project: Optional[str]):
    """Show recent console output history."""
    asyncio.run(console_history_cmd(lines, project))


async def console_history_cmd(lines: int, project_id: Optional[str]):
    """Console history command implementation."""
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
            
            # Get container logs as console history
            result = await api_client.get_container_logs(project_id, lines)
            
            logs = result.get("logs", "")
            if logs:
                console.print(f"\n[bold]Console History[/bold] (last {lines} lines)")
                
                # Display logs with some formatting
                for line in logs.split('\n'):
                    if line.strip():
                        # Simple detection of error lines
                        if any(keyword in line.lower() for keyword in ['error', 'exception', 'traceback']):
                            console.print(f"❌ [red]{line}[/red]")
                        elif any(keyword in line.lower() for keyword in ['warning', 'warn']):
                            console.print(f"⚠️  [yellow]{line}[/yellow]")
                        else:
                            console.print(f"📝 {line}")
            else:
                console.print("📝 No console history available")
            
    except Exception as e:
        console.print(f"[red]Error getting console history:[/red] {str(e)}")


# Alias for the main stream command
@click.command()
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def console_main(project: Optional[str]):
    """Stream real-time console output (main console command)."""
    asyncio.run(stream_console_cmd(project, follow=True))


# Add the main console command
console_commands.add_command(console_main, name="main")
