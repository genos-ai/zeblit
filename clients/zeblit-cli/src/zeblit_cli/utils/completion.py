"""
Tab completion utilities for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial tab completion implementation.
"""

import os
import asyncio
from typing import List, Optional, Tuple

import click
from rich.console import Console

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient

console = Console()


def project_id_completion(ctx, param, incomplete):
    """Tab completion for project IDs."""
    try:
        # Run async completion in sync context
        return asyncio.run(_get_project_completions(incomplete))
    except Exception:
        return []


async def _get_project_completions(incomplete: str) -> List[str]:
    """Get project completions."""
    try:
        auth_manager = get_auth_manager()
        
        # Check if authenticated
        if not await auth_manager.is_authenticated():
            return []
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            projects = await api_client.list_projects()
            
            # Return project IDs and names that match incomplete
            completions = []
            for project in projects:
                project_id = project.get("id", "")
                project_name = project.get("name", "")
                
                # Match by ID prefix
                if project_id.startswith(incomplete):
                    completions.append(project_id)
                
                # Match by name prefix
                if project_name.lower().startswith(incomplete.lower()):
                    completions.append(project_id)
            
            return completions[:10]  # Limit to 10 completions
            
    except Exception:
        return []


def agent_type_completion(ctx, param, incomplete):
    """Tab completion for agent types."""
    agent_types = [
        "dev_manager",
        "product_manager", 
        "engineer",
        "architect",
        "data_analyst",
        "platform_engineer"
    ]
    
    return [agent for agent in agent_types if agent.startswith(incomplete.lower())]


def file_path_completion(ctx, param, incomplete):
    """Tab completion for file paths."""
    try:
        return asyncio.run(_get_file_path_completions(incomplete))
    except Exception:
        return []


