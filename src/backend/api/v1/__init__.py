"""
API version 1 router configuration.

This module aggregates all v1 API routers and provides
a single router instance for the main application.
"""

from fastapi import APIRouter

from .health import router as health_router

# Create main v1 router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(health_router, tags=["health"])

# Future routers will be added here:
# router.include_router(auth_router, prefix="/auth", tags=["authentication"])
# router.include_router(users_router, prefix="/users", tags=["users"])
# router.include_router(projects_router, prefix="/projects", tags=["projects"])
# router.include_router(agents_router, prefix="/agents", tags=["agents"])
# router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
# router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
# router.include_router(files_router, prefix="/files", tags=["files"])
# router.include_router(containers_router, prefix="/containers", tags=["containers"]) 