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
    auth,
    console,
    containers,
    files,
    frontend_logs,
    git,
    health,
    orchestration,
    projects,
    users,
    websocket
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(containers.router, prefix="/containers", tags=["containers"])
api_router.include_router(git.router, prefix="/git", tags=["git"])
api_router.include_router(frontend_logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(console.router, prefix="/console", tags=["console"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(orchestration.router, prefix="/orchestration", tags=["orchestration"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"]) 