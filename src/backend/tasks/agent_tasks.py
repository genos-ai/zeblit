"""
Celery tasks for agent operations.

These tasks handle the execution of agent work in a distributed manner.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from celery import Task

from src.backend.core.celery_app import celery_app
from src.backend.core.database import get_db_context
from src.backend.agents import AgentFactory
from src.backend.models.agent import AgentType
from src.backend.models.task import Task as TaskModel, TaskStatus
from src.backend.repositories.task import TaskRepository
from src.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


class AgentTask(Task):
    """Base class for agent tasks with database session management."""
    
    def __init__(self):
        self._db = None
    
    async def get_db(self):
        """Get database session."""
        if self._db is None:
            self._db = get_db_context()
        return self._db.__aenter__()


@celery_app.task(bind=True, base=AgentTask, name="agent.process_task")
async def process_agent_task(
    self,
    task_id: str,
    agent_type: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a task with the specified agent.
    
    Args:
        task_id: ID of the task to process
        agent_type: Type of agent to use
        project_id: Optional project context
        
    Returns:
        Task result dictionary
    """
    with log_operation("process_agent_task", task_id=task_id, agent_type=agent_type):
        try:
            # Get database session
            async with get_db_context() as db:
                # Load task
                task_repo = TaskRepository(db)
                task = await task_repo.get(UUID(task_id))
                
                if not task:
                    raise ValueError(f"Task {task_id} not found")
                
                # Update task status
                task.status = TaskStatus.IN_PROGRESS
                await db.commit()
                
                # Create agent
                agent = await AgentFactory.create_agent_by_type(
                    AgentType(agent_type),
                    db,
                    project_id=UUID(project_id) if project_id else None
                )
                
                logger.info(
                    "Agent processing task",
                    task_id=task_id,
                    agent_type=agent_type,
                    task_title=task.title
                )
                
                # Process task
                result = await agent.process_task(task)
                
                # Task status is updated by the agent
                await db.commit()
                
                logger.info(
                    "Agent task completed",
                    task_id=task_id,
                    agent_type=agent_type,
                    success=task.status == TaskStatus.COMPLETED
                )
                
                return result
                
        except Exception as e:
            logger.error(
                "Agent task failed",
                task_id=task_id,
                agent_type=agent_type,
                error=str(e),
                exc_info=True
            )
            
            # Update task status on error
            try:
                async with get_db_context() as db:
                    task_repo = TaskRepository(db)
                    task = await task_repo.get(UUID(task_id))
                    if task:
                        task.status = TaskStatus.FAILED
                        task.metadata = task.metadata or {}
                        task.metadata["error"] = str(e)
                        await db.commit()
            except Exception as update_error:
                logger.error("Failed to update task status", error=str(update_error))
            
            raise


@celery_app.task(name="agent.collaborate")
async def agent_collaborate(
    from_agent_type: str,
    to_agent_type: str,
    message: str,
    context: Dict[str, Any],
    project_id: Optional[str] = None
) -> str:
    """
    Handle collaboration between two agents.
    
    Args:
        from_agent_type: Type of agent sending the message
        to_agent_type: Type of agent receiving the message
        message: Collaboration message
        context: Shared context
        project_id: Optional project context
        
    Returns:
        Response from the receiving agent
    """
    with log_operation("agent_collaborate", from_agent=from_agent_type, to_agent=to_agent_type):
        try:
            async with get_db_context() as db:
                # Create both agents
                from_agent = await AgentFactory.create_agent_by_type(
                    AgentType(from_agent_type),
                    db,
                    project_id=UUID(project_id) if project_id else None
                )
                
                to_agent = await AgentFactory.create_agent_by_type(
                    AgentType(to_agent_type),
                    db,
                    project_id=UUID(project_id) if project_id else None
                )
                
                # Handle collaboration
                response = await from_agent.collaborate(to_agent, message, context)
                
                logger.info(
                    "Agent collaboration completed",
                    from_agent=from_agent_type,
                    to_agent=to_agent_type
                )
                
                return response
                
        except Exception as e:
            logger.error(
                "Agent collaboration failed",
                from_agent=from_agent_type,
                to_agent=to_agent_type,
                error=str(e),
                exc_info=True
            )
            raise


@celery_app.task(name="agent.batch_process")
async def batch_process_tasks(
    task_ids: list[str],
    agent_type: str,
    project_id: Optional[str] = None,
    parallel: bool = False
) -> Dict[str, Any]:
    """
    Process multiple tasks with the same agent.
    
    Args:
        task_ids: List of task IDs to process
        agent_type: Type of agent to use
        project_id: Optional project context
        parallel: Whether to process tasks in parallel
        
    Returns:
        Results for each task
    """
    results = {}
    
    if parallel:
        # Create subtasks for parallel execution
        from celery import group
        job = group(
            process_agent_task.s(task_id, agent_type, project_id)
            for task_id in task_ids
        )
        group_result = job.apply_async()
        
        # Collect results
        for i, task_id in enumerate(task_ids):
            try:
                results[task_id] = group_result.results[i].get(timeout=300)
            except Exception as e:
                results[task_id] = {"error": str(e)}
    else:
        # Process sequentially
        for task_id in task_ids:
            try:
                result = await process_agent_task(task_id, agent_type, project_id)
                results[task_id] = result
            except Exception as e:
                results[task_id] = {"error": str(e)}
    
    return results 