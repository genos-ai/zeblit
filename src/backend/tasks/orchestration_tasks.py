"""
Orchestration tasks for coordinating multi-agent workflows.

These tasks handle complex workflows that involve multiple agents
working together to achieve a goal.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from celery import chord, chain, group
from sqlalchemy import select

from src.backend.core.celery_app import celery_app
from src.backend.core.database import get_db_context
from src.backend.models.task import Task, TaskStatus, TaskType
from src.backend.models.agent import AgentType
from src.backend.repositories.task import TaskRepository
from src.backend.repositories.project import ProjectRepository
from src.backend.config.logging_config import get_logger, log_operation
from src.backend.tasks.agent_tasks import process_agent_task

logger = get_logger(__name__)


@celery_app.task(name="orchestration.create_development_workflow")
async def create_development_workflow(
    project_id: str,
    requirements: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Create a complete development workflow for a project.
    
    This orchestrates all agents to work together on implementing
    the given requirements.
    
    Args:
        project_id: Project to work on
        requirements: User requirements
        user_id: User requesting the work
        
    Returns:
        Workflow execution results
    """
    with log_operation("create_development_workflow", project_id=project_id):
        try:
            async with get_db_context() as db:
                task_repo = TaskRepository(db)
                
                # Create parent task
                parent_task = Task(
                    project_id=UUID(project_id),
                    agent_type=AgentType.DEV_MANAGER,
                    title="Implement Requirements",
                    description=requirements,
                    task_type=TaskType.PLANNING,
                    created_by=UUID(user_id),
                    status=TaskStatus.PENDING,
                    metadata={
                        "workflow_type": "full_development",
                        "requirements": requirements
                    }
                )
                db.add(parent_task)
                await db.commit()
                
                logger.info(
                    "Created parent task for workflow",
                    task_id=str(parent_task.id),
                    project_id=project_id
                )
                
                # Define workflow stages
                workflow = chain(
                    # Stage 1: Development Manager plans the work
                    process_agent_task.s(
                        str(parent_task.id),
                        AgentType.DEV_MANAGER.value,
                        project_id
                    ),
                    
                    # Stage 2: Product Manager and Architect work in parallel
                    group(
                        create_subtask_and_process.s(
                            project_id,
                            AgentType.PRODUCT_MANAGER.value,
                            "Create User Stories",
                            "Translate requirements into user stories",
                            user_id,
                            parent_task_id=str(parent_task.id)
                        ),
                        create_subtask_and_process.s(
                            project_id,
                            AgentType.ARCHITECT.value,
                            "Design System Architecture",
                            "Create system design and technology selection",
                            user_id,
                            parent_task_id=str(parent_task.id)
                        )
                    ),
                    
                    # Stage 3: Data Analyst designs data model
                    create_subtask_and_process.s(
                        project_id,
                        AgentType.DATA_ANALYST.value,
                        "Design Data Model",
                        "Create database schema and data flows",
                        user_id,
                        parent_task_id=str(parent_task.id)
                    ),
                    
                    # Stage 4: Engineer implements
                    create_subtask_and_process.s(
                        project_id,
                        AgentType.ENGINEER.value,
                        "Implement Features",
                        "Write code based on design and requirements",
                        user_id,
                        parent_task_id=str(parent_task.id)
                    ),
                    
                    # Stage 5: Platform Engineer sets up deployment
                    create_subtask_and_process.s(
                        project_id,
                        AgentType.PLATFORM_ENGINEER.value,
                        "Setup Deployment",
                        "Configure deployment and infrastructure",
                        user_id,
                        parent_task_id=str(parent_task.id)
                    ),
                    
                    # Stage 6: Final review by Dev Manager
                    finalize_workflow.s(str(parent_task.id), project_id)
                )
                
                # Execute workflow
                result = workflow.apply_async()
                
                return {
                    "workflow_id": result.id,
                    "parent_task_id": str(parent_task.id),
                    "status": "started",
                    "stages": 6
                }
                
        except Exception as e:
            logger.error(
                "Failed to create development workflow",
                project_id=project_id,
                error=str(e),
                exc_info=True
            )
            raise


