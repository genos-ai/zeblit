"""
Task repository for managing AI agent tasks.

Provides task-specific database operations including assignment,
progress tracking, and task analytics.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, or_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import logging

from modules.backend.models import Task
from modules.backend.models.enums import TaskStatus, TaskPriority, AgentType
from .base import BaseRepository

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository[Task]):
    """Repository for task-related database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize task repository."""
        super().__init__(Task, db)
    
    async def create_task(
        self,
        project_id: UUID,
        user_id: UUID,
        title: str,
        description: Optional[str] = None,
        task_type: str = "development",
        priority: TaskPriority = TaskPriority.MEDIUM,
        parent_task_id: Optional[UUID] = None,
        assigned_agent_id: Optional[UUID] = None,
        dependencies: Optional[List[UUID]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            project_id: Project's ID
            user_id: User who created the task
            title: Task title
            description: Task description
            task_type: Type of task (development, review, etc.)
            priority: Task priority
            parent_task_id: Parent task for subtasks
            assigned_agent_id: Agent assigned to the task
            dependencies: List of task IDs this depends on
            metadata: Additional task metadata
            
        Returns:
            Created task instance
        """
        task = await self.create(
            project_id=project_id,
            user_id=user_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            parent_task_id=parent_task_id,
            assigned_agent_id=assigned_agent_id,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        logger.info(f"Created task: {task.title} (ID: {task.id})")
        return task
    
    async def get_project_tasks(
        self,
        project_id: UUID,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_agent_id: Optional[UUID] = None,
        parent_task_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Task]:
        """
        Get tasks for a project with optional filters.
        
        Args:
            project_id: Project's ID
            status: Optional status filter
            priority: Optional priority filter
            assigned_agent_id: Optional agent filter
            parent_task_id: Optional parent task filter (None for root tasks)
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of tasks
        """
        query = select(Task).where(Task.project_id == project_id)
        
        # Add filters
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assigned_agent_id:
            query = query.where(Task.assigned_agent_id == assigned_agent_id)
        if parent_task_id is not None:
            query = query.where(Task.parent_task_id == parent_task_id)
        
        # Add ordering and pagination
        query = (
            query
            .options(
                selectinload(Task.assigned_agent),
                selectinload(Task.parent_task)
            )
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_agent_tasks(
        self,
        agent_id: UUID,
        status: Optional[TaskStatus] = None,
        limit: int = 20
    ) -> List[Task]:
        """
        Get tasks assigned to an agent.
        
        Args:
            agent_id: Agent's ID
            status: Optional status filter
            limit: Maximum tasks to return
            
        Returns:
            List of agent's tasks
        """
        filters = {"assigned_agent_id": agent_id}
        if status:
            filters["status"] = status
        
        return await self.get_many(
            filters=filters,
            limit=limit,
            order_by="priority",
            order_desc=True,
            load_relationships=["project", "user"]
        )
    
    async def assign_task(
        self,
        task_id: UUID,
        agent_id: UUID
    ) -> Optional[Task]:
        """
        Assign a task to an agent.
        
        Args:
            task_id: Task's ID
            agent_id: Agent's ID
            
        Returns:
            Updated task or None if not found
        """
        return await self.update(
            task_id,
            assigned_agent_id=agent_id,
            assigned_at=datetime.now(timezone.utc),
            status=TaskStatus.ASSIGNED
        )
    
    async def update_task_status(
        self,
        task_id: UUID,
        status: TaskStatus,
        progress_percentage: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """
        Update task status and progress.
        
        Args:
            task_id: Task's ID
            status: New status
            progress_percentage: Optional progress (0-100)
            result: Optional task result
            error_message: Optional error message
            
        Returns:
            Updated task or None if not found
        """
        updates = {"status": status}
        
        # Add optional updates
        if progress_percentage is not None:
            updates["progress_percentage"] = max(0, min(100, progress_percentage))
        
        # Handle status-specific updates
        if status == TaskStatus.IN_PROGRESS and "started_at" not in updates:
            updates["started_at"] = datetime.now(timezone.utc)
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            updates["completed_at"] = datetime.now(timezone.utc)
            if result:
                updates["result"] = result
            if error_message:
                updates["error_message"] = error_message
        
        task = await self.update(task_id, **updates)
        
        if task:
            logger.info(f"Updated task {task_id} status to {status}")
        
        return task
    
    async def get_task_with_subtasks(
        self,
        task_id: UUID,
        max_depth: int = 3
    ) -> Optional[Task]:
        """
        Get task with its subtask hierarchy.
        
        Args:
            task_id: Task's ID
            max_depth: Maximum depth to load
            
        Returns:
            Task with subtasks loaded or None
        """
        # This is a simplified version - in production you might want
        # to use a recursive CTE for better performance
        task = await self.get(
            task_id,
            load_relationships=["subtasks", "assigned_agent", "project"]
        )
        
        if not task:
            return None
        
        # Recursively load subtasks up to max_depth
        async def load_subtasks(parent_task: Task, depth: int):
            if depth >= max_depth or not parent_task.subtasks:
                return
            
            for subtask in parent_task.subtasks:
                # Load subtask's subtasks
                subtask_full = await self.get(
                    subtask.id,
                    load_relationships=["subtasks", "assigned_agent"]
                )
                if subtask_full:
                    subtask.subtasks = subtask_full.subtasks
                    await load_subtasks(subtask, depth + 1)
        
        await load_subtasks(task, 1)
        return task
    
    async def get_ready_tasks(
        self,
        project_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Task]:
        """
        Get tasks that are ready to be worked on (no pending dependencies).
        
        Args:
            project_id: Optional project filter
            limit: Maximum tasks to return
            
        Returns:
            List of ready tasks
        """
        query = select(Task).where(
            Task.status.in_([TaskStatus.PENDING, TaskStatus.ASSIGNED])
        )
        
        if project_id:
            query = query.where(Task.project_id == project_id)
        
        # TODO: Add dependency checking logic
        # For now, we'll just return tasks without dependencies
        query = query.where(
            or_(
                Task.dependencies == None,
                func.array_length(Task.dependencies, 1) == 0
            )
        )
        
        query = (
            query
            .options(selectinload(Task.assigned_agent))
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_blocked_tasks(
        self,
        project_id: Optional[UUID] = None
    ) -> List[Task]:
        """
        Get tasks that are blocked by dependencies or errors.
        
        Args:
            project_id: Optional project filter
            
        Returns:
            List of blocked tasks
        """
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        
        # Get tasks with dependencies or in blocked/failed state
        tasks = await self.get_many(
            filters=filters,
            load_relationships=["assigned_agent"]
        )
        
        blocked = []
        for task in tasks:
            if task.status == TaskStatus.BLOCKED:
                blocked.append(task)
            elif task.status == TaskStatus.FAILED and task.retry_count < task.max_retries:
                blocked.append(task)
            elif task.dependencies:
                # Check if any dependencies are not completed
                # This is simplified - in production you'd want a more efficient query
                for dep_id in task.dependencies:
                    dep_task = await self.get(dep_id)
                    if dep_task and dep_task.status != TaskStatus.COMPLETED:
                        blocked.append(task)
                        break
        
        return blocked
    
    async def update_task_metrics(
        self,
        task_id: UUID,
        execution_time_ms: int,
        tokens_used: int,
        cost_usd: float
    ) -> Optional[Task]:
        """
        Update task execution metrics.
        
        Args:
            task_id: Task's ID
            execution_time_ms: Execution time in milliseconds
            tokens_used: Tokens used by AI
            cost_usd: Cost in USD
            
        Returns:
            Updated task or None
        """
        task = await self.get(task_id)
        if not task:
            return None
        
        return await self.update(
            task_id,
            execution_time_ms=execution_time_ms,
            tokens_used=(task.tokens_used or 0) + tokens_used,
            cost_usd=(task.cost_usd or 0) + cost_usd
        )
    
    async def retry_task(
        self,
        task_id: UUID
    ) -> Optional[Task]:
        """
        Retry a failed task.
        
        Args:
            task_id: Task's ID
            
        Returns:
            Updated task or None
        """
        task = await self.get(task_id)
        if not task or task.status != TaskStatus.FAILED:
            return None
        
        if task.retry_count >= task.max_retries:
            logger.warning(f"Task {task_id} has exceeded max retries")
            return None
        
        return await self.update(
            task_id,
            status=TaskStatus.PENDING,
            retry_count=task.retry_count + 1,
            error_message=None,
            assigned_agent_id=None,  # Unassign for fresh assignment
            started_at=None,
            completed_at=None
        )
    
    async def get_task_statistics(
        self,
        project_id: UUID
    ) -> Dict[str, Any]:
        """
        Get task statistics for a project.
        
        Args:
            project_id: Project's ID
            
        Returns:
            Dictionary with task statistics
        """
        # Get all project tasks
        tasks = await self.get_many(
            filters={"project_id": project_id},
            limit=10000  # Get all
        )
        
        # Calculate statistics
        total_tasks = len(tasks)
        
        # Status distribution
        status_counts = {}
        for task in tasks:
            status = task.status.value
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        # Priority distribution
        priority_counts = {}
        for task in tasks:
            priority = task.priority.value
            if priority not in priority_counts:
                priority_counts[priority] = 0
            priority_counts[priority] += 1
        
        # Calculate completion rate
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        completion_rate = completed / total_tasks if total_tasks > 0 else 0
        
        # Calculate average execution time
        completed_tasks = [t for t in tasks if t.execution_time_ms]
        avg_execution_time = (
            sum(t.execution_time_ms for t in completed_tasks) / len(completed_tasks)
            if completed_tasks else 0
        )
        
        # Calculate costs
        total_cost = sum(t.cost_usd or 0 for t in tasks)
        total_tokens = sum(t.tokens_used or 0 for t in tasks)
        
        # Agent performance
        agent_stats = {}
        for task in tasks:
            if task.assigned_agent_id:
                agent_id = str(task.assigned_agent_id)
                if agent_id not in agent_stats:
                    agent_stats[agent_id] = {
                        "total": 0,
                        "completed": 0,
                        "failed": 0
                    }
                agent_stats[agent_id]["total"] += 1
                if task.status == TaskStatus.COMPLETED:
                    agent_stats[agent_id]["completed"] += 1
                elif task.status == TaskStatus.FAILED:
                    agent_stats[agent_id]["failed"] += 1
        
        return {
            "total_tasks": total_tasks,
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "completion_rate": completion_rate,
            "completed_tasks": completed,
            "failed_tasks": status_counts.get("failed", 0),
            "blocked_tasks": status_counts.get("blocked", 0),
            "average_execution_time_ms": avg_execution_time,
            "total_cost_usd": total_cost,
            "total_tokens_used": total_tokens,
            "agent_performance": agent_stats
        } 