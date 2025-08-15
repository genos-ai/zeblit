"""
Project schemas.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2024-01-XX): Added missing schemas for project endpoints.
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
    framework: Optional[str] = Field(None, description="Framework (react, nextjs, vue, etc.)")
    language: str = Field(default="javascript", description="Primary language")
    is_public: bool = Field(default=False, description="Whether the project is public")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Project settings")
    

class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    
    template_id: Optional[UUID] = Field(None, description="Template ID to use")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "My Awesome App",
            "description": "A React-based web application",
            "framework": "react",
            "language": "typescript",
            "is_public": False,
            "settings": {
                "typescript": True,
                "tailwind": True
            }
        }
    })


class ProjectUpdate(BaseModel):
    """Schema for updating project information."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    is_public: Optional[bool] = Field(None, description="Whether the project is public")
    settings: Optional[Dict[str, Any]] = Field(None, description="Project settings")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "My Updated App",
            "description": "Updated description",
            "is_public": True
        }
    })


class ProjectResponse(ProjectBase):
    """Schema for project response data."""
    
    id: UUID = Field(..., description="Project ID")
    owner_id: UUID = Field(..., description="Owner user ID")
    status: str = Field(..., description="Project status")
    repository_url: Optional[str] = Field(None, description="Git repository URL")
    branch: str = Field(default="main", description="Git branch")
    template_type: Optional[str] = Field(None, description="Template used for project creation")
    environment_variables: Dict[str, Any] = Field(default_factory=dict, description="Environment variables")
    is_archived: bool = Field(default=False, description="Whether the project is archived")
    
    # Resource limits
    max_containers: int = Field(default=5, description="Maximum containers allowed")
    max_storage_mb: int = Field(default=10240, description="Maximum storage in MB")
    max_compute_hours: int = Field(default=100, description="Maximum compute hours")
    
    # Usage tracking
    current_containers: int = Field(default=0, description="Current containers count")
    current_storage_mb: int = Field(default=0, description="Current storage usage in MB")
    current_compute_hours: int = Field(default=0, description="Current compute hours used")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Project tags")
    readme_content: Optional[str] = Field(None, description="Project README content")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_activity_at: datetime = Field(..., description="Last activity timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "owner_id": "987e4567-e89b-12d3-a456-426614174000",
                "name": "My Awesome App",
                "description": "A React-based web application",
                "framework": "react",
                "language": "typescript",
                "is_public": False,
                "settings": {
                    "typescript": True,
                    "tailwind": True
                },
                "status": "active",
                "repository_url": "https://github.com/user/my-awesome-app",
                "branch": "main",
                "template_type": "react-typescript",
                "environment_variables": {"NODE_ENV": "development"},
                "is_archived": False,
                "max_containers": 5,
                "max_storage_mb": 10240,
                "max_compute_hours": 100,
                "current_containers": 1,
                "current_storage_mb": 512,
                "current_compute_hours": 2,
                "tags": ["react", "typescript"],
                "readme_content": "# My Awesome App\n\nA React-based web application",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_activity_at": "2024-01-10T10:00:00Z"
            }
        }
    )


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""
    
    items: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., ge=0, description="Total number of items")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Number of items per page")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [],
            "total": 100,
            "skip": 0,
            "limit": 20
        }
    })


class ProjectTemplateResponse(BaseModel):
    """Schema for project template response."""
    
    id: UUID = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    framework: str = Field(..., description="Framework")
    language: str = Field(..., description="Primary language")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    icon_url: Optional[str] = Field(None, description="Template icon URL")
    preview_url: Optional[str] = Field(None, description="Template preview URL")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Default settings")
    popularity_score: int = Field(default=0, description="Usage count")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "React TypeScript Starter",
                "description": "Modern React app with TypeScript, Vite, and Tailwind CSS",
                "framework": "react",
                "language": "typescript",
                "tags": ["react", "typescript", "vite", "tailwind"],
                "icon_url": "https://example.com/react-icon.png",
                "preview_url": "https://example.com/preview/react-starter",
                "settings": {
                    "typescript": True,
                    "tailwind": True,
                    "eslint": True,
                    "prettier": True
                },
                "popularity_score": 150,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )


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
    
    model_config = ConfigDict(json_schema_extra={
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
    }) 