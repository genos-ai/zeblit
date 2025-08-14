"""
API endpoints for orchestration and workflow management.

These endpoints allow users to start complex multi-agent workflows
and monitor their progress.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from modules.backend.core.database import get_db
from modules.backend.core.dependencies import get_current_user
from modules.backend.models.user import User
from modules.backend.services.orchestration import OrchestrationService
from modules.backend.schemas.orchestration import (
    WorkflowCreate,
    WorkflowResponse,
    TaskChainCreate,
    TaskChainResponse,
    WorkflowStatusResponse,
    AgentWorkloadResponse
)
from modules.backend.config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


@router.post("/workflows", response_model=WorkflowResponse)
async def start_workflow(
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Start a new multi-agent workflow.
    
    This endpoint initiates a complex workflow where multiple agents
    collaborate to implement the given requirements.
    """
    service = OrchestrationService(db)
    
    try:
        result = await service.start_development_workflow(
            project_id=workflow.project_id,
            requirements=workflow.requirements,
            user=current_user
        )
        
        return WorkflowResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start workflow"
        )


@router.post("/task-chains", response_model=TaskChainResponse)
async def create_task_chain(
    chain: TaskChainCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a chain of tasks to be executed sequentially.
    
    This is useful for simpler workflows where you want specific
    agents to work on tasks in a defined order.
    """
    service = OrchestrationService(db)
    
    try:
        tasks = await service.create_simple_task_chain(
            project_id=chain.project_id,
            task_chain=chain.tasks,
            user=current_user
        )
        
        return TaskChainResponse(
            project_id=chain.project_id,
            tasks=[
                {
                    "id": str(task.id),
                    "title": task.title,
                    "agent_type": task.agent_type.value,
                    "status": task.status.value
                }
                for task in tasks
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to create task chain: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task chain"
        )


@router.get("/workflows/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get the status of a running workflow.
    
    Returns information about the workflow's current state,
    progress, and any results if completed.
    """
    service = OrchestrationService(db)
    
    try:
        status = await service.get_workflow_status(workflow_id)
        return WorkflowStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow status"
        )


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Cancel a running workflow.
    
    This will attempt to stop all running tasks and prevent
    any pending tasks from starting.
    """
    service = OrchestrationService(db)
    
    try:
        result = await service.cancel_workflow(workflow_id)
        return result
        
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel workflow"
        )


@router.get("/agents/workload", response_model=AgentWorkloadResponse)
async def get_agent_workload(
    agent_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get current workload for agents.
    
    Shows how many tasks are pending or in progress for each
    agent type, useful for monitoring system load.
    """
    service = OrchestrationService(db)
    
    try:
        from modules.backend.models.agent import AgentType
        
        agent_type_enum = AgentType(agent_type) if agent_type else None
        workload = await service.get_agent_workload(agent_type_enum)
        
        return AgentWorkloadResponse(workload=workload)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent type: {agent_type}"
        )
    except Exception as e:
        logger.error(f"Failed to get agent workload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent workload"
        )


@router.post("/tasks/{task_id}/retry")
async def retry_failed_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Retry a failed task.
    
    Creates a new task with the same parameters as the failed task
    and queues it for execution.
    """
    service = OrchestrationService(db)
    
    try:
        new_task = await service.rerun_failed_task(
            task_id=task_id,
            user=current_user
        )
        
        return {
            "original_task_id": str(task_id),
            "new_task_id": str(new_task.id),
            "status": "queued",
            "message": "Task has been queued for retry"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to retry task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry task"
        ) 