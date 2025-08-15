"""
API endpoints for scheduled task management.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial scheduled task endpoints.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.database import get_db
from modules.backend.core.dependencies import get_current_user
from modules.backend.models.user import User
from modules.backend.schemas.scheduled_task import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskRead,
    ScheduledTaskWithRuns,
    ScheduledTaskStats,
    TaskExecutionRequest,
    BulkTaskOperation,
    ScheduleValidationRequest,
    ScheduleValidationResponse,
    TaskQuickCreate
)
from modules.backend.services.scheduled_task import ScheduledTaskService
from modules.backend.core.exceptions import (
    NotFoundError,
    ValidationError,
    ForbiddenError
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/scheduled-tasks",
    tags=["scheduled-tasks"]
)


@router.post("/", response_model=ScheduledTaskRead)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new scheduled task.
    
    Creates a scheduled task that will be executed according to the specified
    cron schedule in the project's container environment.
    """
    try:
        service = ScheduledTaskService(db)
        task = await service.create_task(
            user=current_user,
            project_id=task_data.project_id,
            name=task_data.name,
            schedule=task_data.schedule,
            command=task_data.command,
            description=task_data.description,
            working_directory=task_data.working_directory,
            environment_variables=task_data.environment_variables,
            timeout_seconds=task_data.timeout_seconds,
            max_retries=task_data.max_retries,
            capture_output=task_data.capture_output,
            notify_on_failure=task_data.notify_on_failure,
            notify_on_success=task_data.notify_on_success
        )
        return ScheduledTaskRead.from_orm(task)
        
    except (NotFoundError, ValidationError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create scheduled task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scheduled task"
        )


