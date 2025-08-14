"""
Authentication commands for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial auth commands.
"""

import asyncio
import logging
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient, APIError

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def auth_commands():
    """Authentication management commands."""
    pass


@auth_commands.command("login")
@click.option("--api-key", help="API key (will prompt if not provided)")
@click.option("--server", help="Server URL (uses config default if not provided)")
def login(api_key: Optional[str], server: Optional[str]):
    """Authenticate with Zeblit using an API key."""
    asyncio.run(login_cmd(api_key, server))


async def login_cmd(api_key: Optional[str], server: Optional[str]):
    """Login command implementation."""
    try:
        # Update server URL if provided
        if server:
            from zeblit_cli.config.settings import update_setting
            update_setting("api_base_url", server)
            console.print(f"[green]Server URL updated to:[/green] {server}")
        
        # Get API key
        if not api_key:
            console.print("\n[bold]Zeblit Authentication[/bold]")
            console.print("To get an API key:")
            console.print("1. Go to your Zeblit dashboard")
            console.print("2. Navigate to Settings > API Keys")
            console.print("3. Create a new API key for CLI access")
            console.print()
            
            api_key = Prompt.ask(
                "Enter your API key", 
                password=True,
                console=console
            )
        
        if not api_key:
            console.print("[red]No API key provided[/red]")
            return
        
        # Validate API key
        console.print("🔍 Validating API key...")
        
        auth_manager = get_auth_manager()
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            try:
                user_info = await auth_manager.login_with_api_key(api_key)
                
                # Success
                console.print("✅ [green]Authentication successful![/green]")
                
                # Show user info
                user = user_info.get("user", {})
                if user:
                    console.print(f"Welcome back, [bold]{user.get('username', 'User')}[/bold]!")
                    console.print(f"Email: {user.get('email', 'N/A')}")
                
                console.print("\n🚀 You're ready to use Zeblit CLI!")
                console.print("Try: [bold]zeblit create my-first-project[/bold]")
                
            except Exception as e:
                console.print(f"[red]Authentication failed:[/red] {str(e)}")
                console.print("\n💡 [dim]Make sure your API key is valid and the server is accessible[/dim]")
                
    except Exception as e:
        console.print(f"[red]Login error:[/red] {str(e)}")


@auth_commands.command("logout")
def logout():
    """Clear stored authentication credentials."""
    asyncio.run(logout_cmd())


async def logout_cmd():
    """Logout command implementation."""
    try:
        auth_manager = get_auth_manager()
        await auth_manager.logout()
        
        console.print("✅ [green]Logged out successfully[/green]")
        console.print("Your local credentials have been cleared.")
        
    except Exception as e:
        console.print(f"[red]Logout error:[/red] {str(e)}")


@auth_commands.command("status")
def status():
    """Show current authentication status."""
    asyncio.run(status_cmd())


async def status_cmd():
    """Status command implementation."""
    try:
        settings = get_settings()
        auth_manager = get_auth_manager()
        
        console.print("\n[bold]Authentication Status[/bold]")
        
        # Check if authenticated
        is_authenticated = await auth_manager.is_authenticated()
        
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        
        # Authentication status
        status_icon = "✅" if is_authenticated else "❌"
        status_text = "[green]Authenticated[/green]" if is_authenticated else "[red]Not authenticated[/red]"
        table.add_row("Status", f"{status_icon} {status_text}")
        
        # API key info
        api_key = await auth_manager.get_api_key()
        if api_key:
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            table.add_row("API Key", masked_key)
        else:
            table.add_row("API Key", "[dim]None[/dim]")
        
        # Server URL
        table.add_row("Server", settings.api_base_url)
        
        # Current project
        if settings.current_project_id:
            table.add_row("Current Project", settings.current_project_id)
        else:
            table.add_row("Current Project", "[dim]None selected[/dim]")
        
        # User info
        if is_authenticated:
            user_info = await auth_manager.get_user_info()
            if user_info:
                table.add_row("Username", user_info.get("username", "N/A"))
                table.add_row("Email", user_info.get("email", "N/A"))
        
        console.print(table)
        
        # Suggestions
        if not is_authenticated:
            console.print("\n💡 Run '[bold]zeblit auth login[/bold]' to authenticate")
        elif not settings.current_project_id:
            console.print("\n💡 Run '[bold]zeblit create <name>[/bold]' to create a project")
            console.print("   or '[bold]zeblit list[/bold]' to see existing projects")
        
    except Exception as e:
        console.print(f"[red]Status error:[/red] {str(e)}")


@auth_commands.command("keys")
def keys():
    """Manage your API keys."""
    asyncio.run(keys_cmd())


async def keys_cmd():
    """API keys management command."""
    try:
        auth_manager = get_auth_manager()
        
        # Require authentication
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # List existing keys
            keys = await api_client.list_api_keys()
            
            if not keys:
                console.print("📝 You don't have any API keys yet.")
                console.print("Create one using the web dashboard or 'zeblit auth create-key'")
                return
            
            console.print("\n[bold]Your API Keys[/bold]")
            
            table = Table()
            table.add_column("Name", style="cyan")
            table.add_column("Prefix", style="dim")
            table.add_column("Created", style="green")
            table.add_column("Last Used", style="yellow")
            table.add_column("Status", justify="center")
            
            for key in keys:
                # Status
                if key.get("is_expired"):
                    status = "[red]Expired[/red]"
                elif not key.get("is_active"):
                    status = "[red]Inactive[/red]"
                else:
                    status = "[green]Active[/green]"
                
                # Dates
                created = key.get("created_at", "").split("T")[0] if key.get("created_at") else "N/A"
                last_used = key.get("last_used", "").split("T")[0] if key.get("last_used") else "Never"
                
                table.add_row(
                    key.get("name", "Unnamed"),
                    f"zbl_{key.get('prefix', '***')}...",
                    created,
                    last_used,
                    status
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@auth_commands.command("create-key")
@click.argument("name")
@click.option("--expires-days", type=int, help="Expiration in days (optional)")
def create_key(name: str, expires_days: Optional[int]):
    """Create a new API key."""
    asyncio.run(create_key_cmd(name, expires_days))


async def create_key_cmd(name: str, expires_days: Optional[int]):
    """Create API key command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        # Require authentication
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Create key
            result = await api_client.create_api_key(
                name=name, 
                expires_in_days=expires_days,
                client_type="cli"
            )
            
            console.print("✅ [green]API key created successfully![/green]")
            console.print("\n[yellow]⚠️  IMPORTANT: Save this key now. It won't be shown again![/yellow]")
            console.print(f"\n[bold]API Key:[/bold] {result.get('api_key', 'N/A')}")
            
            # Show key info
            key_info = result.get("key_info", {})
            if key_info:
                console.print(f"[bold]Name:[/bold] {key_info.get('name', 'N/A')}")
                console.print(f"[bold]Prefix:[/bold] zbl_{key_info.get('prefix', '***')}...")
                if key_info.get("expires_at"):
                    console.print(f"[bold]Expires:[/bold] {key_info['expires_at'].split('T')[0]}")
                else:
                    console.print("[bold]Expires:[/bold] Never")
            
            console.print("\n💾 Store this key securely - you can use it to create additional CLI sessions.")
            
    except Exception as e:
        console.print(f"[red]Error creating API key:[/red] {str(e)}")
