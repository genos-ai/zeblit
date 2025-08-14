"""
Chat commands for agent interaction in Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial chat commands.
"""

import asyncio
import logging
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient, APIError

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def chat_commands():
    """Agent chat and interaction commands."""
    pass


@chat_commands.command("send")
@click.argument("message", nargs=-1, required=True)
@click.option("--agent", "-a", help="Target specific agent (default: DevManager)")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def send_message(message: tuple, agent: Optional[str], project: Optional[str]):
    """Send a message to project agents."""
    message_text = " ".join(message)
    asyncio.run(send_message_cmd(message_text, agent, project))


async def send_message_cmd(message: str, agent: Optional[str], project_id: Optional[str]):
    """Send message command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        # Require authentication
        await auth_manager.require_auth()
        
        # Use current project if none specified
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified and no current project set[/red]")
                console.print("Use: [bold]zeblit use <project-id>[/bold] or [bold]zeblit chat --project <project-id> <message>[/bold]")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Show thinking indicator
            console.print(f"💭 Sending to {agent or 'DevManager'}: [dim]{message[:100]}{'...' if len(message) > 100 else ''}[/dim]")
            
            with console.status("[bold blue]Agent is thinking..."):
                # Send message to agents
                response = await api_client.chat_with_agents(
                    project_id=project_id,
                    message=message,
                    target_agent=agent
                )
            
            # Display response
            await display_agent_response(response)
            
    except Exception as e:
        console.print(f"[red]Error sending message:[/red] {str(e)}")


async def display_agent_response(response: dict):
    """Display an agent response in a formatted way."""
    agent_type = response.get("agent_type", "Unknown")
    agent_response = response.get("response", "No response")
    timestamp = response.get("timestamp", "")
    
    # Format timestamp
    if timestamp:
        timestamp = timestamp.split("T")[1].split(".")[0] if "T" in timestamp else timestamp
    
    # Create panel with agent response
    panel_title = f"🤖 {agent_type}"
    if timestamp:
        panel_title += f" • {timestamp}"
    
    # Try to render as markdown if it looks like markdown
    if any(marker in agent_response for marker in ["**", "*", "`", "#", "-", "```"]):
        content = Markdown(agent_response)
    else:
        content = agent_response
    
    panel = Panel(
        content,
        title=panel_title,
        title_align="left",
        border_style="blue"
    )
    
    console.print(panel)
    
    # Show routing information if available
    routing = response.get("routing", {})
    if routing and settings.preferences.verbose_output:
        console.print(f"[dim]Routed via: {routing.get('path', 'direct')}[/dim]")


@chat_commands.command("history")
@click.option("--limit", "-l", default=10, help="Number of recent messages to show")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def chat_history(limit: int, project: Optional[str]):
    """Show recent chat history."""
    asyncio.run(chat_history_cmd(limit, project))


async def chat_history_cmd(limit: int, project_id: Optional[str]):
    """Chat history command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        # Require authentication
        await auth_manager.require_auth()
        
        # Use current project if none specified
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified and no current project set[/red]")
                console.print("Use: [bold]zeblit use <project-id>[/bold] first")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Get chat history
            history = await api_client.get_chat_history(project_id, limit)
            
            if not history:
                console.print("📝 No chat history found.")
                console.print("Start a conversation: [bold]zeblit chat 'Hello, what can you help me with?'[/bold]")
                return
            
            console.print(f"\n[bold]Chat History[/bold] (last {len(history)} messages)")
            console.print()
            
            # Display messages in chronological order
            for msg in reversed(history):
                sender = msg.get("sender", "Unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                
                # Format timestamp
                if timestamp:
                    time_str = timestamp.split("T")[1].split(".")[0] if "T" in timestamp else timestamp
                else:
                    time_str = ""
                
                # Determine sender style
                if sender.lower() == "user":
                    sender_style = "👤 [cyan]You[/cyan]"
                else:
                    sender_style = f"🤖 [blue]{sender}[/blue]"
                
                # Show message
                header = f"{sender_style}"
                if time_str:
                    header += f" [dim]• {time_str}[/dim]"
                
                console.print(header)
                
                # Truncate long messages in history view
                if len(content) > 200:
                    content = content[:200] + "..."
                
                console.print(f"  {content}")
                console.print()
            
    except Exception as e:
        console.print(f"[red]Error getting chat history:[/red] {str(e)}")


@chat_commands.command("agents")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def list_agents(project: Optional[str]):
    """Show available agents and their status."""
    asyncio.run(list_agents_cmd(project))


async def list_agents_cmd(project_id: Optional[str]):
    """List agents command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        # Require authentication
        await auth_manager.require_auth()
        
        # Use current project if none specified
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified and no current project set[/red]")
                console.print("Use: [bold]zeblit use <project-id>[/bold] first")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # This would call a hypothetical agents status endpoint
            # For now, show static information about available agents
            
            console.print(f"\n[bold]Available Agents[/bold]")
            
            agents = [
                {
                    "name": "DevManager", 
                    "role": "Development Manager", 
                    "description": "Routes requests and coordinates other agents",
                    "primary": True
                },
                {
                    "name": "Engineer", 
                    "role": "Software Engineer", 
                    "description": "Writes and reviews code, implements features",
                    "primary": False
                },
                {
                    "name": "Architect", 
                    "role": "System Architect", 
                    "description": "Designs system architecture and technical decisions",
                    "primary": False
                },
                {
                    "name": "ProductManager", 
                    "role": "Product Manager", 
                    "description": "Manages requirements and product decisions",
                    "primary": False
                },
                {
                    "name": "DataAnalyst", 
                    "role": "Data Analyst", 
                    "description": "Analyzes data and provides insights",
                    "primary": False
                },
                {
                    "name": "PlatformEngineer", 
                    "role": "Platform Engineer", 
                    "description": "Manages infrastructure and deployment",
                    "primary": False
                }
            ]
            
            table = Table()
            table.add_column("Agent", style="cyan")
            table.add_column("Role", style="green")
            table.add_column("Description", style="white")
            table.add_column("Access", justify="center")
            
            for agent in agents:
                access = "🎯 Primary" if agent["primary"] else "👥 Direct"
                
                table.add_row(
                    agent["name"],
                    agent["role"],
                    agent["description"],
                    access
                )
            
            console.print(table)
            
            console.print("\n💡 [bold]Usage:[/bold]")
            console.print("  • [bold]zeblit chat 'your message'[/bold] - Send to DevManager (recommended)")
            console.print("  • [bold]zeblit chat --agent Engineer 'your message'[/bold] - Send directly to specific agent")
            
            console.print("\n🎯 [bold]Tip:[/bold] Start with DevManager - they'll route your request to the right specialist!")
            
    except Exception as e:
        console.print(f"[red]Error listing agents:[/red] {str(e)}")


# Convenient alias for main chat command
@click.command()
@click.argument("message", nargs=-1, required=True)
@click.option("--agent", "-a", help="Target specific agent (default: DevManager)")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def chat_main(message: tuple, agent: Optional[str], project: Optional[str]):
    """Send a message to project agents (main chat command)."""
    message_text = " ".join(message)
    asyncio.run(send_message_cmd(message_text, agent, project))


# Add the main chat command to the chat group
chat_commands.add_command(chat_main, name="main")
