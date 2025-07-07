"""
Task schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial task schemas implementation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    """Base task schema with common fields."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: str = Field(..., description="Task description")
    task_type: Optional[str] = Field(None, description="Task type (feature, bug_fix, refactor, etc.)")
    complexity: Optional[str] = Field(None, description="Task complexity (simple, medium, complex)")
    

class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    
    project_id: UUID = Field(..., description="Project ID")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID for subtasks")
    assigned_agents: List[str] = Field(default_factory=list, description="Agent types to assign")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Implement user authentication",
                "description": "Add JWT-based authentication to the API",
                "task_type": "feature",
                "complexity": "medium",
                "assigned_agents": ["engineer", "architect"]
            }
        }


class TaskUpdate(BaseModel):
    """Schema for updating task information."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[str] = Field(None, description="Task status")
    assigned_agents: Optional[List[str]] = Field(None, description="Agent types to assign")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "in_progress",
                "assigned_agents": ["engineer", "architect", "dev_manager"]
            }
        }


class TaskResponse(TaskBase):
    """Schema for task response data."""
    
    id: UUID = Field(..., description="Task ID")
    project_id: UUID = Field(..., description="Project ID")
    user_id: Optional[UUID] = Field(None, description="User who created the task")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID")
    status: str = Field(..., description="Task status")
    assigned_agents: List[str] = Field(..., description="Assigned agent types")
    primary_agent: Optional[str] = Field(None, description="Primary agent type")
    results: Dict[str, Any] = Field(default_factory=dict, description="Task results")
    generated_files: List[str] = Field(default_factory=list, description="Generated file paths")
    git_commits: List[str] = Field(default_factory=list, description="Git commit hashes")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    execution_time_seconds: Optional[int] = Field(None, description="Execution time in seconds")
    retry_count: int = Field(default=0, description="Number of retries")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "456e4567-e89b-12d3-a456-426614174000",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "789e4567-e89b-12d3-a456-426614174000",
                "title": "Implement user authentication",
                "description": "Add JWT-based authentication to the API",
                "task_type": "feature",
                "complexity": "medium",
                "status": "completed",
                "assigned_agents": ["engineer", "architect"],
                "primary_agent": "engineer",
                "results": {
                    "files_created": 5,
                    "tests_passed": True
                },
                "generated_files": [
                    "src/auth/jwt.py",
                    "src/auth/middleware.py"
                ],
                "git_commits": ["abc123", "def456"],
                "started_at": "2024-01-10T10:00:00Z",
                "completed_at": "2024-01-10T11:30:00Z",
                "execution_time_seconds": 5400,
                "retry_count": 0,
                "created_at": "2024-01-10T09:00:00Z",
                "updated_at": "2024-01-10T11:30:00Z"
            }
        } 