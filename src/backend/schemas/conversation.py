"""
Conversation schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial conversation schemas implementation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MessageBase(BaseModel):
    """Base message schema."""
    
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    message_type: Optional[str] = Field(default="text", description="Message type (text, code, error, status_update)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    

class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    
    target_agent: Optional[str] = Field(None, description="Target agent type if directed")
    requires_response: bool = Field(default=True, description="Whether message requires a response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Create a React component for user login",
                "message_type": "text",
                "target_agent": "engineer",
                "requires_response": True
            }
        }


class MessageResponse(MessageBase):
    """Schema for message response data."""
    
    id: UUID = Field(..., description="Message ID")
    conversation_id: UUID = Field(..., description="Conversation ID")
    task_id: Optional[UUID] = Field(None, description="Associated task ID")
    agent_id: Optional[UUID] = Field(None, description="Agent ID if from agent")
    token_count: Optional[int] = Field(None, description="Token count")
    model_used: Optional[str] = Field(None, description="LLM model used")
    target_agent: Optional[str] = Field(None, description="Target agent type")
    requires_response: bool = Field(..., description="Whether requires response")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    
    project_id: UUID = Field(..., description="Project ID")
    agent_id: Optional[UUID] = Field(None, description="Initial agent ID")
    title: Optional[str] = Field(None, description="Conversation title")
    context: Dict[str, Any] = Field(default_factory=dict, description="Initial context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Implement authentication feature",
                "context": {
                    "framework": "react",
                    "requirements": ["JWT", "OAuth2"]
                }
            }
        }


class ConversationResponse(BaseModel):
    """Schema for conversation response data."""
    
    id: UUID = Field(..., description="Conversation ID")
    project_id: UUID = Field(..., description="Project ID")
    user_id: UUID = Field(..., description="User ID")
    agent_id: Optional[UUID] = Field(None, description="Current agent ID")
    title: Optional[str] = Field(None, description="Conversation title")
    context: Dict[str, Any] = Field(..., description="Conversation context")
    is_active: bool = Field(..., description="Whether conversation is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    message_count: int = Field(default=0, description="Total message count")
    
    model_config = ConfigDict(from_attributes=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "789e4567-e89b-12d3-a456-426614174000",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e4567-e89b-12d3-a456-426614174000",
                "agent_id": "abc4567-e89b-12d3-a456-426614174000",
                "title": "Implement authentication feature",
                "context": {
                    "framework": "react",
                    "requirements": ["JWT", "OAuth2"]
                },
                "is_active": True,
                "created_at": "2024-01-10T10:00:00Z",
                "updated_at": "2024-01-10T12:00:00Z",
                "last_message_at": "2024-01-10T12:00:00Z",
                "message_count": 15
            }
        }


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation with messages."""
    
    messages: List[MessageResponse] = Field(..., description="Conversation messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "789e4567-e89b-12d3-a456-426614174000",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e4567-e89b-12d3-a456-426614174000",
                "agent_id": "abc4567-e89b-12d3-a456-426614174000",
                "title": "Implement authentication feature",
                "context": {
                    "framework": "react",
                    "requirements": ["JWT", "OAuth2"]
                },
                "is_active": True,
                "created_at": "2024-01-10T10:00:00Z",
                "updated_at": "2024-01-10T12:00:00Z",
                "last_message_at": "2024-01-10T12:00:00Z",
                "message_count": 2,
                "messages": [
                    {
                        "id": "msg1-4567-e89b-12d3-a456-426614174000",
                        "conversation_id": "789e4567-e89b-12d3-a456-426614174000",
                        "role": "user",
                        "content": "Create a React login component",
                        "message_type": "text",
                        "metadata": {},
                        "created_at": "2024-01-10T10:00:00Z"
                    },
                    {
                        "id": "msg2-4567-e89b-12d3-a456-426614174000",
                        "conversation_id": "789e4567-e89b-12d3-a456-426614174000",
                        "role": "assistant",
                        "content": "I'll create a React login component...",
                        "message_type": "text",
                        "metadata": {},
                        "model_used": "claude-sonnet-4",
                        "token_count": 150,
                        "created_at": "2024-01-10T10:01:00Z"
                    }
                ]
            }
        } 