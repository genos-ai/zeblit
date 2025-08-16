"""
Service for managing scheduled tasks.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial scheduled task service.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from croniter import croniter

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.models.scheduled_task import ScheduledTask, ScheduledTaskRun
from modules.backend.models.user import User
from modules.backend.models.project import Project
from modules.backend.repositories.scheduled_task import (
    ScheduledTaskRepository, 
    ScheduledTaskRunRepository
)
from modules.backend.repositories.project import ProjectRepository
from modules.backend.services.container import ContainerService
from modules.backend.core.exceptions import (
    NotFoundError, 
    ValidationError, 
    ForbiddenError
)

logger = logging.getLogger(__name__)


class ScheduledTaskService:
    """Service for managing scheduled tasks."""
    
    def __init__(self, db: AsyncSession):
        """Initialize scheduled task service."""
        self.db = db
        self.task_repo = ScheduledTaskRepository(db)
        self.run_repo = ScheduledTaskRunRepository(db)
        self.project_repo = ProjectRepository(db)
        self.container_service = ContainerService()
    
    async def create_task(
        self,
        user: User,
        project_id: UUID,
        name: str,
        schedule: str,
        command: str,
        description: Optional[str] = None,
        working_directory: str = "/workspace",
        environment_variables: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        capture_output: bool = True,
        notify_on_failure: bool = True,
        notify_on_success: bool = False
    ) -> ScheduledTask:
        """
        Create a new scheduled task.
        
        Args:
            user: User creating the task
            project_id: Project ID
            name: Task name
            schedule: Cron expression
            command: Command to execute
            description: Optional description
            working_directory: Working directory for execution
            environment_variables: Environment variables for execution
            timeout_seconds: Execution timeout
            max_retries: Maximum retry attempts
            capture_output: Whether to capture stdout/stderr
            notify_on_failure: Send notifications on failure
            notify_on_success: Send notifications on success
            
        Returns:
            Created scheduled task
            
        Raises:
            NotFoundError: If project not found
            ForbiddenError: If user lacks access to project
            ValidationError: If schedule or other parameters are invalid
        """
        # Verify project access
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project not found")
        
        if project.owner_id != user.id:
            raise ForbiddenError("Access denied to project")
        
        # Validate cron expression
        try:
            cron = croniter(schedule)
            next_run = cron.get_next(datetime)
        except Exception as e:
            raise ValidationError(f"Invalid cron expression: {str(e)}")
        
        # Validate command
        if not command.strip():
            raise ValidationError("Command cannot be empty")
        
        # Check for duplicate names in project
        existing_tasks = await self.task_repo.get_project_tasks(project_id)
        if any(task.name == name for task in existing_tasks):
            raise ValidationError(f"Task with name '{name}' already exists in this project")
        
        # Create task
        created_task = await self.task_repo.create(
            name=name,
            description=description,
            user_id=user.id,
            project_id=project_id,
            schedule=schedule,
            command=command,
            working_directory=working_directory,
            environment_variables=environment_variables or {},
            next_run_at=next_run,
            timeout_seconds=str(timeout_seconds),
            max_retries=str(max_retries),
            capture_output=capture_output,
            notify_on_failure=notify_on_failure,
            notify_on_success=notify_on_success
        )
        
        # Schedule with Celery Beat (implementation below)
        await self._schedule_with_celery(created_task)
        
        logger.info(f"Created scheduled task '{name}' for project {project_id}")
        return created_task
    
    async def update_task(
        self,
        user: User,
        task_id: UUID,
        **updates
    ) -> ScheduledTask:
        """
        Update a scheduled task.
        
        Args:
            user: User updating the task
            task_id: Task ID
            **updates: Fields to update
            
        Returns:
            Updated task
            
        Raises:
            NotFoundError: If task not found
            ForbiddenError: If user lacks access
            ValidationError: If updates are invalid
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError("Scheduled task not found")
        
        if task.user_id != user.id:
            raise ForbiddenError("Access denied to task")
        
        # Validate schedule if being updated
        if 'schedule' in updates:
            try:
                croniter(updates['schedule'])
            except Exception as e:
                raise ValidationError(f"Invalid cron expression: {str(e)}")
        
        # Update fields
        for field, value in updates.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        # Recalculate next run if schedule changed
        if 'schedule' in updates:
            cron = croniter(task.schedule)
            task.next_run_at = cron.get_next(datetime)
        
        task.updated_at = datetime.utcnow()
        
        updated_task = await self.task_repo.update(task)
        
        # Update Celery Beat schedule
        await self._schedule_with_celery(updated_task)
        
        logger.info(f"Updated scheduled task {task_id}")
        return updated_task
    
    async def delete_task(
        self,
        user: User,
        task_id: UUID
    ) -> bool:
        """
        Delete a scheduled task.
        
        Args:
            user: User deleting the task
            task_id: Task ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If task not found
            ForbiddenError: If user lacks access
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError("Scheduled task not found")
        
        if task.user_id != user.id:
            raise ForbiddenError("Access denied to task")
        
        # Remove from Celery Beat
        await self._unschedule_from_celery(task)
        
        # Delete task (runs will be cascade deleted)
        success = await self.task_repo.delete(task_id)
        
        logger.info(f"Deleted scheduled task {task_id}")
        return success
    
    async def get_user_tasks(
        self,
        user: User,
        project_id: Optional[UUID] = None,
        enabled_only: bool = False
    ) -> List[ScheduledTask]:
        """Get tasks for a user."""
        return await self.task_repo.get_user_tasks(
            user.id, 
            project_id, 
            enabled_only
        )
    
    async def get_project_tasks(
        self,
        user: User,
        project_id: UUID,
        enabled_only: bool = False
    ) -> List[ScheduledTask]:
        """Get tasks for a project."""
        # Verify project access
        project = await self.project_repo.get(project_id)
        if not project or project.owner_id != user.id:
            raise ForbiddenError("Access denied to project")
        
        return await self.task_repo.get_project_tasks(project_id, enabled_only)
    
    async def get_task_with_runs(
        self,
        user: User,
        task_id: UUID,
        run_limit: int = 50
    ) -> ScheduledTask:
        """Get task with execution history."""
        task = await self.task_repo.get_task_with_runs(task_id, run_limit)
        if not task:
            raise NotFoundError("Scheduled task not found")
        
        if task.user_id != user.id:
            raise ForbiddenError("Access denied to task")
        
        return task
    
    async def execute_task(
        self,
        task_id: UUID,
        retry_attempt: int = 0
    ) -> ScheduledTaskRun:
        """
        Execute a scheduled task.
        
        This method is called by Celery to execute tasks.
        
        Args:
            task_id: Task ID to execute
            retry_attempt: Current retry attempt (0 for first attempt)
            
        Returns:
            Task run record
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError(f"Scheduled task {task_id} not found")
        
        if not task.is_enabled:
            logger.info(f"Skipping disabled task {task_id}")
            return
        
        # Create run record
        created_run = await self.run_repo.create(
            task_id=task_id,
            retry_attempt=str(retry_attempt),
            status="running"
        )
        
        try:
            # Execute in container
            result = await self._execute_in_container(task, created_run)
            
            # Update task statistics
            success = result.get('exit_code', 1) == 0
            await self.task_repo.update_execution_stats(task_id, success)
            
            # Calculate next run time
            await self._calculate_next_run(task)
            
            return created_run
            
        except Exception as e:
            logger.error(f"Failed to execute task {task_id}: {e}")
            
            # Mark run as failed
            await self.run_repo.complete_run(
                created_run.id,
                status="failed",
                error_message=str(e)
            )
            
            # Update task statistics
            await self.task_repo.update_execution_stats(task_id, False)
            
            # Retry if configured
            if retry_attempt < int(task.max_retries):
                logger.info(f"Retrying task {task_id}, attempt {retry_attempt + 1}")
                # Schedule retry (implementation depends on task queue)
                await self._schedule_retry(task, retry_attempt + 1)
            
            raise
    
    async def _execute_in_container(
        self,
        task: ScheduledTask,
        run: ScheduledTaskRun
    ) -> Dict[str, Any]:
        """Execute task command in project container."""
        start_time = datetime.utcnow()
        
        try:
            # Ensure container is running
            container = await self.container_service.get_project_container(
                self.db, 
                task.project_id,
                # We need to get the user, but for now we'll use None and handle in service
                user=None  # TODO: Get user from task.user_id
            )
            
            if not container:
                # Start container if needed
                container = await self.container_service.start_project_container(
                    self.db,
                    task.project_id,
                    user=None  # TODO: Get user from task.user_id
                )
            
            # Execute command
            exit_code, output = await self.container_service.execute_command(
                self.db,
                container.id,
                user=None,  # TODO: Get user from task.user_id
                command=task.command,
                workdir=task.working_directory
            )
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Parse stdout and stderr from output
            # This is simplified - in practice you'd need better output parsing
            stdout = output if exit_code == 0 else ""
            stderr = output if exit_code != 0 else ""
            
            # Update run record
            await self.run_repo.complete_run(
                run.id,
                status="success" if exit_code == 0 else "failed",
                exit_code=exit_code,
                stdout=stdout if task.capture_output else None,
                stderr=stderr if task.capture_output else None,
                container_id=container.container_id,
                execution_duration_ms=duration_ms
            )
            
            # Send notifications if configured
            await self._send_notifications(task, run, exit_code == 0)
            
            return {
                'exit_code': exit_code,
                'output': output,
                'duration_ms': duration_ms
            }
            
        except Exception as e:
            # Calculate duration even on failure
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update run record
            await self.run_repo.complete_run(
                run.id,
                status="failed",
                error_message=str(e),
                execution_duration_ms=duration_ms
            )
            
            raise
    
    async def _calculate_next_run(self, task: ScheduledTask) -> None:
        """Calculate and update next run time."""
        try:
            cron = croniter(task.schedule, task.last_run_at or datetime.utcnow())
            next_run = cron.get_next(datetime)
            await self.task_repo.update_next_run(task.id, next_run)
        except Exception as e:
            logger.error(f"Failed to calculate next run for task {task.id}: {e}")
    
    async def _schedule_with_celery(self, task: ScheduledTask) -> None:
        """Schedule task with Celery Beat (placeholder)."""
        # TODO: Implement Celery Beat integration
        # This would register the task with Celery Beat's dynamic scheduler
        logger.info(f"TODO: Schedule task {task.id} with Celery Beat")
    
    async def _unschedule_from_celery(self, task: ScheduledTask) -> None:
        """Remove task from Celery Beat (placeholder)."""
        # TODO: Implement Celery Beat integration
        # This would remove the task from Celery Beat's scheduler
        logger.info(f"TODO: Unschedule task {task.id} from Celery Beat")
    
    async def _schedule_retry(self, task: ScheduledTask, retry_attempt: int) -> None:
        """Schedule a retry execution (placeholder)."""
        # TODO: Implement retry scheduling
        # This would schedule the task to run again after retry_delay_seconds
        delay_seconds = int(task.retry_delay_seconds)
        logger.info(f"TODO: Schedule retry for task {task.id} in {delay_seconds} seconds")
    
    async def _send_notifications(
        self, 
        task: ScheduledTask, 
        run: ScheduledTaskRun, 
        success: bool
    ) -> None:
        """Send notifications for task completion (placeholder)."""
        if (success and task.notify_on_success) or (not success and task.notify_on_failure):
            # TODO: Implement notification system
            status = "succeeded" if success else "failed"
            logger.info(f"TODO: Send notification - Task '{task.name}' {status}")
    
    async def get_overdue_tasks(self) -> List[ScheduledTask]:
        """Get tasks that are overdue for execution."""
        return await self.task_repo.get_overdue_tasks()
    
    async def cleanup_old_runs(
        self, 
        days_old: int = 30,
        keep_per_task: int = 10
    ) -> int:
        """Clean up old task run records."""
        return await self.run_repo.cleanup_old_runs(days_old, keep_per_task)
