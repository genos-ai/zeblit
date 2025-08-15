"""
API v1 router configuration.

Version: 1.3.0
Author: Zeblit Team

## Changelog
- 1.3.0 (2024-01-08): Fixed imports and added missing endpoints
- 1.2.0 (2024-01-08): Added frontend_logs endpoint
- 1.1.0 (2024-01-07): Added git endpoints
- 1.0.0 (2024-01-05): Initial API router setup
"""

from fastapi import APIRouter

from modules.backend.api.v1.endpoints import (
    agents,
    api_keys,
    auth,
    console,
    containers,
    files,
    frontend_logs,
    git,
    health,
    models,
    orchestration,
    projects,
    scheduled_tasks,
    users,
    websocket
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(api_keys.router, tags=["api-keys"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(containers.router, tags=["containers"])
api_router.include_router(git.router, tags=["git"])
api_router.include_router(frontend_logs.router, tags=["logs"])
api_router.include_router(console.router, tags=["console"])
api_router.include_router(files.router, tags=["files"])
api_router.include_router(orchestration.router, prefix="/orchestration", tags=["orchestration"])
api_router.include_router(scheduled_tasks.router, tags=["scheduled-tasks"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"]) 