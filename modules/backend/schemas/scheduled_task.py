"""
Schemas for scheduled task operations.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial scheduled task schemas.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ScheduledTaskBase(BaseModel):
    """Base schema for scheduled tasks."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Task name")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    schedule: str = Field(..., description="Cron expression for scheduling")
    command: str = Field(..., min_length=1, description="Command to execute")
    working_directory: str = Field("/workspace", description="Working directory for execution")
    environment_variables: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")
    timeout_seconds: int = Field(300, ge=1, le=3600, description="Execution timeout in seconds")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    capture_output: bool = Field(True, description="Whether to capture stdout/stderr")
    notify_on_failure: bool = Field(True, description="Send notifications on failure")
    notify_on_success: bool = Field(False, description="Send notifications on success")
    
    @validator('schedule')
    def validate_cron_expression(cls, v):
        """Validate cron expression format."""
        try:
            from croniter import croniter
            croniter(v)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        return v
    
    @validator('command')
    def validate_command(cls, v):
        """Validate command is not empty."""
        if not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()


class ScheduledTaskCreate(ScheduledTaskBase):
    """Schema for creating a scheduled task."""
    
    project_id: UUID = Field(..., description="Project ID where task will run")


class ScheduledTaskUpdate(BaseModel):
    """Schema for updating a scheduled task."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    schedule: Optional[str] = Field(None)
    command: Optional[str] = Field(None, min_length=1)
    working_directory: Optional[str] = Field(None)
    environment_variables: Optional[Dict[str, str]] = Field(None)
    is_enabled: Optional[bool] = Field(None)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=3600)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    capture_output: Optional[bool] = Field(None)
    notify_on_failure: Optional[bool] = Field(None)
    notify_on_success: Optional[bool] = Field(None)
    
    @validator('schedule')
    def validate_cron_expression(cls, v):
        """Validate cron expression format."""
        if v is not None:
            try:
                from croniter import croniter
                croniter(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {str(e)}")
        return v
    
    @validator('command')
    def validate_command(cls, v):
        """Validate command is not empty."""
        if v is not None and not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip() if v else v


class ScheduledTaskRead(BaseModel):
    """Schema for reading a scheduled task."""
    
    id: UUID
    name: str
    description: Optional[str]
    user_id: UUID
    project_id: UUID
    schedule: str
    command: str
    working_directory: str
    environment_variables: Dict[str, str]
    is_enabled: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    capture_output: bool
    notify_on_failure: bool
    notify_on_success: bool
    is_overdue: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScheduledTaskRunBase(BaseModel):
    """Base schema for task runs."""
    
    started_at: datetime
    completed_at: Optional[datetime]
    status: str = Field(..., description="Execution status: running, success, failed, timeout")
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    error_message: Optional[str]
    container_id: Optional[str]
    execution_duration_ms: Optional[int]
    retry_attempt: int = Field(0, ge=0)


class ScheduledTaskRunRead(ScheduledTaskRunBase):
    """Schema for reading a task run."""
    
    id: UUID
    task_id: UUID
    duration_seconds: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScheduledTaskWithRuns(ScheduledTaskRead):
    """Schema for task with execution history."""
    
    task_runs: List[ScheduledTaskRunRead] = Field(default_factory=list)


class ScheduledTaskStats(BaseModel):
    """Schema for task statistics."""
    
    total_tasks: int
    enabled_tasks: int
    disabled_tasks: int
    overdue_tasks: int
    total_runs_today: int
    successful_runs_today: int
    failed_runs_today: int
    success_rate_today: float


class TaskExecutionRequest(BaseModel):
    """Schema for manual task execution."""
    
    task_id: UUID
    execute_now: bool = True


class BulkTaskOperation(BaseModel):
    """Schema for bulk operations on tasks."""
    
    task_ids: List[UUID] = Field(..., min_items=1, max_items=50)
    operation: str = Field(..., description="Operation: enable, disable, delete")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validate operation type."""
        allowed_operations = ['enable', 'disable', 'delete']
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {allowed_operations}")
        return v


class ScheduleValidationRequest(BaseModel):
    """Schema for validating cron schedules."""
    
    schedule: str = Field(..., description="Cron expression to validate")
    
    @validator('schedule')
    def validate_cron_expression(cls, v):
        """Validate cron expression format."""
        try:
            from croniter import croniter
            croniter(v)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {str(e)}")
        return v


class ScheduleValidationResponse(BaseModel):
    """Schema for schedule validation response."""
    
    is_valid: bool
    error_message: Optional[str]
    next_runs: List[datetime] = Field(default_factory=list, description="Next 5 execution times")
    human_readable: Optional[str] = Field(None, description="Human-readable schedule description")


class TaskQuickCreate(BaseModel):
    """Schema for quick task creation with common presets."""
    
    name: str = Field(..., min_length=1, max_length=255)
    project_id: UUID
    preset: str = Field(..., description="Preset type: daily, hourly, weekly, custom")
    command: str = Field(..., min_length=1)
    custom_schedule: Optional[str] = Field(None, description="Custom cron expression (required if preset=custom)")
    
    @validator('preset')
    def validate_preset(cls, v):
        """Validate preset type."""
        allowed_presets = ['daily', 'hourly', 'weekly', 'custom']
        if v not in allowed_presets:
            raise ValueError(f"Preset must be one of: {allowed_presets}")
        return v
    
    @validator('custom_schedule')
    def validate_custom_schedule(cls, v, values):
        """Validate custom schedule when preset is custom."""
        if values.get('preset') == 'custom':
            if not v:
                raise ValueError("Custom schedule is required when preset is 'custom'")
            try:
                from croniter import croniter
                croniter(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {str(e)}")
        return v
    
    def get_schedule(self) -> str:
        """Get the actual cron schedule based on preset."""
        presets = {
            'daily': '0 0 * * *',      # Daily at midnight
            'hourly': '0 * * * *',     # Every hour
            'weekly': '0 0 * * 0',     # Weekly on Sunday at midnight
        }
        
        if self.preset == 'custom':
            return self.custom_schedule
        else:
            return presets[self.preset]