async def _get_file_path_completions(incomplete: str) -> List[str]:
    """Get file path completions from current project."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        # Check if authenticated and has active project
        if not await auth_manager.is_authenticated() or not settings.current_project_id:
            return []
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Get file tree
            file_tree = await api_client.get_file_tree(settings.current_project_id)
            
            # Extract file paths that match incomplete
            completions = []
            _extract_paths_from_tree(file_tree, "", incomplete, completions)
            
            return completions[:20]  # Limit to 20 completions
            
    except Exception:
        return []


def _extract_paths_from_tree(tree: dict, current_path: str, incomplete: str, completions: List[str]):
    """Recursively extract file paths from tree structure."""
    if not isinstance(tree, dict):
        return
    
    for name, subtree in tree.items():
        path = f"{current_path}/{name}".lstrip("/")
        
        # Add if it matches incomplete
        if path.startswith(incomplete) or incomplete in path:
            completions.append(path)
        
        # Recurse into directories
        if isinstance(subtree, dict):
            _extract_paths_from_tree(subtree, path, incomplete, completions)


def container_command_completion(ctx, param, incomplete):
    """Tab completion for common container commands."""
    common_commands = [
        "python",
        "pip install",
        "npm install", 
        "npm run",
        "node",
        "ls",
        "pwd",
        "cat",
        "grep",
        "find",
        "git status",
        "git add",
        "git commit",
        "git push",
        "git pull",
        "docker",
        "curl",
        "wget",
        "vim",
        "nano",
        "mkdir",
        "rm",
        "cp",
        "mv",
        "chmod",
        "cd"
    ]
    
    return [cmd for cmd in common_commands if cmd.startswith(incomplete)]


def template_completion(ctx, param, incomplete):
    """Tab completion for project templates."""
    templates = [
        "python-web",
        "python-api", 
        "python-cli",
        "javascript-web",
        "javascript-api",
        "react-app",
        "vue-app",
        "nextjs-app",
        "node-api",
        "docker-app",
        "minimal"
    ]
    
    return [template for template in templates if template.startswith(incomplete)]


def local_file_completion(ctx, param, incomplete):
    """Tab completion for local file paths."""
    try:
        # Handle ~ expansion
        if incomplete.startswith("~"):
            incomplete = os.path.expanduser(incomplete)
        
        # Get directory and filename parts
        if os.path.sep in incomplete:
            directory = os.path.dirname(incomplete)
            filename_start = os.path.basename(incomplete)
        else:
            directory = "."
            filename_start = incomplete
        
        # List directory contents
        if os.path.isdir(directory):
            completions = []
            for item in os.listdir(directory):
                if item.startswith(filename_start):
                    full_path = os.path.join(directory, item)
                    if os.path.isdir(full_path):
                        completions.append(full_path + os.path.sep)
                    else:
                        completions.append(full_path)
            return completions
        
        return []
        
    except Exception:
        return []


def setup_completion():
    """Setup shell completion for Zeblit CLI."""
    console.print("🔧 Setting up tab completion...")
    
    # Get the shell
    shell = os.environ.get('SHELL', '').split('/')[-1]
    
    if shell == 'bash':
        setup_bash_completion()
    elif shell == 'zsh':
        setup_zsh_completion()
    elif shell in ['fish']:
        setup_fish_completion()
    else:
        console.print(f"[yellow]Unsupported shell: {shell}[/yellow]")
        console.print("Supported shells: bash, zsh, fish")
        return False
    
    console.print("✅ [green]Tab completion setup complete![/green]")
    console.print("💡 [blue]Restart your shell or run 'source ~/.bashrc' (or equivalent) to activate.[/blue]")
    return True


def setup_bash_completion():
    """Setup bash completion."""
    bash_completion = '''
# Zeblit CLI bash completion
eval "$(_ZEBLIT_COMPLETE=bash_source zeblit)"
'''
    
    bashrc_path = os.path.expanduser("~/.bashrc")
    
    # Check if already added
    try:
        with open(bashrc_path, 'r') as f:
            content = f.read()
            if "_ZEBLIT_COMPLETE" in content:
                console.print("[yellow]Bash completion already configured[/yellow]")
                return
    except FileNotFoundError:
        pass
    
    # Add to bashrc
    try:
        with open(bashrc_path, 'a') as f:
            f.write('\n' + bash_completion)
        console.print(f"Added completion to {bashrc_path}")
    except Exception as e:
        console.print(f"[red]Failed to setup bash completion: {e}[/red]")


def setup_zsh_completion():
    """Setup zsh completion."""
    zsh_completion = '''
# Zeblit CLI zsh completion
eval "$(_ZEBLIT_COMPLETE=zsh_source zeblit)"
'''
    
    zshrc_path = os.path.expanduser("~/.zshrc")
    
    # Check if already added
    try:
        with open(zshrc_path, 'r') as f:
            content = f.read()
            if "_ZEBLIT_COMPLETE" in content:
                console.print("[yellow]Zsh completion already configured[/yellow]")
                return
    except FileNotFoundError:
        pass
    
    # Add to zshrc
    try:
        with open(zshrc_path, 'a') as f:
            f.write('\n' + zsh_completion)
        console.print(f"Added completion to {zshrc_path}")
    except Exception as e:
        console.print(f"[red]Failed to setup zsh completion: {e}[/red]")


def setup_fish_completion():
    """Setup fish completion."""
    fish_completion = '''
# Zeblit CLI fish completion
eval (env _ZEBLIT_COMPLETE=fish_source zeblit)
'''
    
    config_dir = os.path.expanduser("~/.config/fish")
    config_path = os.path.join(config_dir, "config.fish")
    
    # Create config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    # Check if already added
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            if "_ZEBLIT_COMPLETE" in content:
                console.print("[yellow]Fish completion already configured[/yellow]")
                return
    except FileNotFoundError:
        pass
    
    # Add to config.fish
    try:
        with open(config_path, 'a') as f:
            f.write('\n' + fish_completion)
        console.print(f"Added completion to {config_path}")
    except Exception as e:
        console.print(f"[red]Failed to setup fish completion: {e}[/red]")


# Apply completion to specific Click parameters
def add_completions_to_commands():
    """Add completions to CLI commands (called during initialization)."""
    # This would be called by the main CLI to add completions
    # The actual completion setup happens through Click's built-in mechanisms
    pass
