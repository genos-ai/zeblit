"""
Health check schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial health check schemas.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    """Basic health check response."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Timestamp of health check")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")


class ComponentHealth(BaseModel):
    """Health status of a component."""
    status: str = Field(..., description="Component health status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class DatabaseHealthCheck(BaseModel):
    """Database health check response."""
    status: str = Field(..., description="Database health status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class DetailedHealthCheck(BaseModel):
    """Detailed health check response."""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Timestamp of health check")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment name")
    components: Dict[str, ComponentHealth] = Field(..., description="Component health statuses")


class ReadinessCheck(BaseModel):
    """Readiness check response."""
    ready: bool = Field(..., description="Whether service is ready")
    timestamp: str = Field(..., description="Timestamp of readiness check")
    reason: Optional[str] = Field(None, description="Reason if not ready")


class LivenessCheck(BaseModel):
    """Liveness check response."""
    alive: bool = Field(..., description="Whether service is alive")
    timestamp: str = Field(..., description="Timestamp of liveness check") 