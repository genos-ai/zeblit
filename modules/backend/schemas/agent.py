"""
Agent schemas.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2024-01-XX): Added AgentListResponse and AgentStatusUpdate schemas.
- 1.0.0 (2024-01-XX): Initial agent schemas implementation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AgentBase(BaseModel):
    """Base agent schema with common fields."""
    
    name: str = Field(..., description="Agent display name")
    agent_type: str = Field(..., description="Agent type identifier")
    description: Optional[str] = Field(None, description="Agent description")
    default_model: str = Field(..., description="AI model to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(4000, gt=0, description="Maximum tokens per response")
    

class AgentCreate(AgentBase):
    """Schema for creating a new agent."""
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Development Manager",
            "agent_type": "development_manager",
            "description": "Manages development tasks and coordinates other agents",
            "default_model": "claude-3-sonnet-20240620",
            "temperature": 0.7,
            "max_tokens": 4000
        }
    })


class AgentUpdate(BaseModel):
    """Schema for updating agent information."""
    
    name: Optional[str] = Field(None, description="Agent display name")
    description: Optional[str] = Field(None, description="Agent description")
    default_model: Optional[str] = Field(None, description="AI model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens per response")
    is_active: Optional[bool] = Field(None, description="Whether agent is active")
    

class AgentResponse(AgentBase):
    """Schema for agent response data."""
    
    id: UUID = Field(..., description="Agent ID")
    is_active: bool = Field(True, description="Whether agent is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Performance metrics
    total_tasks_completed: int = Field(0, description="Total tasks handled")
    total_tokens_used: int = Field(0, description="Total tokens consumed")
    total_cost_usd: float = Field(0.0, description="Total cost in USD")
    average_completion_time_minutes: Optional[float] = Field(None, description="Average completion time in minutes")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Development Manager",
                "agent_type": "development_manager",
                "description": "Manages development tasks and coordinates other agents",
                "default_model": "claude-3-sonnet-20240620",
                "temperature": 0.7,
                "max_tokens": 4000,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "total_tasks_completed": 150,
                "total_tokens_used": 250000,
                "total_cost_usd": 12.50,
                "average_completion_time_minutes": 2.5
            }
        }
    )


class AgentListResponse(BaseModel):
    """Schema for paginated agent list response."""
    
    items: List[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., ge=0, description="Total number of items")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Number of items per page")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [],
            "total": 6,
            "skip": 0,
            "limit": 20
        }
    })


class AgentStatusUpdate(BaseModel):
    """Schema for updating agent status."""
    
    status: str = Field(..., description="New agent status")
    current_task_id: Optional[UUID] = Field(None, description="Current task being processed")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "busy",
            "current_task_id": "456e7890-e89b-12d3-a456-426614174000",
            "last_activity": "2024-01-10T15:30:00Z"
        }
    })


class AgentMetrics(BaseModel):
    """Schema for agent performance metrics."""
    
    agent_id: UUID = Field(..., description="Agent ID")
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")
    
    # Task metrics
    tasks_completed: int = Field(..., description="Number of tasks completed")
    tasks_failed: int = Field(..., description="Number of tasks failed")
    average_task_duration: float = Field(..., description="Average task duration in seconds")
    
    # Token usage
    total_input_tokens: int = Field(..., description="Total input tokens")
    total_output_tokens: int = Field(..., description="Total output tokens")
    
    # Cost metrics
    total_cost_usd: float = Field(..., description="Total cost in USD")
    average_cost_per_task: float = Field(..., description="Average cost per task")
    
    # Performance
    success_rate: float = Field(..., description="Task success rate (0-1)")
    average_response_time: float = Field(..., description="Average response time in seconds")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "agent_id": "123e4567-e89b-12d3-a456-426614174000",
            "period_start": "2024-01-01T00:00:00Z",
            "period_end": "2024-01-31T23:59:59Z",
            "tasks_completed": 150,
            "tasks_failed": 5,
            "average_task_duration": 45.2,
            "total_input_tokens": 125000,
            "total_output_tokens": 125000,
            "total_cost_usd": 12.50,
            "average_cost_per_task": 0.083,
            "success_rate": 0.968,
            "average_response_time": 2.5
        }
    })


# New schemas for agent orchestrator

class AgentChatRequest(BaseModel):
    """Schema for agent chat requests."""
    
    message: str = Field(..., description="Message to send to agent")
    target_agent: Optional[str] = Field(None, description="Optional specific agent type to target")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the agent")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Create a new API endpoint for user management",
            "target_agent": "engineer",
            "context": {
                "priority": "high",
                "deadline": "2024-01-15"
            }
        }
    })


class AgentChatResponse(BaseModel):
    """Schema for agent chat responses."""
    
    agent_id: str = Field(..., description="ID of the responding agent")
    agent_type: str = Field(..., description="Type of the responding agent")
    response: str = Field(..., description="Agent's response message")
    timestamp: str = Field(..., description="Response timestamp")
    routing: Optional[Dict[str, Any]] = Field(None, description="Routing information if message should be forwarded")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "agent_id": "123e4567-e89b-12d3-a456-426614174000",
            "agent_type": "dev_manager",
            "response": "I'll help you create that API endpoint. Let me route this to our Engineer agent who can implement the specific code.",
            "timestamp": "2024-01-11T10:30:00Z",
            "routing": {
                "suggested_agent": "engineer",
                "reason": "Message contains keywords related to engineer",
                "keywords_found": ["implement", "API endpoint"]
            }
        }
    }) 