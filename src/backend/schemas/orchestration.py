"""
Pydantic schemas for orchestration and workflow management.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    """Schema for creating a new workflow."""
    project_id: UUID = Field(..., description="Project to run workflow on")
    requirements: str = Field(..., description="Requirements to implement", min_length=10)


class WorkflowResponse(BaseModel):
    """Response after starting a workflow."""
    workflow_id: str = Field(..., description="Celery task ID for tracking")
    project_id: str = Field(..., description="Project ID")
    status: str = Field(..., description="Workflow status")
    message: str = Field(..., description="Status message")


class TaskDefinition(BaseModel):
    """Definition for a task in a chain."""
    agent_type: str = Field(..., description="Type of agent to handle the task")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    task_type: Optional[str] = Field("IMPLEMENTATION", description="Type of task")
    depends_on: Optional[int] = Field(None, description="Index of task this depends on")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TaskChainCreate(BaseModel):
    """Schema for creating a task chain."""
    project_id: UUID = Field(..., description="Project context")
    tasks: List[TaskDefinition] = Field(..., description="List of tasks to create")


class TaskInfo(BaseModel):
    """Information about a task."""
    id: str
    title: str
    agent_type: str
    status: str


class TaskChainResponse(BaseModel):
    """Response after creating a task chain."""
    project_id: UUID
    tasks: List[TaskInfo]


class WorkflowStatusResponse(BaseModel):
    """Status information for a workflow."""
    workflow_id: str
    state: str = Field(..., description="Celery task state")
    ready: bool = Field(..., description="Whether workflow has finished")
    successful: Optional[bool] = Field(None, description="Whether workflow succeeded")
    failed: Optional[bool] = Field(None, description="Whether workflow failed")
    info: Optional[str] = Field(None, description="Human-readable status")
    result: Optional[Dict[str, Any]] = Field(None, description="Workflow result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class AgentWorkloadInfo(BaseModel):
    """Workload information for an agent type."""
    pending: int = Field(..., description="Number of pending tasks")
    in_progress: int = Field(..., description="Number of tasks in progress")
    total: int = Field(..., description="Total active tasks")


class AgentWorkloadResponse(BaseModel):
    """Response with agent workload information."""
    workload: Dict[str, AgentWorkloadInfo] = Field(
        ..., 
        description="Workload by agent type"
    ) 