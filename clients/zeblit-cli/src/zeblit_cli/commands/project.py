"""
Project management commands for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial project commands.
"""

import asyncio
import logging
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from zeblit_cli.config.settings import get_settings, set_current_project
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient, APIError
from zeblit_cli.utils import (
    with_progress,
    show_error,
    show_success,
    show_info,
    project_id_completion,
    template_completion
)

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def project_commands():
    """Project management commands."""
    pass


@project_commands.command("create")
@click.argument("name")
@click.option("--template", "-t", help="Project template to use")
@click.option("--description", "-d", help="Project description")
def create_project(name: str, template: Optional[str], description: Optional[str]):
    """Create a new project."""
    asyncio.run(create_project_cmd(name, template, description))


async def create_project_cmd(name: str, template: Optional[str], description: Optional[str]):
    """Create project command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        # Require authentication
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Create project with progress
            project = await with_progress(
                api_client.create_project(name=name, description=description, template=template),
                f"Creating project '{name}'...",
                "Project created successfully!"
            )
            
            # Set as current project
            project_id = project.get("id")
            if project_id:
                set_current_project(project_id)
                
                show_success(f"Project '{project.get('name', name)}' created successfully!")
                show_info(f"Project ID: {project_id}")
                if template:
                    show_info(f"Template: {template}")
                if description:
                    show_info(f"Description: {description}")
                
                console.print(f"\n🎯 Project '[bold]{name}[/bold]' is now your active project!")
                console.print("Next steps:")
                console.print("  • [bold]zeblit chat 'What should I build?'[/bold] - Ask the Dev Manager")
                console.print("  • [bold]zeblit container start[/bold] - Start the development environment")
                console.print("  • [bold]zeblit files tree[/bold] - Explore the project structure")
            else:
                show_error("Failed to create project", "No project ID returned from server")
            
    except Exception as e:
        console.print(f"[red]Error creating project:[/red] {str(e)}")


@project_commands.command("list")
@click.option("--limit", "-l", default=20, help="Maximum number of projects to show")
def list_projects(limit: int):
    """List your projects."""
    asyncio.run(list_projects_cmd(limit))


async def list_projects_cmd(limit: int = 20):
    """List projects command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        # Require authentication
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Get projects
            projects = await api_client.list_projects()
            
            if not projects:
                console.print("📝 You don't have any projects yet.")
                console.print("Create one with: [bold]zeblit create <project-name>[/bold]")
                return
            
            # Limit results
            if len(projects) > limit:
                projects = projects[:limit]
                console.print(f"[dim]Showing first {limit} projects[/dim]")
            
            console.print(f"\n[bold]Your Projects[/bold] ({len(projects)} shown)")
            
            table = Table()
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Description", style="green")
            table.add_column("Created", style="yellow")
            table.add_column("Status", justify="center")
            
            current_project_id = settings.current_project_id
            
            for project in projects:
                # Mark current project
                name = project.get("name", "Unnamed")
                if project.get("id") == current_project_id:
                    name = f"👉 {name}"
                
                # Status (simplified)
                status = "🟢 Active"  # Could be enhanced with real status
                
                # Created date
                created = project.get("created_at", "").split("T")[0] if project.get("created_at") else "N/A"
                
                table.add_row(
                    name,
                    project.get("id", "N/A")[:8] + "...",  # Shortened ID
                    project.get("description", "No description")[:50],  # Truncated
                    created,
                    status
                )
            
            console.print(table)
            
            if current_project_id:
                console.print(f"\n👉 Current project: [bold]{current_project_id}[/bold]")
            else:
                console.print("\n💡 Use '[bold]zeblit use <project-id>[/bold]' to select a project")
            
    except Exception as e:
        console.print(f"[red]Error listing projects:[/red] {str(e)}")


@project_commands.command("use")
@click.argument("project_id")
def use_project(project_id: str):
    """Set the active project."""
    asyncio.run(use_project_cmd(project_id))


