"""
Task service for managing AI agent tasks and orchestration.

Handles task creation, assignment, progress tracking, and dependencies.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ValidationError, ServiceError
from models import Task, Project, Agent
from models.enums import TaskStatus, TaskPriority, AgentType
from repositories import TaskRepository, ProjectRepository, AgentRepository

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task-related business operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize task service with database session."""
        self.db = db
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.agent_repo = AgentRepository(db)
    
    async def create_task(
        self,
        project_id: UUID,
        title: str,
        description: str,
        agent_type: AgentType,
        priority: TaskPriority = TaskPriority.MEDIUM,
        parent_task_id: Optional[UUID] = None,
        dependencies: Optional[List[UUID]] = None,
        estimated_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            project_id: Project ID
            title: Task title
            description: Task description
            agent_type: Type of agent for the task
            priority: Task priority
            parent_task_id: Parent task for subtasks
            dependencies: List of task IDs this depends on
            estimated_tokens: Estimated tokens needed
            metadata: Additional task metadata
            
        Returns:
            Created task
            
        Raises:
            NotFoundError: If project not found
            ValidationError: If validation fails
        """
        # Verify project exists
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        # Validate parent task if provided
        if parent_task_id:
            parent = await self.task_repo.get(parent_task_id)
            if not parent or parent.project_id != project_id:
                raise ValidationError("Invalid parent task")
        
        # Validate dependencies
        if dependencies:
            for dep_id in dependencies:
                dep = await self.task_repo.get(dep_id)
                if not dep or dep.project_id != project_id:
                    raise ValidationError(f"Invalid dependency: {dep_id}")
        
        # Create task
        task = await self.task_repo.create_task(
            project_id=project_id,
            title=title,
            description=description,
            agent_type=agent_type,
            priority=priority,
            parent_task_id=parent_task_id,
            dependencies=dependencies or [],
            estimated_tokens=estimated_tokens,
            metadata=metadata
        )
        
        logger.info(f"Created task '{task.title}' for project {project_id}")
        return task
    
    async def get_task(self, task_id: UUID) -> Task:
        """
        Get task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task instance
            
        Raises:
            NotFoundError: If task not found
        """
        task = await self.task_repo.get(
            task_id,
            load_relationships=["project", "agent", "parent_task"]
        )
        if not task:
            raise NotFoundError("Task", task_id)
        return task
    
    async def get_project_tasks(
        self,
        project_id: UUID,
        status: Optional[TaskStatus] = None,
        agent_type: Optional[AgentType] = None,
        include_subtasks: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> List[Task]:
        """
        Get tasks for a project.
        
        Args:
            project_id: Project ID
            status: Filter by status
            agent_type: Filter by agent type
            include_subtasks: Include subtasks
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of tasks
        """
        filters = {"project_id": project_id}
        
        if status:
            filters["status"] = status
        if agent_type:
            filters["agent_type"] = agent_type
        if not include_subtasks:
            filters["parent_task_id"] = None
        
        return await self.task_repo.list(
            filters,
            skip=skip,
            limit=limit,
            order_by="created_at",
            order_desc=True,
            load_relationships=["agent"]
        )
    
    async def assign_task(
        self,
        task_id: UUID,
        agent_id: Optional[UUID] = None
    ) -> Task:
        """
        Assign a task to an agent.
        
        Args:
            task_id: Task to assign
            agent_id: Specific agent to assign to (optional)
            
        Returns:
            Updated task
            
        Raises:
            ServiceError: If assignment fails
        """
        task = await self.get_task(task_id)
        
        # Check if task can be assigned
        if task.status not in [TaskStatus.PENDING, TaskStatus.FAILED]:
            raise ValidationError(f"Cannot assign task in {task.status.value} status")
        
        # Check dependencies
        if not await self._can_start_task(task):
            raise ValidationError("Task has unresolved dependencies")
        
        # Get or find agent
        if agent_id:
            agent = await self.agent_repo.get(agent_id)
            if not agent or agent.type != task.agent_type:
                raise ValidationError("Invalid agent for task type")
        else:
            # Find available agent
            agents = await self.agent_repo.list({
                "type": task.agent_type,
                "is_active": True
            })
            
            if not agents:
                raise ServiceError(f"No available {task.agent_type.value} agent")
            
            # Simple load balancing - pick least loaded
            agent = min(agents, key=lambda a: a.current_load)
        
        # Assign task
        task = await self.task_repo.update(
            task_id,
            agent_id=agent.id,
            status=TaskStatus.ASSIGNED,
            assigned_at=datetime.now(timezone.utc)
        )
        
        # Update agent load
        await self.agent_repo.update(
            agent.id,
            current_load=agent.current_load + 1
        )
        
        logger.info(f"Assigned task {task_id} to agent {agent.id}")
        return task
    
    async def start_task(self, task_id: UUID) -> Task:
        """
        Start working on a task.
        
        Args:
            task_id: Task to start
            
        Returns:
            Updated task
        """
        task = await self.get_task(task_id)
        
        if task.status != TaskStatus.ASSIGNED:
            raise ValidationError("Task must be assigned before starting")
        
        task = await self.task_repo.update(
            task_id,
            status=TaskStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"Started task {task_id}")
        return task
    
    async def update_task_progress(
        self,
        task_id: UUID,
        progress_percentage: int,
        progress_message: Optional[str] = None
    ) -> Task:
        """
        Update task progress.
        
        Args:
            task_id: Task to update
            progress_percentage: Progress (0-100)
            progress_message: Optional progress message
            
        Returns:
            Updated task
        """
        if not 0 <= progress_percentage <= 100:
            raise ValidationError("Progress must be between 0 and 100")
        
        updates = {"progress_percentage": progress_percentage}
        
        if progress_message:
            task = await self.get_task(task_id)
            progress_updates = task.progress_updates or []
            progress_updates.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "percentage": progress_percentage,
                "message": progress_message
            })
            updates["progress_updates"] = progress_updates
        
        return await self.task_repo.update(task_id, **updates)
    
    async def complete_task(
        self,
        task_id: UUID,
        result: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None
    ) -> Task:
        """
        Mark task as completed.
        
        Args:
            task_id: Task to complete
            result: Task result data
            tokens_used: Tokens used
            model_used: AI model used
            
        Returns:
            Updated task
        """
        task = await self.get_task(task_id)
        
        if task.status != TaskStatus.IN_PROGRESS:
            raise ValidationError("Task must be in progress to complete")
        
        # Update task
        task = await self.task_repo.update(
            task_id,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
            result=result,
            tokens_used=tokens_used,
            model_used=model_used,
            progress_percentage=100
        )
        
        # Update agent load if assigned
        if task.agent_id:
            agent = await self.agent_repo.get(task.agent_id)
            if agent:
                await self.agent_repo.update(
                    agent.id,
                    current_load=max(0, agent.current_load - 1)
                )
        
        # Check if this unblocks other tasks
        await self._check_dependent_tasks(task_id)
        
        logger.info(f"Completed task {task_id}")
        return task
    
    async def fail_task(
        self,
        task_id: UUID,
        error_message: str,
        can_retry: bool = True
    ) -> Task:
        """
        Mark task as failed.
        
        Args:
            task_id: Task that failed
            error_message: Error description
            can_retry: Whether task can be retried
            
        Returns:
            Updated task
        """
        task = await self.get_task(task_id)
        
        # Update retry info
        retry_count = task.retry_count + 1
        max_retries = task.max_retries or 3
        
        updates = {
            "status": TaskStatus.FAILED,
            "completed_at": datetime.now(timezone.utc),
            "error_message": error_message,
            "retry_count": retry_count
        }
        
        # Check if can retry
        if not can_retry or retry_count >= max_retries:
            updates["status"] = TaskStatus.FAILED
        else:
            updates["status"] = TaskStatus.PENDING  # Ready for retry
        
        task = await self.task_repo.update(task_id, **updates)
        
        # Update agent load if assigned
        if task.agent_id:
            agent = await self.agent_repo.get(task.agent_id)
            if agent:
                await self.agent_repo.update(
                    agent.id,
                    current_load=max(0, agent.current_load - 1)
                )
        
        logger.warning(f"Task {task_id} failed: {error_message}")
        return task
    
    async def get_task_dependencies(
        self,
        task_id: UUID
    ) -> Dict[str, List[Task]]:
        """
        Get task dependencies and dependents.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict with dependencies and dependents
        """
        task = await self.get_task(task_id)
        
        # Get dependencies
        dependencies = []
        for dep_id in task.dependencies:
            dep = await self.task_repo.get(dep_id)
            if dep:
                dependencies.append(dep)
        
        # Get dependents (tasks that depend on this one)
        dependents = await self.task_repo.get_dependent_tasks(task_id)
        
        return {
            "dependencies": dependencies,
            "dependents": dependents
        }
    
    async def get_task_subtasks(
        self,
        task_id: UUID,
        recursive: bool = False
    ) -> List[Task]:
        """
        Get subtasks of a task.
        
        Args:
            task_id: Parent task ID
            recursive: Get all descendants
            
        Returns:
            List of subtasks
        """
        if recursive:
            return await self._get_subtasks_recursive(task_id)
        else:
            return await self.task_repo.list({"parent_task_id": task_id})
    
    async def update_task_metadata(
        self,
        task_id: UUID,
        metadata: Dict[str, Any]
    ) -> Task:
        """
        Update task metadata.
        
        Args:
            task_id: Task to update
            metadata: New metadata
            
        Returns:
            Updated task
        """
        task = await self.get_task(task_id)
        
        # Merge with existing metadata
        current_metadata = task.metadata or {}
        current_metadata.update(metadata)
        
        return await self.task_repo.update(
            task_id,
            metadata=current_metadata
        )
    
    async def get_task_statistics(
        self,
        project_id: UUID
    ) -> Dict[str, Any]:
        """
        Get task statistics for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Task statistics
        """
        return await self.task_repo.get_task_statistics(project_id)
    
    async def _can_start_task(self, task: Task) -> bool:
        """Check if task dependencies are resolved."""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep = await self.task_repo.get(dep_id)
            if not dep or dep.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _check_dependent_tasks(self, completed_task_id: UUID):
        """Check and potentially unblock dependent tasks."""
        dependents = await self.task_repo.get_dependent_tasks(completed_task_id)
        
        for dep_task in dependents:
            if dep_task.status == TaskStatus.BLOCKED:
                # Check if all dependencies are now complete
                if await self._can_start_task(dep_task):
                    await self.task_repo.update(
                        dep_task.id,
                        status=TaskStatus.PENDING
                    )
                    logger.info(f"Unblocked task {dep_task.id}")
    
    async def _get_subtasks_recursive(self, task_id: UUID) -> List[Task]:
        """Recursively get all subtasks."""
        subtasks = []
        direct_subtasks = await self.task_repo.list({"parent_task_id": task_id})
        
        for subtask in direct_subtasks:
            subtasks.append(subtask)
            # Recursively get subtasks
            subtasks.extend(await self._get_subtasks_recursive(subtask.id))
        
        return subtasks 