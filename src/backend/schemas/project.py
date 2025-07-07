"""
Project schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial project schemas implementation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    template_type: Optional[str] = Field(None, description="Template type (react, nextjs, etc.)")
    framework_config: Dict[str, Any] = Field(default_factory=dict, description="Framework configuration")
    git_repo_url: Optional[str] = Field(None, description="Git repository URL")
    

class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    
    template_id: Optional[UUID] = Field(None, description="Template ID to use")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Awesome App",
                "description": "A React-based web application",
                "template_type": "react",
                "framework_config": {
                    "typescript": True,
                    "tailwind": True
                }
            }
        }


class ProjectUpdate(BaseModel):
    """Schema for updating project information."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    framework_config: Optional[Dict[str, Any]] = Field(None, description="Framework configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Updated App",
                "description": "Updated description"
            }
        }


class ProjectResponse(ProjectBase):
    """Schema for project response data."""
    
    id: UUID = Field(..., description="Project ID")
    owner_id: UUID = Field(..., description="Owner user ID")
    status: str = Field(..., description="Project status")
    container_id: Optional[str] = Field(None, description="Container ID")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    default_branch: str = Field(default="main", description="Default Git branch")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_accessed: datetime = Field(..., description="Last access timestamp")
    
    model_config = ConfigDict(from_attributes=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "owner_id": "987e4567-e89b-12d3-a456-426614174000",
                "name": "My Awesome App",
                "description": "A React-based web application",
                "template_type": "react",
                "framework_config": {
                    "typescript": True,
                    "tailwind": True
                },
                "status": "active",
                "container_id": "container_abc123",
                "preview_url": "https://preview.example.com/project123",
                "default_branch": "main",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_accessed": "2024-01-10T10:00:00Z"
            }
        }


class ProjectStats(BaseModel):
    """Schema for project statistics."""
    
    project_id: UUID = Field(..., description="Project ID")
    file_count: int = Field(..., description="Number of files")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    task_count: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    active_branches: int = Field(..., description="Number of active branches")
    collaborator_count: int = Field(..., description="Number of collaborators")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "file_count": 42,
                "total_size_bytes": 1048576,
                "task_count": 20,
                "completed_tasks": 15,
                "active_branches": 3,
                "collaborator_count": 2,
                "last_activity": "2024-01-10T15:30:00Z"
            }
        } 