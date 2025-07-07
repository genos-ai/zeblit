"""
Agent schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial agent schemas implementation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AgentBase(BaseModel):
    """Base agent schema with common fields."""
    
    agent_type: str = Field(..., description="Agent type (dev_manager, product_manager, etc.)")
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    system_prompt: str = Field(..., description="System prompt for the agent")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    default_model: str = Field(default="claude-sonnet-4", description="Default LLM model")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Temperature setting")
    max_tokens: int = Field(default=4000, ge=1, description="Maximum tokens per response")
    

class AgentResponse(AgentBase):
    """Schema for agent response data."""
    
    id: UUID = Field(..., description="Agent ID")
    is_active: bool = Field(..., description="Whether agent is active")
    current_load: int = Field(..., description="Current number of active tasks")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_type": "dev_manager",
                "name": "Development Manager",
                "description": "Orchestrates development tasks",
                "system_prompt": "You are a development manager...",
                "capabilities": ["task_orchestration", "code_review"],
                "default_model": "claude-sonnet-4",
                "temperature": 0.3,
                "max_tokens": 4000,
                "is_active": True,
                "current_load": 2,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class AgentStats(BaseModel):
    """Schema for agent statistics."""
    
    agent_id: UUID = Field(..., description="Agent ID")
    tasks_completed: int = Field(..., description="Total tasks completed")
    tasks_failed: int = Field(..., description="Total tasks failed")
    avg_response_time: float = Field(..., description="Average response time in seconds")
    total_tokens_used: int = Field(..., description="Total tokens consumed")
    success_rate: float = Field(..., description="Success rate percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "tasks_completed": 150,
                "tasks_failed": 5,
                "avg_response_time": 2.5,
                "total_tokens_used": 1500000,
                "success_rate": 96.8
            }
        } 