async def use_project_cmd(project_id: str):
    """Use project command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        # Require authentication
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Verify project exists and user has access
            try:
                project = await api_client.get_project(project_id)
            except APIError as e:
                if e.status_code == 404:
                    console.print(f"[red]Project not found:[/red] {project_id}")
                    console.print("Use '[bold]zeblit list[/bold]' to see available projects")
                    return
                raise
            
            # Set as current project
            set_current_project(project_id)
            
            console.print("✅ [green]Active project updated![/green]")
            console.print(f"[bold]Name:[/bold] {project.get('name', 'N/A')}")
            console.print(f"[bold]ID:[/bold] {project_id}")
            console.print(f"[bold]Description:[/bold] {project.get('description', 'No description')}")
            
            console.print("\n🎯 You're now working on this project!")
            console.print("Try:")
            console.print("  • [bold]zeblit status[/bold] - Check project status")
            console.print("  • [bold]zeblit chat 'What's in this project?'[/bold] - Ask about the project")
            console.print("  • [bold]zeblit container start[/bold] - Start development environment")
            
    except Exception as e:
        console.print(f"[red]Error setting active project:[/red] {str(e)}")


@project_commands.command("delete")
@click.argument("project_id")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def delete_project(project_id: str, force: bool):
    """Delete a project."""
    asyncio.run(delete_project_cmd(project_id, force))


async def delete_project_cmd(project_id: str, force: bool):
    """Delete project command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        # Require authentication
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Get project info for confirmation
            try:
                project = await api_client.get_project(project_id)
            except APIError as e:
                if e.status_code == 404:
                    console.print(f"[red]Project not found:[/red] {project_id}")
                    return
                raise
            
            project_name = project.get("name", "Unknown")
            
            # Confirmation
            if not force:
                console.print(f"⚠️  [yellow]You are about to delete project '[bold]{project_name}[/bold]'[/yellow]")
                console.print("This action cannot be undone!")
                
                if not Confirm.ask("Are you sure you want to delete this project?"):
                    console.print("❌ Delete cancelled")
                    return
            
            # Delete project
            console.print(f"🗑️  Deleting project '[bold]{project_name}[/bold]'...")
            
            await api_client.delete_project(project_id)
            
            # Clear current project if it was the deleted one
            if settings.current_project_id == project_id:
                set_current_project(None)
                console.print("💡 Active project cleared (was the deleted project)")
            
            console.print("✅ [green]Project deleted successfully![/green]")
            
    except Exception as e:
        console.print(f"[red]Error deleting project:[/red] {str(e)}")


@project_commands.command("info")
@click.argument("project_id", required=False)
def project_info(project_id: Optional[str]):
    """Show detailed project information."""
    asyncio.run(project_info_cmd(project_id))


async def project_info_cmd(project_id: Optional[str]):
    """Project info command implementation."""
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
                console.print("Use: [bold]zeblit project info <project-id>[/bold]")
                console.print("Or: [bold]zeblit use <project-id>[/bold] first")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Get project details
            project = await api_client.get_project(project_id)
            
            console.print(f"\n[bold]Project Information[/bold]")
            
            table = Table(show_header=False, box=None)
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            
            table.add_row("Name", project.get("name", "N/A"))
            table.add_row("ID", project.get("id", "N/A"))
            table.add_row("Description", project.get("description", "No description"))
            table.add_row("Template", project.get("template", "N/A"))
            table.add_row("Created", project.get("created_at", "N/A").split("T")[0] if project.get("created_at") else "N/A")
            table.add_row("Updated", project.get("updated_at", "N/A").split("T")[0] if project.get("updated_at") else "N/A")
            
            # Mark if current project
            if project_id == settings.current_project_id:
                table.add_row("Status", "👉 [green]Current Project[/green]")
            
            console.print(table)
            
            # Additional info could be added here (container status, file count, etc.)
            
    except Exception as e:
        console.print(f"[red]Error getting project info:[/red] {str(e)}")


async def status_cmd():
    """Show current project and container status."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        # Require authentication
        await auth_manager.require_auth()
        
        if not settings.current_project_id:
            console.print("[yellow]No active project selected[/yellow]")
            console.print("Use '[bold]zeblit list[/bold]' to see projects or '[bold]zeblit create <name>[/bold]' to create one")
            return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            console.print("\n[bold]Current Status[/bold]")
            
            # Get project info
            try:
                project = await api_client.get_project(settings.current_project_id)
                console.print(f"📁 [bold]Project:[/bold] {project.get('name', 'N/A')} ({settings.current_project_id[:8]}...)")
            except:
                console.print(f"📁 [bold]Project:[/bold] {settings.current_project_id[:8]}... [red](error loading details)[/red]")
            
            # Get container status
            try:
                container_status = await api_client.get_container_status(settings.current_project_id)
                status = container_status.get("status", "unknown")
                
                if status == "running":
                    console.print("🟢 [bold]Container:[/bold] [green]Running[/green]")
                elif status == "stopped":
                    console.print("🔴 [bold]Container:[/bold] [red]Stopped[/red]")
                else:
                    console.print(f"🟡 [bold]Container:[/bold] {status}")
                    
            except:
                console.print("🟡 [bold]Container:[/bold] [yellow]Status unknown[/yellow]")
            
            # Quick actions
            console.print("\n💡 [bold]Quick actions:[/bold]")
            console.print("  • [bold]zeblit chat 'What can I do?'[/bold] - Ask the Dev Manager")
            console.print("  • [bold]zeblit container start[/bold] - Start development environment")
            console.print("  • [bold]zeblit files tree[/bold] - View project files")
            console.print("  • [bold]zeblit console[/bold] - Live container output")
            
    except Exception as e:
        console.print(f"[red]Error getting status:[/red] {str(e)}")
