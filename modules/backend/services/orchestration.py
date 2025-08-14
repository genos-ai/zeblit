"""
Orchestration service for coordinating multi-agent workflows.

This service provides high-level orchestration of agent tasks,
managing complex workflows and ensuring proper task execution.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from modules.backend.core.database import get_db
from modules.backend.models.task import Task, TaskStatus, TaskType
from modules.backend.models.agent import AgentType
from modules.backend.models.user import User
from modules.backend.models.project import Project
from modules.backend.repositories.task import TaskRepository
from modules.backend.repositories.project import ProjectRepository
from modules.backend.tasks.orchestration_tasks import (
    create_development_workflow,
    execute_parallel_tasks
)
from modules.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


class OrchestrationService:
    """Service for orchestrating multi-agent workflows."""
    
    def __init__(self, db):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
    
    async def start_development_workflow(
        self,
        project_id: UUID,
        requirements: str,
        user: User
    ) -> Dict[str, Any]:
        """
        Start a complete development workflow for implementing requirements.
        
        This creates a multi-stage workflow where agents collaborate
        to implement the given requirements.
        
        Args:
            project_id: Project to work on
            requirements: User requirements to implement
            user: User requesting the work
            
        Returns:
            Workflow information including workflow ID and tracking info
        """
        with log_operation("start_development_workflow", project_id=str(project_id)):
            try:
                # Verify project exists and user has access
                project = await self.project_repo.get(project_id)
                if not project:
                    raise ValueError(f"Project {project_id} not found")
                
                if project.owner_id != user.id:
                    raise ValueError("User does not have access to this project")
                
                # Start the workflow asynchronously
                result = create_development_workflow.delay(
                    str(project_id),
                    requirements,
                    str(user.id)
                )
                
                logger.info(
                    "Started development workflow",
                    project_id=str(project_id),
                    workflow_id=result.id
                )
                
                return {
                    "workflow_id": result.id,
                    "project_id": str(project_id),
                    "status": "started",
                    "message": "Development workflow has been started. Agents are now working on your requirements."
                }
                
            except Exception as e:
                logger.error(
                    "Failed to start development workflow",
                    project_id=str(project_id),
                    error=str(e),
                    exc_info=True
                )
                raise
    
    async def create_simple_task_chain(
        self,
        project_id: UUID,
        task_chain: List[Dict[str, Any]],
        user: User
    ) -> List[Task]:
        """
        Create a simple chain of tasks to be executed sequentially.
        
        Args:
            project_id: Project context
            task_chain: List of task definitions, each containing:
                - agent_type: Type of agent to handle the task
                - title: Task title
                - description: Task description
                - depends_on: Optional list of task indices this depends on
            user: User creating the tasks
            
        Returns:
            List of created tasks
        """
        with log_operation("create_simple_task_chain", project_id=str(project_id)):
            created_tasks = []
            
            try:
                for i, task_def in enumerate(task_chain):
                    # Determine parent task
                    parent_task_id = None
                    if i > 0 and task_def.get("depends_on") is None:
                        # Default to depending on previous task
                        parent_task_id = created_tasks[i-1].id
                    elif task_def.get("depends_on") is not None:
                        # Use specified dependency
                        dep_index = task_def["depends_on"]
                        if 0 <= dep_index < len(created_tasks):
                            parent_task_id = created_tasks[dep_index].id
                    
                    # Create task
                    task = await self.task_repo.create(
                        project_id=project_id,
                        agent_type=AgentType(task_def["agent_type"]),
                        title=task_def["title"],
                        description=task_def["description"],
                        task_type=task_def.get("task_type", TaskType.IMPLEMENTATION),
                        created_by=user.id,
                        parent_task_id=parent_task_id,
                        metadata=task_def.get("metadata", {})
                    )
                    
                    created_tasks.append(task)
                
                logger.info(
                    "Created task chain",
                    project_id=str(project_id),
                    task_count=len(created_tasks)
                )
                
                return created_tasks
                
            except Exception as e:
                logger.error(
                    "Failed to create task chain",
                    project_id=str(project_id),
                    error=str(e),
                    exc_info=True
                )
                # Clean up any created tasks
                for task in created_tasks:
                    await self.db.delete(task)
                await self.db.commit()
                raise
    
    async def execute_parallel_agent_tasks(
        self,
        tasks: List[Task]
    ) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel using different agents.
        
        Args:
            tasks: List of tasks to execute in parallel
            
        Returns:
            Execution results
        """
        with log_operation("execute_parallel_agent_tasks", task_count=len(tasks)):
            try:
                # Prepare task configurations
                task_configs = [
                    {
                        "task_id": str(task.id),
                        "agent_type": task.agent_type.value,
                        "project_id": str(task.project_id) if task.project_id else None
                    }
                    for task in tasks
                ]
                
                # Execute in parallel
                result = execute_parallel_tasks.delay(task_configs)
                
                logger.info(
                    "Started parallel task execution",
                    task_count=len(tasks),
                    celery_task_id=result.id
                )
                
                return {
                    "execution_id": result.id,
                    "task_count": len(tasks),
                    "status": "running",
                    "tasks": [str(task.id) for task in tasks]
                }
                
            except Exception as e:
                logger.error(
                    "Failed to execute parallel tasks",
                    error=str(e),
                    exc_info=True
                )
                raise
    
    async def get_workflow_status(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of a running workflow.
        
        Args:
            workflow_id: Celery task ID of the workflow
            
        Returns:
            Workflow status information
        """
        from celery.result import AsyncResult
        
        try:
            result = AsyncResult(workflow_id)
            
            status = {
                "workflow_id": workflow_id,
                "state": result.state,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "failed": result.failed() if result.ready() else None
            }
            
            if result.ready():
                try:
                    status["result"] = result.result
                except Exception as e:
                    status["error"] = str(e)
            
            if result.state == "PENDING":
                status["info"] = "Workflow is waiting to start"
            elif result.state == "STARTED":
                status["info"] = "Workflow is running"
            elif result.state == "SUCCESS":
                status["info"] = "Workflow completed successfully"
            elif result.state == "FAILURE":
                status["info"] = "Workflow failed"
                if result.info:
                    status["error"] = str(result.info)
            
            return status
            
        except Exception as e:
            logger.error(
                "Failed to get workflow status",
                workflow_id=workflow_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def cancel_workflow(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: Celery task ID of the workflow
            
        Returns:
            Cancellation result
        """
        from celery.result import AsyncResult
        
        try:
            result = AsyncResult(workflow_id)
            result.revoke(terminate=True)
            
            logger.info("Cancelled workflow", workflow_id=workflow_id)
            
            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "message": "Workflow has been cancelled"
            }
            
        except Exception as e:
            logger.error(
                "Failed to cancel workflow",
                workflow_id=workflow_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def get_agent_workload(
        self,
        agent_type: Optional[AgentType] = None
    ) -> Dict[str, Any]:
        """
        Get current workload for agents.
        
        Args:
            agent_type: Optional specific agent type to check
            
        Returns:
            Workload information by agent type
        """
        try:
            # Build query
            query = self.db.query(Task).filter(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
            
            if agent_type:
                query = query.filter(Task.agent_type == agent_type)
            
            # Get tasks
            tasks = await self.db.execute(query)
            tasks = tasks.scalars().all()
            
            # Group by agent type
            workload = {}
            for task in tasks:
                agent_key = task.agent_type.value
                if agent_key not in workload:
                    workload[agent_key] = {
                        "pending": 0,
                        "in_progress": 0,
                        "total": 0
                    }
                
                if task.status == TaskStatus.PENDING:
                    workload[agent_key]["pending"] += 1
                elif task.status == TaskStatus.IN_PROGRESS:
                    workload[agent_key]["in_progress"] += 1
                
                workload[agent_key]["total"] += 1
            
            return workload
            
        except Exception as e:
            logger.error(
                "Failed to get agent workload",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def rerun_failed_task(
        self,
        task_id: UUID,
        user: User
    ) -> Task:
        """
        Rerun a failed task.
        
        Args:
            task_id: ID of the failed task
            user: User requesting the rerun
            
        Returns:
            New task created for the rerun
        """
        with log_operation("rerun_failed_task", task_id=str(task_id)):
            try:
                # Get original task
                original_task = await self.task_repo.get(task_id)
                if not original_task:
                    raise ValueError(f"Task {task_id} not found")
                
                if original_task.status != TaskStatus.FAILED:
                    raise ValueError("Can only rerun failed tasks")
                
                # Create new task as a copy
                new_task = await self.task_repo.create(
                    project_id=original_task.project_id,
                    agent_type=original_task.agent_type,
                    title=f"Retry: {original_task.title}",
                    description=original_task.description,
                    task_type=original_task.task_type,
                    created_by=user.id,
                    parent_task_id=original_task.parent_task_id,
                    metadata={
                        **original_task.metadata,
                        "retry_of": str(original_task.id),
                        "retry_count": original_task.metadata.get("retry_count", 0) + 1
                    }
                )
                
                logger.info(
                    "Created retry task",
                    original_task_id=str(task_id),
                    new_task_id=str(new_task.id)
                )
                
                return new_task
                
            except Exception as e:
                logger.error(
                    "Failed to rerun task",
                    task_id=str(task_id),
                    error=str(e),
                    exc_info=True
                )
                raise 