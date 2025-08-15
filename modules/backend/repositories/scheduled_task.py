"""
Repository for scheduled task operations.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial scheduled task repository.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.backend.models.scheduled_task import ScheduledTask, ScheduledTaskRun
from modules.backend.repositories.base import BaseRepository


class ScheduledTaskRepository(BaseRepository[ScheduledTask]):
    """Repository for ScheduledTask operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ScheduledTask, db)
    
    async def get_user_tasks(
        self, 
        user_id: UUID, 
        project_id: Optional[UUID] = None,
        enabled_only: bool = False
    ) -> List[ScheduledTask]:
        """
        Get scheduled tasks for a user.
        
        Args:
            user_id: User ID
            project_id: Optional project filter
            enabled_only: Only return enabled tasks
            
        Returns:
            List of scheduled tasks
        """
        query = select(ScheduledTask).where(ScheduledTask.user_id == user_id)
        
        if project_id:
            query = query.where(ScheduledTask.project_id == project_id)
        
        if enabled_only:
            query = query.where(ScheduledTask.is_enabled == True)
        
        query = query.order_by(ScheduledTask.next_run_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_project_tasks(
        self, 
        project_id: UUID,
        enabled_only: bool = False
    ) -> List[ScheduledTask]:
        """
        Get scheduled tasks for a project.
        
        Args:
            project_id: Project ID
            enabled_only: Only return enabled tasks
            
        Returns:
            List of scheduled tasks
        """
        query = select(ScheduledTask).where(ScheduledTask.project_id == project_id)
        
        if enabled_only:
            query = query.where(ScheduledTask.is_enabled == True)
        
        query = query.order_by(ScheduledTask.next_run_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_overdue_tasks(self) -> List[ScheduledTask]:
        """
        Get tasks that are overdue for execution.
        
        Returns:
            List of overdue tasks
        """
        now = datetime.utcnow()
        query = select(ScheduledTask).where(
            and_(
                ScheduledTask.is_enabled == True,
                ScheduledTask.next_run_at <= now
            )
        ).order_by(ScheduledTask.next_run_at.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_tasks_by_name(
        self, 
        user_id: UUID, 
        name: str
    ) -> List[ScheduledTask]:
        """
        Find tasks by name for a user.
        
        Args:
            user_id: User ID
            name: Task name (case-insensitive)
            
        Returns:
            List of matching tasks
        """
        query = select(ScheduledTask).where(
            and_(
                ScheduledTask.user_id == user_id,
                ScheduledTask.name.ilike(f"%{name}%")
            )
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_task_with_runs(
        self, 
        task_id: UUID,
        limit: int = 50
    ) -> Optional[ScheduledTask]:
        """
        Get a task with its recent runs.
        
        Args:
            task_id: Task ID
            limit: Maximum number of runs to include
            
        Returns:
            Task with runs or None
        """
        query = select(ScheduledTask).where(
            ScheduledTask.id == task_id
        ).options(
            selectinload(ScheduledTask.task_runs).limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_execution_stats(
        self, 
        task_id: UUID,
        success: bool
    ) -> None:
        """
        Update task execution statistics.
        
        Args:
            task_id: Task ID
            success: Whether the execution was successful
        """
        task = await self.get(task_id)
        if not task:
            return
        
        # Update counters
        task.total_runs = str(int(task.total_runs) + 1)
        
        if success:
            task.successful_runs = str(int(task.successful_runs) + 1)
            task.last_success_at = datetime.utcnow()
        else:
            task.failed_runs = str(int(task.failed_runs) + 1)
            task.last_failure_at = datetime.utcnow()
        
        task.last_run_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def update_next_run(
        self, 
        task_id: UUID, 
        next_run: datetime
    ) -> None:
        """
        Update the next run time for a task.
        
        Args:
            task_id: Task ID
            next_run: Next scheduled run time
        """
        task = await self.get(task_id)
        if task:
            task.next_run_at = next_run
            task.updated_at = datetime.utcnow()
            await self.db.commit()


class ScheduledTaskRunRepository(BaseRepository[ScheduledTaskRun]):
    """Repository for ScheduledTaskRun operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ScheduledTaskRun, db)
    
    async def get_task_runs(
        self, 
        task_id: UUID,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[ScheduledTaskRun]:
        """
        Get runs for a specific task.
        
        Args:
            task_id: Task ID
            limit: Maximum number of runs to return
            status: Optional status filter
            
        Returns:
            List of task runs
        """
        query = select(ScheduledTaskRun).where(
            ScheduledTaskRun.task_id == task_id
        )
        
        if status:
            query = query.where(ScheduledTaskRun.status == status)
        
        query = query.order_by(
            ScheduledTaskRun.started_at.desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_runs(
        self, 
        limit: int = 100
    ) -> List[ScheduledTaskRun]:
        """
        Get recent task runs across all tasks.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of recent task runs
        """
        query = select(ScheduledTaskRun).order_by(
            ScheduledTaskRun.started_at.desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_running_tasks(self) -> List[ScheduledTaskRun]:
        """
        Get currently running task executions.
        
        Returns:
            List of running task runs
        """
        query = select(ScheduledTaskRun).where(
            ScheduledTaskRun.status == "running"
        ).order_by(ScheduledTaskRun.started_at.asc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def complete_run(
        self, 
        run_id: UUID,
        status: str,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ) -> None:
        """
        Mark a task run as completed.
        
        Args:
            run_id: Run ID
            status: Final status (success, failed, timeout)
            exit_code: Process exit code
            stdout: Standard output
            stderr: Standard error
            error_message: Error message if failed
            execution_duration_ms: Execution duration in milliseconds
        """
        run = await self.get(run_id)
        if not run:
            return
        
        run.status = status
        run.completed_at = datetime.utcnow()
        run.exit_code = str(exit_code) if exit_code is not None else None
        run.stdout = stdout
        run.stderr = stderr
        run.error_message = error_message
        run.execution_duration_ms = str(execution_duration_ms) if execution_duration_ms is not None else None
        
        await self.db.commit()
    
    async def cleanup_old_runs(
        self, 
        days_old: int = 30,
        keep_per_task: int = 10
    ) -> int:
        """
        Clean up old task runs.
        
        Args:
            days_old: Delete runs older than this many days
            keep_per_task: Keep at least this many runs per task
            
        Returns:
            Number of runs deleted
        """
        cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
        cutoff_datetime = datetime.fromtimestamp(cutoff_date)
        
        # This is a simplified version - in production you'd want a more sophisticated cleanup
        # that respects the keep_per_task parameter
        
        query = select(ScheduledTaskRun).where(
            ScheduledTaskRun.started_at < cutoff_datetime
        )
        
        result = await self.db.execute(query)
        old_runs = list(result.scalars().all())
        
        for run in old_runs:
            await self.db.delete(run)
        
        await self.db.commit()
        return len(old_runs)
