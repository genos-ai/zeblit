"""
API version 1 router.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial API v1 implementation.
"""

from fastapi import APIRouter

from src.backend.api.v1.endpoints import (
    health_router,
    auth_router,
    users_router,
    projects_router,
    agents_router,
    websocket_router,
    console_router,
    containers_router,
)

# Create v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(projects_router)
api_router.include_router(agents_router)
api_router.include_router(websocket_router)
api_router.include_router(console_router)
api_router.include_router(containers_router)

# Future routers will be added here:
# router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
# router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
# router.include_router(files_router, prefix="/files", tags=["files"])

# Export as router for main.py
router = api_router 