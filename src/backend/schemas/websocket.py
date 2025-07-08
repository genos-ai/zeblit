"""
WebSocket message schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial WebSocket schemas.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """WebSocket message types."""
    # Connection management
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Console/Error capture
    CONSOLE_LOG = "console_log"
    ERROR_LOG = "error_log"
    
    # File operations
    FILE_CHANGE = "file_change"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    
    # Agent communication
    AGENT_MESSAGE = "agent_message"
    AGENT_STATUS = "agent_status"
    AGENT_RESPONSE = "agent_response"
    
    # Task updates
    TASK_UPDATE = "task_update"
    TASK_PROGRESS = "task_progress"
    
    # Container events
    CONTAINER_STATUS = "container_status"
    CONTAINER_OUTPUT = "container_output"
    
    # Git events
    GIT_PUSH = "git_push"
    GIT_COMMIT = "git_commit"
    GIT_BRANCH_CHANGE = "git_branch_change"


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: WebSocketMessageType = Field(..., description="Message type")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Message timestamp"
    )
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request/response")


class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    user_id: str = Field(..., description="User ID")
    project_id: Optional[str] = Field(None, description="Project ID")
    connected_at: str = Field(..., description="Connection timestamp")
    
    model_config = {"protected_namespaces": ()}


class ConsoleLogPayload(BaseModel):
    """Console log message payload."""
    level: str = Field(..., description="Log level (log, warn, error, info, debug)")
    message: str = Field(..., description="Log message")
    args: Optional[list] = Field(None, description="Additional arguments")
    stack_trace: Optional[str] = Field(None, description="Stack trace for errors")
    source: Optional[str] = Field(None, description="Source file")
    line: Optional[int] = Field(None, description="Line number")
    column: Optional[int] = Field(None, description="Column number")


class ErrorLogPayload(BaseModel):
    """Error log message payload."""
    message: str = Field(..., description="Error message")
    stack: Optional[str] = Field(None, description="Stack trace")
    type: Optional[str] = Field(None, description="Error type")
    filename: Optional[str] = Field(None, description="File where error occurred")
    line: Optional[int] = Field(None, description="Line number")
    column: Optional[int] = Field(None, description="Column number")
    is_unhandled: bool = Field(False, description="Whether error was unhandled")


class FileChangePayload(BaseModel):
    """File change message payload."""
    file_path: str = Field(..., description="Path to changed file")
    change_type: str = Field(..., description="Type of change (created, modified, deleted)")
    content: Optional[str] = Field(None, description="New content for created/modified files")
    old_content: Optional[str] = Field(None, description="Previous content for modified files")


class AgentMessagePayload(BaseModel):
    """Agent message payload."""
    agent_type: str = Field(..., description="Target agent type")
    message: str = Field(..., description="Message content")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class TaskUpdatePayload(BaseModel):
    """Task update payload."""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")


class ContainerStatusPayload(BaseModel):
    """Container status payload."""
    container_id: str = Field(..., description="Container ID")
    status: str = Field(..., description="Container status")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, description="Memory usage in MB")
    disk_usage: Optional[float] = Field(None, description="Disk usage in MB") 