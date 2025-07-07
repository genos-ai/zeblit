"""
Service layer for the AI Development Platform.

This package provides business logic services that coordinate
between repositories, handle transactions, and integrate with
external services.
"""

from .auth import AuthService
from .user import UserService
from .project import ProjectService
from .agent import AgentService
from .conversation import ConversationService
from .task import TaskService
from .email import EmailService

__all__ = [
    "AuthService",
    "UserService",
    "ProjectService",
    "AgentService",
    "ConversationService",
    "TaskService",
    "EmailService",
] 