@router.post("/quick", response_model=ScheduledTaskRead)
async def create_quick_task(
    task_data: TaskQuickCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a scheduled task using presets.
    
    Provides a simplified interface for creating common scheduled tasks
    using predefined schedules (daily, hourly, weekly) or custom cron expressions.
    """
    try:
        service = ScheduledTaskService(db)
        schedule = task_data.get_schedule()
        
        task = await service.create_task(
            user=current_user,
            project_id=task_data.project_id,
            name=task_data.name,
            schedule=schedule,
            command=task_data.command
        )
        return ScheduledTaskRead.from_orm(task)
        
    except (NotFoundError, ValidationError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create quick task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scheduled task"
        )


@router.get("/", response_model=List[ScheduledTaskRead])
async def list_scheduled_tasks(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    enabled_only: bool = Query(False, description="Only return enabled tasks"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List scheduled tasks for the current user.
    
    Returns all scheduled tasks owned by the current user, optionally
    filtered by project and enabled status.
    """
    try:
        service = ScheduledTaskService(db)
        tasks = await service.get_user_tasks(
            user=current_user,
            project_id=project_id,
            enabled_only=enabled_only
        )
        return [ScheduledTaskRead.from_orm(task) for task in tasks]
        
    except Exception as e:
        logger.error(f"Failed to list scheduled tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list scheduled tasks"
        )


@router.get("/projects/{project_id}", response_model=List[ScheduledTaskRead])
async def list_project_tasks(
    project_id: UUID,
    enabled_only: bool = Query(False, description="Only return enabled tasks"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List scheduled tasks for a specific project.
    
    Returns all scheduled tasks for the specified project that the
    current user has access to.
    """
    try:
        service = ScheduledTaskService(db)
        tasks = await service.get_project_tasks(
            user=current_user,
            project_id=project_id,
            enabled_only=enabled_only
        )
        return [ScheduledTaskRead.from_orm(task) for task in tasks]
        
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list project tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list project tasks"
        )


@router.get("/{task_id}", response_model=ScheduledTaskWithRuns)
async def get_scheduled_task(
    task_id: UUID,
    include_runs: bool = Query(True, description="Include execution history"),
    run_limit: int = Query(50, ge=1, le=200, description="Maximum runs to include"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific scheduled task with execution history.
    
    Returns detailed information about a scheduled task including
    recent execution history if requested.
    """
    try:
        service = ScheduledTaskService(db)
        
        if include_runs:
            task = await service.get_task_with_runs(
                user=current_user,
                task_id=task_id,
                run_limit=run_limit
            )
            return ScheduledTaskWithRuns.from_orm(task)
        else:
            # Get task without runs for efficiency
            tasks = await service.get_user_tasks(current_user)
            task = next((t for t in tasks if t.id == task_id), None)
            if not task:
                raise NotFoundError("Scheduled task not found")
            return ScheduledTaskWithRuns.from_orm(task)
        
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get scheduled task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduled task"
        )


@router.put("/{task_id}", response_model=ScheduledTaskRead)
async def update_scheduled_task(
    task_id: UUID,
    task_update: ScheduledTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a scheduled task.
    
    Updates the specified scheduled task with the provided data.
    Only the fields included in the request will be updated.
    """
    try:
        service = ScheduledTaskService(db)
        
        # Convert Pydantic model to dict, excluding None values
        updates = task_update.dict(exclude_none=True)
        
        task = await service.update_task(
            user=current_user,
            task_id=task_id,
            **updates
        )
        return ScheduledTaskRead.from_orm(task)
        
    except (NotFoundError, ValidationError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update scheduled task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scheduled task"
        )


@router.delete("/{task_id}")
async def delete_scheduled_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a scheduled task.
    
    Permanently deletes the specified scheduled task and all its
    execution history. This action cannot be undone.
    """
    try:
        service = ScheduledTaskService(db)
        success = await service.delete_task(
            user=current_user,
            task_id=task_id
        )
        
        if success:
            return {"message": "Scheduled task deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete scheduled task"
            )
        
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete scheduled task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete scheduled task"
        )


@router.post("/{task_id}/execute")
async def execute_task_now(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a scheduled task immediately.
    
    Triggers an immediate execution of the specified task, regardless
    of its schedule. This does not affect the normal scheduled executions.
    """
    try:
        service = ScheduledTaskService(db)
        
        # Verify task ownership
        task = await service.get_task_with_runs(
            user=current_user,
            task_id=task_id,
            run_limit=1
        )
        
        # Execute the task
        run = await service.execute_task(task_id)
        
        return {
            "message": "Task execution started",
            "run_id": str(run.id),
            "status": run.status
        }
        
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute task"
        )


@router.post("/{task_id}/enable")
async def enable_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable a scheduled task."""
    try:
        service = ScheduledTaskService(db)
        task = await service.update_task(
            user=current_user,
            task_id=task_id,
            is_enabled=True
        )
        return {"message": "Task enabled successfully", "is_enabled": task.is_enabled}
        
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enable task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable task"
        )


@router.post("/{task_id}/disable")
async def disable_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable a scheduled task."""
    try:
        service = ScheduledTaskService(db)
        task = await service.update_task(
            user=current_user,
            task_id=task_id,
            is_enabled=False
        )
        return {"message": "Task disabled successfully", "is_enabled": task.is_enabled}
        
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to disable task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable task"
        )


@router.post("/validate-schedule", response_model=ScheduleValidationResponse)
async def validate_schedule(
    schedule_data: ScheduleValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Validate a cron schedule expression.
    
    Validates the provided cron expression and returns information
    about when it would execute, including the next few execution times.
    """
    try:
        from croniter import croniter
        from datetime import datetime
        
        # Validate the cron expression
        try:
            cron = croniter(schedule_data.schedule)
            is_valid = True
            error_message = None
        except Exception as e:
            is_valid = False
            error_message = str(e)
            return ScheduleValidationResponse(
                is_valid=is_valid,
                error_message=error_message,
                next_runs=[],
                human_readable=None
            )
        
        # Get next 5 execution times
        next_runs = []
        base_time = datetime.utcnow()
        for _ in range(5):
            next_run = cron.get_next(datetime)
            next_runs.append(next_run)
        
        # Generate human-readable description (simplified)
        human_readable = f"Cron expression: {schedule_data.schedule}"
        
        return ScheduleValidationResponse(
            is_valid=is_valid,
            error_message=error_message,
            next_runs=next_runs,
            human_readable=human_readable
        )
        
    except Exception as e:
        logger.error(f"Failed to validate schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate schedule"
        )


@router.post("/bulk-operations")
async def bulk_task_operations(
    operation_data: BulkTaskOperation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform bulk operations on multiple tasks.
    
    Allows enabling, disabling, or deleting multiple tasks in a single request.
    All tasks must be owned by the current user.
    """
    try:
        service = ScheduledTaskService(db)
        results = []
        errors = []
        
        for task_id in operation_data.task_ids:
            try:
                if operation_data.operation == "enable":
                    await service.update_task(
                        user=current_user,
                        task_id=task_id,
                        is_enabled=True
                    )
                    results.append({"task_id": str(task_id), "status": "enabled"})
                    
                elif operation_data.operation == "disable":
                    await service.update_task(
                        user=current_user,
                        task_id=task_id,
                        is_enabled=False
                    )
                    results.append({"task_id": str(task_id), "status": "disabled"})
                    
                elif operation_data.operation == "delete":
                    await service.delete_task(
                        user=current_user,
                        task_id=task_id
                    )
                    results.append({"task_id": str(task_id), "status": "deleted"})
                    
            except Exception as e:
                errors.append({
                    "task_id": str(task_id),
                    "error": str(e)
                })
        
        return {
            "message": f"Bulk {operation_data.operation} completed",
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Failed to perform bulk operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operations"
        )


@router.get("/stats/overview", response_model=ScheduledTaskStats)
async def get_task_stats(
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get scheduled task statistics.
    
    Returns overview statistics about scheduled tasks for the current user,
    optionally filtered by project.
    """
    try:
        service = ScheduledTaskService(db)
        
        # Get all user tasks (or project tasks if filtered)
        if project_id:
            tasks = await service.get_project_tasks(current_user, project_id)
        else:
            tasks = await service.get_user_tasks(current_user)
        
        # Calculate statistics
        total_tasks = len(tasks)
        enabled_tasks = sum(1 for task in tasks if task.is_enabled)
        disabled_tasks = total_tasks - enabled_tasks
        overdue_tasks = sum(1 for task in tasks if task.is_overdue)
        
        # Calculate today's run statistics (simplified)
        total_runs_today = sum(int(task.total_runs) for task in tasks)
        successful_runs_today = sum(int(task.successful_runs) for task in tasks)
        failed_runs_today = sum(int(task.failed_runs) for task in tasks)
        
        success_rate_today = 0.0
        if total_runs_today > 0:
            success_rate_today = (successful_runs_today / total_runs_today) * 100.0
        
        return ScheduledTaskStats(
            total_tasks=total_tasks,
            enabled_tasks=enabled_tasks,
            disabled_tasks=disabled_tasks,
            overdue_tasks=overdue_tasks,
            total_runs_today=total_runs_today,
            successful_runs_today=successful_runs_today,
            failed_runs_today=failed_runs_today,
            success_rate_today=success_rate_today
        )
        
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task statistics"
        )
