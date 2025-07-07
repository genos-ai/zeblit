"""
Health check endpoints for monitoring application status.

Provides endpoints to check the health of the application and its dependencies.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from core.config import settings
from core.dependencies import get_db, get_request_id
from core.database import engine

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(request_id: str = Depends(get_request_id)) -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict containing health status and metadata
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
        "request_id": request_id
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Simple status indicating the service is alive
    """
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the service is ready to accept traffic by verifying
    database and Redis connections.
    
    Returns:
        Dict containing readiness status and dependency checks
    """
    checks = {
        "database": False,
        "redis": False
    }
    errors = []
    
    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        checks["database"] = result.scalar() == 1
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        checks["redis"] = True
        await redis_client.close()
    except Exception as e:
        errors.append(f"Redis error: {str(e)}")
    
    # Determine overall status
    all_healthy = all(checks.values())
    
    response = {
        "status": "ready" if all_healthy else "not ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if errors:
        response["errors"] = errors
    
    # Return 503 if not ready
    if not all_healthy:
        return response, status.HTTP_503_SERVICE_UNAVAILABLE
    
    return response


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(get_request_id)
) -> Dict[str, Any]:
    """
    Detailed health check with comprehensive system information.
    
    Returns:
        Dict containing detailed health status and system metrics
    """
    # Basic info
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "request_id": request_id,
        "dependencies": {}
    }
    
    # Database health
    try:
        # Check basic connectivity
        result = await db.execute(text("SELECT 1"))
        db_healthy = result.scalar() == 1
        
        # Get database stats
        pool = engine.pool
        response["dependencies"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "pool_type": type(pool).__name__
        }
        
        # Add pool stats if not using NullPool
        if hasattr(pool, 'size'):
            response["dependencies"]["database"].update({
                "pool_size": pool.size(),
                "checked_out_connections": pool.checked_out(),
                "overflow": pool.overflow(),
                "total": pool.total()
            })
    except Exception as e:
        response["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Redis health
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        
        # Get Redis info
        info = await redis_client.info()
        response["dependencies"]["redis"] = {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown")
        }
        await redis_client.close()
    except Exception as e:
        response["dependencies"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check if any dependency is unhealthy
    any_unhealthy = any(
        dep.get("status") == "unhealthy" 
        for dep in response["dependencies"].values()
    )
    
    if any_unhealthy:
        response["status"] = "degraded"
    
    return response 