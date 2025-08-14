"""
Task service for managing AI agent tasks and orchestration.

Handles task creation, assignment, progress tracking, and dependencies.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.exceptions import NotFoundError, ValidationError, ServiceError
from modules.backend.models import Task, Project, Agent, User
from modules.backend.models.enums import TaskStatus, TaskPriority, AgentType, TaskType
from modules.backend.repositories import TaskRepository, ProjectRepository, AgentRepository

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
        user_id: UUID,
        title: str,
        description: str,
        task_type: Optional[str] = None,
        complexity: Optional[str] = None,
        parent_task_id: Optional[UUID] = None,
        assigned_agents: Optional[List[str]] = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            project_id: Project ID
            user_id: User creating the task
            title: Task title
            description: Task description
            task_type: Type of task
            complexity: Task complexity
            parent_task_id: Parent task for subtasks
            assigned_agents: Agent types to assign
            
        Returns:
            Created task
            
        Raises:
            NotFoundError: If project or parent task not found
            ValidationError: If validation fails
        """
        # Validate project exists and user has access
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        # Validate parent task if specified
        if parent_task_id:
            parent_task = await self.task_repo.get(parent_task_id)
            if not parent_task:
                raise NotFoundError("Parent task", parent_task_id)
            if parent_task.project_id != project_id:
                raise ValidationError("Parent task must be in the same project")
        
        # Create task
        task = await self.task_repo.create(
            project_id=project_id,
            user_id=user_id,
            title=title,
            description=description,
            task_type=task_type,
            complexity=complexity,
            parent_task_id=parent_task_id,
            status=TaskStatus.PENDING,
            assigned_agents=assigned_agents or []
        )
        
        logger.info(f"Created task '{task.title}' in project {project_id}")
        return task
    
    async def get_task(
        self,
        task_id: UUID,
        user_id: UUID
    ) -> Task:
        """
        Get a task with authorization check.
        
        Args:
            task_id: Task ID
            user_id: User requesting
            
        Returns:
            Task instance
            
        Raises:
            NotFoundError: If task not found
        """
        task = await self.task_repo.get(
            task_id,
            load_relationships=["project", "agent_messages"]
        )
        
        if not task:
            raise NotFoundError("Task", task_id)
        
        # TODO: Add authorization check based on project access
        
        return task
    
    async def list_project_tasks(
        self,
        project_id: UUID,
        user_id: UUID,
        status: Optional[TaskStatus] = None,
        assigned_agent: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Task]:
        """
        List tasks for a project.
        
        Args:
            project_id: Project ID
            user_id: User requesting
            status: Filter by status
            assigned_agent: Filter by assigned agent
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of tasks
        """
        # TODO: Add authorization check
        
        criteria = {"project_id": project_id}
        if status:
            criteria["status"] = status
        if assigned_agent:
            # This would need a more complex query for array contains
            pass
        
        return await self.task_repo.find(
            criteria=criteria,
            skip=skip,
            limit=limit,
            order_by=[("created_at", "desc")]
        )
    
    async def update_task_status(
        self,
        task_id: UUID,
        status: TaskStatus,
        agent_id: Optional[UUID] = None,
        error_message: Optional[str] = None
    ) -> Task:
        """
        Update task status.
        
        Args:
            task_id: Task ID
            status: New status
            agent_id: Agent updating status
            error_message: Error message if failed
            
        Returns:
            Updated task
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        
        update_data = {"status": status}
        
        # Set timestamps based on status
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            update_data["started_at"] = datetime.now(timezone.utc)
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            update_data["completed_at"] = datetime.now(timezone.utc)
            if task.started_at:
                duration = (update_data["completed_at"] - task.started_at).total_seconds()
                update_data["execution_time_seconds"] = int(duration)
        
        if error_message and status == TaskStatus.FAILED:
            update_data["error_message"] = error_message
        
        task = await self.task_repo.update(task_id, **update_data)
        
        logger.info(f"Updated task {task_id} status to {status}")
        return task
    
    async def assign_agent_to_task(
        self,
        task_id: UUID,
        agent_type: str,
        is_primary: bool = False
    ) -> Task:
        """
        Assign an agent to a task.
        
        Args:
            task_id: Task ID
            agent_type: Agent type to assign
            is_primary: Whether this is the primary agent
            
        Returns:
            Updated task
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        
        # Verify agent exists
        agent = await self.agent_repo.get_by_type(agent_type)
        if not agent:
            raise NotFoundError("Agent", agent_type)
        
        # Update assigned agents
        assigned_agents = task.assigned_agents or []
        if agent_type not in assigned_agents:
            assigned_agents.append(agent_type)
        
        update_data = {"assigned_agents": assigned_agents}
        if is_primary:
            update_data["primary_agent"] = agent_type
        
        task = await self.task_repo.update(task_id, **update_data)
        
        logger.info(f"Assigned agent {agent_type} to task {task_id}")
        return task
    
    async def add_task_result(
        self,
        task_id: UUID,
        result_key: str,
        result_value: Any
    ) -> Task:
        """
        Add a result to a task.
        
        Args:
            task_id: Task ID
            result_key: Result key
            result_value: Result value
            
        Returns:
            Updated task
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        
        # Update results
        results = task.results or {}
        results[result_key] = result_value
        
        task = await self.task_repo.update(task_id, results=results)
        
        return task
    
    async def add_generated_file(
        self,
        task_id: UUID,
        file_path: str
    ) -> Task:
        """
        Add a generated file path to a task.
        
        Args:
            task_id: Task ID
            file_path: Generated file path
            
        Returns:
            Updated task
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        
        # Update generated files
        generated_files = task.generated_files or []
        if file_path not in generated_files:
            generated_files.append(file_path)
        
        task = await self.task_repo.update(task_id, generated_files=generated_files)
        
        return task
    
    async def get_subtasks(
        self,
        parent_task_id: UUID
    ) -> List[Task]:
        """
        Get subtasks of a parent task.
        
        Args:
            parent_task_id: Parent task ID
            
        Returns:
            List of subtasks
        """
        return await self.task_repo.find(
            criteria={"parent_task_id": parent_task_id},
            order_by=[("created_at", "asc")]
        )
    
    async def retry_task(
        self,
        task_id: UUID,
        user_id: UUID
    ) -> Task:
        """
        Retry a failed task.
        
        Args:
            task_id: Task ID
            user_id: User requesting retry
            
        Returns:
            Reset task
        """
        task = await self.get_task(task_id, user_id)
        
        if task.status != TaskStatus.FAILED:
            raise ValidationError("Can only retry failed tasks")
        
        # Reset task
        update_data = {
            "status": TaskStatus.PENDING,
            "started_at": None,
            "completed_at": None,
            "execution_time_seconds": None,
            "error_message": None,
            "retry_count": task.retry_count + 1
        }
        
        task = await self.task_repo.update(task_id, **update_data)
        
        logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")
        return task
    
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
        tasks = await self.task_repo.find(
            criteria={"project_id": project_id}
        )
        
        total = len(tasks)
        by_status = {}
        by_type = {}
        total_execution_time = 0
        failed_tasks = []
        
        for task in tasks:
            # Count by status
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by type
            task_type = task.task_type or "unspecified"
            by_type[task_type] = by_type.get(task_type, 0) + 1
            
            # Sum execution time
            if task.execution_time_seconds:
                total_execution_time += task.execution_time_seconds
            
            # Track failed tasks
            if task.status == TaskStatus.FAILED:
                failed_tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "error": task.error_message
                })
        
        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "total_execution_time_seconds": total_execution_time,
            "average_execution_time_seconds": total_execution_time / total if total > 0 else 0,
            "completion_rate": by_status.get(TaskStatus.COMPLETED.value, 0) / total if total > 0 else 0,
            "failed_tasks": failed_tasks[:5]  # Top 5 failed tasks
        }
    
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