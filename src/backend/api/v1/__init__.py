"""API v1 router configuration."""

from fastapi import APIRouter

from src.backend.api.v1.endpoints import (
    auth_router,
    users_router,
    projects_router,
    agents_router,
    health_router,
    conversations_router,
    tasks_router,
    websocket_router,
    console_router,
    containers_router,
    files_router,
    orchestration_router,
    git_router
)

api_router = APIRouter()

# Include all routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(projects_router)
api_router.include_router(agents_router)
api_router.include_router(conversations_router)
api_router.include_router(tasks_router)
api_router.include_router(console_router)
api_router.include_router(containers_router)
api_router.include_router(files_router)
api_router.include_router(orchestration_router)
api_router.include_router(git_router)
api_router.include_router(websocket_router)

# Future routers will be added here:
# router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
# router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
# router.include_router(files_router, prefix="/files", tags=["files"])

# Export as router for main.py
router = api_router 