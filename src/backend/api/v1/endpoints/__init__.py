"""API v1 endpoints."""

from src.backend.api.v1.endpoints.auth import router as auth_router
from src.backend.api.v1.endpoints.users import router as users_router
from src.backend.api.v1.endpoints.projects import router as projects_router
from src.backend.api.v1.endpoints.agents import router as agents_router
from src.backend.api.v1.endpoints.health import router as health_router
from src.backend.api.v1.endpoints.conversations import router as conversations_router
from src.backend.api.v1.endpoints.tasks import router as tasks_router
from src.backend.api.v1.endpoints.websocket import router as websocket_router
from src.backend.api.v1.endpoints.console import router as console_router
from src.backend.api.v1.endpoints.containers import router as containers_router
from src.backend.api.v1.endpoints.files import router as files_router
from src.backend.api.v1.endpoints.orchestration import router as orchestration_router

__all__ = [
    "auth_router",
    "users_router",
    "projects_router",
    "agents_router",
    "health_router",
    "conversations_router",
    "tasks_router",
    "websocket_router",
    "console_router",
    "containers_router",
    "files_router",
    "orchestration_router"
] 