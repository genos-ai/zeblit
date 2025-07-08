"""
Container schemas for API requests and responses.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial container schemas.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.backend.models.enums import ContainerStatus


class ContainerBase(BaseModel):
    """Base container schema."""
    cpu_limit: Optional[float] = Field(None, ge=0.5, le=4.0, description="CPU cores limit")
    memory_limit: Optional[int] = Field(None, ge=512, le=8192, description="Memory limit in MB")
    disk_limit: Optional[int] = Field(None, ge=1024, le=20480, description="Disk limit in MB")
    environment_vars: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Environment variables"
    )
    
    model_config = {"protected_namespaces": ()}


class ContainerCreate(ContainerBase):
    """Container creation request."""
    pass


class ContainerUpdate(BaseModel):
    """Container update request."""
    cpu_limit: Optional[float] = Field(None, ge=0.5, le=4.0)
    memory_limit: Optional[int] = Field(None, ge=512, le=8192)
    disk_limit: Optional[int] = Field(None, ge=1024, le=20480)
    environment_vars: Optional[Dict[str, str]] = None
    auto_sleep_minutes: Optional[int] = Field(None, ge=5, le=120)
    auto_stop_hours: Optional[int] = Field(None, ge=1, le=168)
    
    model_config = {"protected_namespaces": ()}


class ContainerRead(ContainerBase):
    """Container response schema."""
    id: UUID
    project_id: UUID
    container_id: str = Field(..., description="Docker/OrbStack container ID")
    container_name: Optional[str] = Field(None, description="Container name")
    status: ContainerStatus
    
    # Ports and networking
    internal_port: int = Field(3000, description="Internal application port")
    external_port: Optional[int] = Field(None, description="External mapped port")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    last_active_at: datetime
    stopped_at: Optional[datetime]
    
    # Auto-management settings
    auto_sleep_minutes: int
    auto_stop_hours: int
    auto_delete_days: int
    
    # Computed properties
    is_running: bool
    is_sleeping: bool
    is_healthy: bool
    uptime_minutes: Optional[int]
    idle_minutes: int
    
    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class ContainerStats(BaseModel):
    """Container statistics response."""
    status: ContainerStatus
    uptime_minutes: Optional[int] = None
    
    # Resource usage
    cpu_percent: float = Field(0.0, description="CPU usage percentage")
    memory_usage_mb: int = Field(0, description="Memory usage in MB")
    memory_limit_mb: int = Field(0, description="Memory limit in MB")
    disk_usage_mb: int = Field(0, description="Disk usage in MB")
    
    # Network usage
    network_in_mb: float = Field(0.0, description="Network input in MB")
    network_out_mb: float = Field(0.0, description="Network output in MB")
    
    # Resource percentages
    resource_usage: Dict[str, float] = Field(
        default_factory=dict,
        description="Resource usage percentages"
    )
    
    # Process info
    pids: int = Field(0, description="Number of processes")
    
    model_config = {"protected_namespaces": ()}


class ContainerLogs(BaseModel):
    """Container logs response."""
    logs: str = Field(..., description="Container log output")
    tail: int = Field(100, description="Number of lines returned")
    
    model_config = {"protected_namespaces": ()}


class ContainerCommand(BaseModel):
    """Container command execution request."""
    command: List[str] = Field(..., description="Command to execute")
    workdir: Optional[str] = Field(None, description="Working directory")
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v: List[str]) -> List[str]:
        """Validate command."""
        if not v:
            raise ValueError("Command cannot be empty")
        return v
    
    model_config = {"protected_namespaces": ()}


class ContainerCommandResult(BaseModel):
    """Container command execution result."""
    exit_code: int = Field(..., description="Command exit code")
    output: str = Field(..., description="Command output")
    
    model_config = {"protected_namespaces": ()}


class ContainerList(BaseModel):
    """List of containers."""
    containers: List[ContainerRead]
    total: int = Field(..., description="Total number of containers")
    
    model_config = {"protected_namespaces": ()}


class ContainerHealth(BaseModel):
    """Container health check result."""
    healthy: bool = Field(..., description="Is container healthy")
    status: ContainerStatus
    last_health_check: Optional[datetime] = None
    health_check_failures: int = Field(0, description="Consecutive health check failures")
    
    model_config = {"protected_namespaces": ()} 