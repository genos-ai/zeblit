"""Commands package for Zeblit CLI."""

# Import all command groups for easy access
from .auth import auth_commands
from .project import project_commands  
from .chat import chat_commands
from .container import container_commands
from .files import file_commands
from .console import console_commands

__all__ = [
    "auth_commands",
    "project_commands", 
    "chat_commands",
    "container_commands",
    "file_commands", 
    "console_commands"
]
