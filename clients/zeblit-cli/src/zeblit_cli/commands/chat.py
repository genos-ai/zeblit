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
import time

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


async def retry_with_timeout(func, max_retries=2, timeout_increase=30):
    """
    Retry a function with increasing timeouts and user feedback.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        timeout_increase: Additional seconds to add per retry
    """
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                console.print(f"[yellow]⏱️  Request timed out. Retrying (attempt {attempt + 1}/{max_retries + 1}) with longer timeout...[/yellow]")
            
            return await func()
            
        except APIError as e:
            error_msg = str(e)
            
            # Handle timeout errors
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    console.print(f"[yellow]⏳ Waiting {wait_time} seconds before retry...[/yellow]")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    console.print("[red]❌ Request failed after multiple attempts.[/red]")
                    console.print("[dim]The AI service may be experiencing high load. Please try again in a few minutes.[/dim]")
                    return None
            
            # Handle other API errors
            elif "Request failed" in error_msg and not error_msg.strip():
                console.print("[red]❌ Connection failed.[/red]")
                console.print("[dim]Please check your internet connection and ensure the backend is running.[/dim]")
                return None
            
            # Handle authentication errors
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                console.print("[red]❌ Authentication failed.[/red]")
                console.print("[dim]Please run 'zeblit auth login' to authenticate.[/dim]")
                return None
            
            # Handle other specific errors
            else:
                console.print(f"[red]❌ Request failed:[/red] {error_msg}")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Unexpected error:[/red] {str(e)}")
            return None
    
    return None


@click.group(invoke_without_command=True)
@click.argument("message", nargs=-1, required=False)
@click.option("--agent", "-a", help="Target specific agent (default: DevManager)")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
@click.pass_context
def chat_commands(ctx, message: tuple, agent: Optional[str], project: Optional[str]):
    """Agent chat and interaction commands.
    
    Usage:
        zeblit chat "your message"              # Send message directly
        zeblit chat send "your message"         # Alternative syntax
        zeblit chat history                     # View chat history
        zeblit chat agents                      # List available agents
    """
    # Check if first word is a known subcommand
    subcommands = ['send', 'history', 'agents', 'main']
    
    if message and len(message) > 0 and message[0] in subcommands:
        # This is actually a subcommand, let Click handle it normally
        return
    elif message:
        # Direct message - invoke send_message_cmd
        message_text = " ".join(message)
        asyncio.run(send_message_cmd(message_text, agent, project))
    elif ctx.invoked_subcommand is None:
        # No message and no subcommand - show help
        click.echo(ctx.get_help())


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
            
            # Define the chat function to retry
            async def make_chat_request():
                with console.status("[bold blue]Agent is thinking..."):
                    return await api_client.chat_with_agents(
                        project_id=project_id,
                        message=message,
                        target_agent=agent
                    )
            
            # Retry with timeout handling
            response = await retry_with_timeout(make_chat_request, max_retries=2)
            
            if response:
                # Display response
                await display_agent_response(response)
            else:
                console.print("\n💡 [bold]Troubleshooting tips:[/bold]")
                console.print("  • Check that the backend is running: [bold]python start_backend.py[/bold]")
                console.print("  • Verify your internet connection")
                console.print("  • Try a shorter message if the request is very long")
                console.print("  • Check backend logs for more details")
            
    except Exception as e:
        console.print(f"[red]Error sending message:[/red] {str(e)}")
        logger.exception("Unexpected error in send_message_cmd")


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
    try:
        settings = get_settings()
        if routing and settings.preferences.verbose_output:
            console.print(f"[dim]Routed via: {routing.get('path', 'direct')}[/dim]")
    except:
        # Skip routing info if settings unavailable
        pass


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