@celery_app.task(name="orchestration.create_subtask_and_process")
async def create_subtask_and_process(
    previous_results: Any,  # Results from previous stage
    project_id: str,
    agent_type: str,
    title: str,
    description: str,
    user_id: str,
    parent_task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a subtask and process it with the specified agent.
    
    This is used in workflow chains to create tasks dynamically
    based on previous results.
    """
    with log_operation("create_subtask_and_process", agent_type=agent_type):
        try:
            async with get_db_context() as db:
                task_repo = TaskRepository(db)
                
                # Enhance description with context from previous results
                enhanced_description = description
                if isinstance(previous_results, dict) and "context" in previous_results:
                    enhanced_description += f"\n\nContext from previous stage:\n{previous_results['context']}"
                
                # Create subtask
                subtask = Task(
                    project_id=UUID(project_id),
                    agent_type=AgentType(agent_type),
                    title=title,
                    description=enhanced_description,
                    task_type=TaskType.IMPLEMENTATION,
                    created_by=UUID(user_id),
                    parent_task_id=UUID(parent_task_id) if parent_task_id else None,
                    status=TaskStatus.PENDING,
                    metadata={
                        "previous_results": previous_results if isinstance(previous_results, dict) else None
                    }
                )
                db.add(subtask)
                await db.commit()
                
                # Process with agent
                result = await process_agent_task(
                    str(subtask.id),
                    agent_type,
                    project_id
                )
                
                return result
                
        except Exception as e:
            logger.error(
                "Failed to create and process subtask",
                agent_type=agent_type,
                error=str(e),
                exc_info=True
            )
            raise


@celery_app.task(name="orchestration.finalize_workflow")
async def finalize_workflow(
    previous_results: Any,
    parent_task_id: str,
    project_id: str
) -> Dict[str, Any]:
    """
    Finalize a workflow by having the Dev Manager review all work.
    """
    with log_operation("finalize_workflow", parent_task_id=parent_task_id):
        try:
            async with get_db_context() as db:
                task_repo = TaskRepository(db)
                
                # Get parent task
                parent_task = await task_repo.get(UUID(parent_task_id))
                if not parent_task:
                    raise ValueError(f"Parent task {parent_task_id} not found")
                
                # Update parent task with review request
                parent_task.task_type = TaskType.REVIEW
                parent_task.description += "\n\nReview all completed work and provide a summary."
                await db.commit()
                
                # Have Dev Manager review
                result = await process_agent_task(
                    parent_task_id,
                    AgentType.DEV_MANAGER.value,
                    project_id
                )
                
                return {
                    "workflow_complete": True,
                    "summary": result.get("response", "Workflow completed"),
                    "parent_task_id": parent_task_id
                }
                
        except Exception as e:
            logger.error(
                "Failed to finalize workflow",
                parent_task_id=parent_task_id,
                error=str(e),
                exc_info=True
            )
            raise


@celery_app.task(name="orchestration.execute_parallel_tasks")
async def execute_parallel_tasks(
    task_configs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Execute multiple tasks in parallel.
    
    Args:
        task_configs: List of task configurations, each containing:
            - task_id: ID of task to process
            - agent_type: Type of agent to use
            - project_id: Optional project context
            
    Returns:
        Results from all tasks
    """
    # Create parallel job group
    job = group(
        process_agent_task.s(
            config["task_id"],
            config["agent_type"],
            config.get("project_id")
        )
        for config in task_configs
    )
    
    # Execute and collect results
    result = job.apply_async()
    return result.get(timeout=600)  # 10 minute timeout


@celery_app.task(name="orchestration.cleanup_completed_tasks")
async def cleanup_completed_tasks() -> Dict[str, int]:
    """
    Periodic task to clean up old completed tasks.
    
    Removes tasks older than 30 days that are completed or failed.
    """
    with log_operation("cleanup_completed_tasks"):
        try:
            async with get_db_context() as db:
                task_repo = TaskRepository(db)
                
                # Calculate cutoff date
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                # Get old tasks
                old_tasks = await db.execute(
                    select(Task).where(
                        Task.updated_at < cutoff_date,
                        Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED])
                    )
                )
                
                count = 0
                for task in old_tasks.scalars():
                    await db.delete(task)
                    count += 1
                
                await db.commit()
                
                logger.info(f"Cleaned up {count} old tasks")
                return {"cleaned_up": count}
                
        except Exception as e:
            logger.error("Failed to cleanup tasks", error=str(e), exc_info=True)
            raise 