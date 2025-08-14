"""
User schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial user schemas implementation.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(default=True, description="Whether user is active")
    role: str = Field(default="user", description="User role")
    

class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, description="User password")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@example.com",
            "username": "johndoe",
            "password": "securepassword123",
            "full_name": "John Doe",
            "is_active": True,
            "role": "user"
        }
    })


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "full_name": "John M. Doe",
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        }
    })


class UserResponse(UserBase):
    """Schema for user response data."""
    
    id: UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(default=0, description="Number of logins")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    monthly_token_limit: int = Field(..., description="Monthly token limit")
    monthly_cost_limit: float = Field(..., description="Monthly cost limit in USD")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
                "role": "user",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-10T10:00:00Z",
                "login_count": 5,
                "preferences": {"theme": "dark"},
                "monthly_token_limit": 1000000,
                "monthly_cost_limit": 50.0
            }
        }
    )


class UserProfile(BaseModel):
    """Schema for user profile information."""
    
    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="User's full name")
    role: str = Field(..., description="User role")
    created_at: datetime = Field(..., description="User creation timestamp")
    project_count: int = Field(default=0, description="Number of projects")
    total_tokens_used: int = Field(default=0, description="Total tokens used")
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    
    model_config = ConfigDict(from_attributes=True)


class UserStats(BaseModel):
    """Schema for user usage statistics."""
    
    user_id: UUID = Field(..., description="User ID")
    tokens_used_this_month: int = Field(..., description="Tokens used this month")
    cost_this_month: float = Field(..., description="Cost this month in USD")
    tokens_remaining: int = Field(..., description="Tokens remaining this month")
    cost_remaining: float = Field(..., description="Cost remaining this month in USD")
    project_count: int = Field(..., description="Total number of projects")
    active_projects: int = Field(..., description="Number of active projects")
    task_count: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "tokens_used_this_month": 250000,
            "cost_this_month": 25.50,
            "tokens_remaining": 750000,
            "cost_remaining": 74.50,
            "project_count": 10,
            "active_projects": 3,
            "task_count": 150,
            "completed_tasks": 120
        }
    }) 