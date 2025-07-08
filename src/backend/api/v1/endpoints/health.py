"""
Health check endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial health check endpoints implementation.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import settings
from src.backend.core.dependencies import get_db
from src.backend.core.redis_client import redis_client
from src.backend.schemas.health import HealthCheck, DatabaseHealthCheck

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict with status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.VERSION,
    }


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Detailed health check including database connectivity.
    
    Args:
        db: Database session.
        
    Returns:
        Dict with detailed health status of all components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": {
                "status": "unknown",
                "response_time_ms": None,
            },
            "redis": {
                "status": "unknown",
                "response_time_ms": None,
            }
        }
    }
    
    # Check database connectivity
    try:
        start_time = datetime.utcnow()
        result = await db.execute(text("SELECT 1"))
        await db.commit()
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        health_status["components"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": None,
        }
    
    # Check Redis connectivity
    try:
        start_time = datetime.utcnow()
        await redis_client.client.ping()
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        health_status["components"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": None,
        }
    
    return health_status


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes.
    
    Checks if the service is ready to accept traffic.
    
    Args:
        db: Database session.
        
    Returns:
        Dict with readiness status.
        
    Raises:
        HTTPException: If service is not ready.
    """
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        await db.commit()
    except Exception as e:
        return {
            "ready": False,
            "reason": f"Database connection failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes.
    
    Simple check to verify the service is alive.
    
    Returns:
        Dict with liveness status.
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    } 