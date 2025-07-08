"""
Main FastAPI application for the AI Development Platform.

This module creates and configures the FastAPI application instance
with all middleware, routers, and event handlers.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.backend.core.config import settings
from src.backend.core.database import create_tables
from src.backend.core.middleware import configure_middleware
from src.backend.core.exceptions import BaseAPIException
from src.backend.api.v1 import router as v1_router
from src.backend.core.redis_client import redis_client
from src.backend.core.message_bus import message_bus

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifecycle events.
    
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # Create database tables if needed (for development)
    if settings.ENVIRONMENT == "development":
        logger.info("Creating database tables...")
        await create_tables()
    
    # Initialize Redis connection pool
    await redis_client.connect()
    
    # Start message bus
    await message_bus.start()
    
    # Future startup tasks:
    # - Start background tasks
    # - Connect to external services
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop message bus
    await message_bus.stop()
    
    # Close Redis connections
    await redis_client.disconnect()
    
    # Future shutdown tasks:
    # - Cancel background tasks
    # - Cleanup resources


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered development platform with collaborative agents",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure middleware
configure_middleware(app)

# Include routers with proper prefix
app.include_router(v1_router, prefix="/api/v1")


# Exception handlers
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_type": exc.error_type,
            "request_id": getattr(request.state, "request_id", "unknown")
        },
        headers=getattr(exc, "headers", None)
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "error_type": "ValidationError",
            "errors": exc.errors(),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_type": "HTTPException",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", "unknown")}
    )
    
    # Don't expose internal errors in production
    if settings.DEBUG:
        detail = f"{type(exc).__name__}: {str(exc)}"
    else:
        detail = "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": detail,
            "error_type": "InternalError",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to API docs."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }


# CLI entry point
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    ) 