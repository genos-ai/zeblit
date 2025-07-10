"""
Console API endpoints for managing console logs and errors.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial console endpoints implementation.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.database import get_db
from src.backend.core.dependencies import get_current_user
from src.backend.models.user import User
from src.backend.schemas.user import UserResponse
from src.backend.schemas.websocket import ConsoleLogPayload, ErrorLogPayload
from src.backend.services.console import ConsoleService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/console",
    tags=["console"],
)


@router.get("/projects/{project_id}/logs")
async def get_project_console_logs(
    project_id: UUID,
    count: int = Query(100, ge=1, le=1000, description="Number of logs to retrieve"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent console logs for a project.
    
    Args:
        project_id: Project ID
        count: Number of logs to retrieve (max 1000)
        level: Optional filter by log level (log, warn, error, info, debug)
        
    Returns:
        List of console log entries
    """
    # Check project access
    project = await ConsoleService.get_project_by_id(db, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get logs
    logs = await ConsoleService.get_recent_logs(
        project_id=project_id,
        count=count,
        level_filter=level
    )
    
    return logs


@router.get("/projects/{project_id}/errors")
async def get_project_errors(
    project_id: UUID,
    count: int = Query(50, ge=1, le=100, description="Number of errors to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent error logs for a project.
    
    Args:
        project_id: Project ID
        count: Number of errors to retrieve (max 100)
        
    Returns:
        List of error log entries
    """
    # Check project access
    project = await ConsoleService.get_project_by_id(db, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get errors
    errors = await ConsoleService.get_recent_errors(
        project_id=project_id,
        count=count
    )
    
    return errors


@router.get("/projects/{project_id}/stats")
async def get_project_console_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, int]:
    """
    Get console statistics for a project.
    
    Args:
        project_id: Project ID
        
    Returns:
        Dictionary with log counts by level
    """
    # Check project access
    project = await ConsoleService.get_project_by_id(db, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get stats
    stats = await ConsoleService.get_console_stats(project_id=project_id)
    
    return stats


@router.get("/projects/{project_id}/context")
async def get_project_console_context(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get console context formatted for AI analysis.
    
    Args:
        project_id: Project ID
        
    Returns:
        Console context including recent errors, warnings, logs, and statistics
    """
    # Check project access
    project = await ConsoleService.get_project_by_id(db, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get AI context
    context = await ConsoleService.get_console_context_for_ai(project_id=project_id)
    
    return context


@router.delete("/projects/{project_id}/logs")
async def clear_project_logs(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Clear all console logs for a project.
    
    Args:
        project_id: Project ID
        
    Returns:
        Success message
    """
    # Check project access
    project = await ConsoleService.get_project_by_id(db, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Clear logs
    success = await ConsoleService.clear_logs(project_id=project_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear logs"
        )
    
    return {"message": "Console logs cleared successfully"}


@router.post("/projects/{project_id}/logs")
async def store_console_log(
    project_id: UUID,
    log_data: ConsoleLogPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Store a console log entry (typically from WebSocket, but available via REST).
    
    Args:
        project_id: Project ID
        log_data: Console log data
        
    Returns:
        Success message
    """
    # Check project access
    project = await ConsoleService.get_project_by_id(db, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Store log
    await ConsoleService.store_console_log(
        project_id=project_id,
        user_id=current_user.id,
        log_data=log_data
    )
    
    return {"message": "Console log stored successfully"}


@router.post("/projects/{project_id}/errors")
async def store_error_log(
    project_id: UUID,
    error_data: ErrorLogPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Store an error log entry (typically from WebSocket, but available via REST).
    
    Args:
        project_id: Project ID
        error_data: Error log data
        
    Returns:
        Success message
    """
    # Check project access
    project = await ConsoleService.get_project_by_id(db, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Store error
    await ConsoleService.store_error_log(
        project_id=project_id,
        user_id=current_user.id,
        error_data=error_data
    )
    
    return {"message": "Error log stored successfully"} 