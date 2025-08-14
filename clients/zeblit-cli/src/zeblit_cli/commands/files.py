"""
File management commands for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial file commands.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.tree import Tree
from rich.table import Table

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient, APIError

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def file_commands():
    """File management commands."""
    pass


@file_commands.command("tree")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def file_tree(project: Optional[str]):
    """Show project file tree."""
    asyncio.run(file_tree_cmd(project))


async def file_tree_cmd(project_id: Optional[str]):
    """File tree command implementation."""
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
            
            file_tree = await api_client.get_file_tree(project_id)
            
            if not file_tree:
                console.print("📁 Project appears to be empty")
                return
            
            # Create rich tree visualization
            tree = Tree("📁 Project Files")
            _build_tree(tree, file_tree, "")
            
            console.print(tree)
            
    except Exception as e:
        console.print(f"[red]Error getting file tree:[/red] {str(e)}")


def _build_tree(tree, file_data, path):
    """Recursively build tree structure."""
    if isinstance(file_data, dict):
        if "type" in file_data:
            # This is a file/directory node
            if file_data["type"] == "directory":
                branch = tree.add(f"📁 {path}")
                children = file_data.get("children", {})
                for name, child in children.items():
                    _build_tree(branch, child, name)
            else:
                # File
                size = file_data.get("size", 0)
                size_str = f" ({size} bytes)" if size > 0 else ""
                tree.add(f"📄 {path}{size_str}")
        else:
            # Dict of children
            for name, child in file_data.items():
                _build_tree(tree, child, name)


@file_commands.command("list")
@click.argument("path", default="/")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def list_files(path: str, project: Optional[str]):
    """List files in a directory."""
    asyncio.run(list_files_cmd(path, project))


async def list_files_cmd(path: str, project_id: Optional[str]):
    """List files command implementation."""
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
            
            files = await api_client.list_files(project_id, path)
            
            if not files:
                console.print(f"📁 Directory '{path}' is empty")
                return
            
            console.print(f"\n[bold]Files in {path}[/bold]")
            
            table = Table()
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Size", style="yellow", justify="right")
            table.add_column("Modified", style="dim")
            
            for file_info in files:
                name = file_info.get("name", "unknown")
                file_type = "📁 Directory" if file_info.get("type") == "directory" else "📄 File"
                size = file_info.get("size", 0)
                size_str = f"{size:,} bytes" if file_type == "📄 File" else "-"
                modified = file_info.get("modified", "").split("T")[0] if file_info.get("modified") else "N/A"
                
                table.add_row(name, file_type, size_str, modified)
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error listing files:[/red] {str(e)}")


@file_commands.command("upload")
@click.argument("local_path")
@click.argument("remote_path")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def upload_file(local_path: str, remote_path: str, project: Optional[str]):
    """Upload a file to the project."""
    asyncio.run(upload_file_cmd(local_path, remote_path, project))


async def upload_file_cmd(local_path: str, remote_path: str, project_id: Optional[str]):
    """Upload file command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified[/red]")
                return
        
        # Check if local file exists
        if not os.path.exists(local_path):
            console.print(f"[red]Local file not found:[/red] {local_path}")
            return
        
        # Get file size for progress
        file_size = os.path.getsize(local_path)
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            console.print(f"📤 Uploading {local_path} → {remote_path} ({file_size:,} bytes)")
            
            result = await api_client.upload_file(project_id, local_path, remote_path)
            
            console.print("✅ [green]Upload completed successfully![/green]")
            
            if result.get("file_info"):
                info = result["file_info"]
                console.print(f"Remote path: {info.get('path', remote_path)}")
                console.print(f"Size: {info.get('size', file_size):,} bytes")
            
    except Exception as e:
        console.print(f"[red]Error uploading file:[/red] {str(e)}")


@file_commands.command("download")
@click.argument("remote_path")
@click.argument("local_path", required=False)
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
def download_file(remote_path: str, local_path: Optional[str], project: Optional[str]):
    """Download a file from the project."""
    if not local_path:
        local_path = os.path.basename(remote_path)
    
    asyncio.run(download_file_cmd(remote_path, local_path, project))


async def download_file_cmd(remote_path: str, local_path: str, project_id: Optional[str]):
    """Download file command implementation."""
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
            
            console.print(f"📥 Downloading {remote_path} → {local_path}")
            
            content = await api_client.download_file(project_id, remote_path)
            
            # Create local directory if needed
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            # Write file
            with open(local_path, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            console.print(f"✅ [green]Download completed![/green] ({file_size:,} bytes)")
            console.print(f"Saved to: {local_path}")
            
    except Exception as e:
        console.print(f"[red]Error downloading file:[/red] {str(e)}")


@file_commands.command("edit")
@click.argument("remote_path")
@click.option("--project", "-p", help="Project ID (uses current project if not specified)")
@click.option("--editor", help="Editor to use (default: from preferences)")
def edit_file(remote_path: str, project: Optional[str], editor: Optional[str]):
    """Edit a file (download, edit locally, upload back)."""
    asyncio.run(edit_file_cmd(remote_path, project, editor))


async def edit_file_cmd(remote_path: str, project_id: Optional[str], editor: Optional[str]):
    """Edit file command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                console.print("[red]No project specified[/red]")
                return
        
        # Use configured editor
        if not editor:
            editor = settings.preferences.default_editor
        
        # Create temp file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False, 
                                               suffix=os.path.splitext(remote_path)[1])
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            async with ZeblitAPIClient(auth_manager) as api_client:
                auth_manager.set_api_client(api_client)
                
                # Download file
                console.print(f"📥 Downloading {remote_path} for editing...")
                content = await api_client.download_file(project_id, remote_path)
                
                # Write to temp file
                with open(temp_path, 'wb') as f:
                    f.write(content)
                
                # Get original modification time
                original_mtime = os.path.getmtime(temp_path)
                
                # Open in editor
                console.print(f"✏️  Opening in {editor}...")
                os.system(f"{editor} {temp_path}")
                
                # Check if file was modified
                new_mtime = os.path.getmtime(temp_path)
                
                if new_mtime > original_mtime:
                    # File was modified, upload it back
                    console.print(f"📤 Uploading changes to {remote_path}...")
                    await api_client.upload_file(project_id, temp_path, remote_path)
                    console.print("✅ [green]Changes saved![/green]")
                else:
                    console.print("📝 No changes detected")
                
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        console.print(f"[red]Error editing file:[/red] {str(e)}")
