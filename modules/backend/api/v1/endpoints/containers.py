"""
Container API endpoints for managing development environments.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial container endpoints implementation.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.database import get_db
from modules.backend.core.dependencies import get_current_user
from modules.backend.models.user import User
from modules.backend.schemas.container import (
    ContainerCreate,
    ContainerRead,
    ContainerUpdate,
    ContainerStats,
    ContainerLogs,
    ContainerCommand,
    ContainerCommandResult,
    ContainerHealth
)
from modules.backend.services.container import ContainerService
from modules.backend.core.exceptions import (
    NotFoundError,
    ValidationError,
    ForbiddenError,
    ServiceError
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/containers",
    tags=["containers"],
)


@router.post("/projects/{project_id}/container", response_model=ContainerRead)
async def create_container(
    project_id: UUID,
    container_data: ContainerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new container for a project.
    
    Args:
        project_id: Project ID
        container_data: Container configuration
        
    Returns:
        Created container
    """
    try:
        container = await ContainerService.create_container(
            db=db,
            project_id=project_id,
            user=current_user,
            cpu_limit=container_data.cpu_limit,
            memory_limit=container_data.memory_limit,
            disk_limit=container_data.disk_limit,
            environment_vars=container_data.environment_vars
        )
        return container
    except (NotFoundError, ValidationError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create container"
        )


@router.get("/projects/{project_id}/container", response_model=Optional[ContainerRead])
async def get_project_container(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get container for a project.
    
    Args:
        project_id: Project ID
        
    Returns:
        Container if exists, None otherwise
    """
    try:
        container = await ContainerService.get_project_container(
            db=db,
            project_id=project_id,
            user=current_user
        )
        return container
    except NotFoundError:
        return None
    except Exception as e:
        logger.error(f"Failed to get container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get container"
        )


@router.post("/{container_id}/start", response_model=ContainerRead)
async def start_container(
    container_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a stopped or sleeping container."""
    try:
        container = await ContainerService.start_container(
            db=db,
            container_id=container_id,
            user=current_user
        )
        return container
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start container"
        )


@router.post("/{container_id}/stop", response_model=ContainerRead)
async def stop_container(
    container_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop a running container."""
    try:
        container = await ContainerService.stop_container(
            db=db,
            container_id=container_id,
            user=current_user
        )
        return container
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to stop container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop container"
        )


@router.post("/{container_id}/restart", response_model=ContainerRead)
async def restart_container(
    container_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Restart a container."""
    try:
        container = await ContainerService.restart_container(
            db=db,
            container_id=container_id,
            user=current_user
        )
        return container
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restart container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart container"
        )


@router.delete("/{container_id}")
async def delete_container(
    container_id: UUID,
    force: bool = Query(False, description="Force delete even if running"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a container."""
    try:
        success = await ContainerService.delete_container(
            db=db,
            container_id=container_id,
            user=current_user,
            force=force
        )
        if success:
            return {"message": "Container deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete container"
            )
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete container"
        )


@router.get("/{container_id}/stats", response_model=ContainerStats)
async def get_container_stats(
    container_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get container resource usage statistics."""
    try:
        stats = await ContainerService.get_container_stats(
            db=db,
            container_id=container_id,
            user=current_user
        )
        return ContainerStats(**stats)
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get container stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get container statistics"
        )


@router.get("/{container_id}/logs", response_model=ContainerLogs)
async def get_container_logs(
    container_id: UUID,
    tail: int = Query(100, ge=1, le=1000, description="Number of lines to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get container logs."""
    try:
        logs = await ContainerService.get_container_logs(
            db=db,
            container_id=container_id,
            user=current_user,
            tail=tail
        )
        return ContainerLogs(logs=logs, tail=tail)
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get container logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get container logs"
        )


@router.post("/{container_id}/exec", response_model=ContainerCommandResult)
async def execute_command(
    container_id: UUID,
    command: ContainerCommand,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a command in the container.
    
    Args:
        container_id: Container ID
        command: Command to execute
        
    Returns:
        Command execution result
    """
    try:
        exit_code, output = await ContainerService.execute_command(
            db=db,
            container_id=container_id,
            user=current_user,
            command=command.command,
            workdir=command.workdir
        )
        return ContainerCommandResult(exit_code=exit_code, output=output)
    except (NotFoundError, ForbiddenError, ValidationError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute command"
        )


@router.get("/{container_id}/health", response_model=ContainerHealth)
async def check_container_health(
    container_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check container health status."""
    try:
        # Get container
        from modules.backend.repositories.container import ContainerRepository
        
        repo = ContainerRepository(db)
        container = await repo.get_by_id(container_id)
        
        if not container:
            raise NotFoundError("Container not found")
        
        # Verify access
        await db.refresh(container, ["project"])
        if container.project.owner_id != current_user.id:
            raise ForbiddenError("Access denied")
        
        return ContainerHealth(
            healthy=container.is_healthy,
            status=container.status,
            last_health_check=container.last_health_check,
            health_check_failures=container.health_check_failures
        )
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to check container health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check container health"
        )


# New API endpoints for backend-first implementation

@router.post("/projects/{project_id}/container/start")
async def start_project_container(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start or create container for a project."""
    try:
        container = await ContainerService.start_project_container(
            db=db,
            project_id=project_id,
            user=current_user
        )
        return {"container_id": str(container.id), "status": container.status}
    except (NotFoundError, ValidationError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start project container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start container"
        )


@router.post("/projects/{project_id}/container/stop")
async def stop_project_container(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop container for a project."""
    try:
        success = await ContainerService.stop_project_container(
            db=db,
            project_id=project_id,
            user=current_user
        )
        return {"success": success}
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to stop project container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop container"
        )


@router.get("/projects/{project_id}/container/status")
async def get_project_container_status(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get container status for a project."""
    try:
        status_info = await ContainerService.get_project_container_status(
            db=db,
            project_id=project_id,
            user=current_user
        )
        return status_info
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get container status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get container status"
        )


@router.post("/projects/{project_id}/container/execute")
async def execute_project_command(
    project_id: UUID,
    command: ContainerCommand,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a command in project container."""
    try:
        result = await ContainerService.execute_project_command(
            db=db,
            project_id=project_id,
            user=current_user,
            command=command.command,
            workdir=command.workdir
        )
        return result
    except (NotFoundError, ValidationError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute project command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute command"
        )


@router.get("/projects/{project_id}/container/logs")
async def get_project_container_logs(
    project_id: UUID,
    tail: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get logs from project container."""
    try:
        logs = await ContainerService.get_project_container_logs(
            db=db,
            project_id=project_id,
            user=current_user,
            tail=tail
        )
        return {"logs": logs, "tail": tail}
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get project container logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get container logs"
        ) 