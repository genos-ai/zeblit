"""
API v1 endpoints.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2024-01-XX): Added file management endpoints.
- 1.0.0 (2024-01-XX): Initial endpoints module.
"""

from .health import router as health_router
from .auth import router as auth_router
from .users import router as users_router
from .projects import router as projects_router
from .agents import router as agents_router
from .websocket import router as websocket_router
from .console import router as console_router
from .containers import router as containers_router
from .files import router as files_router

__all__ = [
    "health_router",
    "auth_router", 
    "users_router",
    "projects_router",
    "agents_router",
    "websocket_router",
    "console_router",
    "containers_router",
    "files_router",
] 