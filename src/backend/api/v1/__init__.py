"""
API version 1 router configuration.

This module aggregates all v1 API routers and provides
a single router instance for the main application.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2024-01-XX): Added auth and users endpoints.
- 1.0.0 (2024-01-XX): Initial v1 router configuration.
"""

from fastapi import APIRouter

from .health import router as health_router
from .endpoints.auth import router as auth_router
from .endpoints.users import router as users_router

# Create main v1 router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["authentication"])
router.include_router(users_router, tags=["users"])

# Future routers will be added here:
# router.include_router(projects_router, prefix="/projects", tags=["projects"])
# router.include_router(agents_router, prefix="/agents", tags=["agents"])
# router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
# router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
# router.include_router(files_router, prefix="/files", tags=["files"])
# router.include_router(containers_router, prefix="/containers", tags=["containers"]) 