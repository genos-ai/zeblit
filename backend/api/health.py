"""
Health check endpoints for monitoring application status.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import redis.asyncio as redis

from core.database import get_db
from core.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    services: Dict[str, Dict[str, Any]]


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint that verifies all services are operational.
    
    Returns:
        HealthResponse: Status of the application and its dependencies
    """
    services = {}
    
    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = {
            "status": "healthy",
            "message": "Connected to PostgreSQL"
        }
    except Exception as e:
        services["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        services["redis"] = {
            "status": "healthy",
            "message": "Connected to Redis"
        }
    except Exception as e:
        services["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
    
    # Check LLM API availability (basic check)
    services["llm_apis"] = {
        "anthropic": {
            "configured": bool(settings.ANTHROPIC_API_KEY),
            "status": "configured" if settings.ANTHROPIC_API_KEY else "not_configured"
        },
        "openai": {
            "configured": bool(settings.OPENAI_API_KEY),
            "status": "configured" if settings.OPENAI_API_KEY else "not_configured"
        },
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY),
            "status": "configured" if settings.GEMINI_API_KEY else "not_configured"
        }
    }
    
    # Determine overall status
    unhealthy_services = [
        name for name, service in services.items() 
        if isinstance(service, dict) and service.get("status") == "unhealthy"
    ]
    
    overall_status = "unhealthy" if unhealthy_services else "healthy"
    
    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        services=services
    )


@router.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Dict: Simple ready status
    """
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Dict: Simple alive status
    """
    return {"status": "alive"} 