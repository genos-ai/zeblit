"""
Main entry point for the AI Development Platform backend.

Initializes the FastAPI application with all routes, middleware,
and configurations.
"""

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import structlog

from modules.backend.api.v1 import api_router
from modules.backend.core.config import settings
from modules.backend.core.database import init_db
from modules.backend.core.middleware import (
    RequestTrackingMiddleware,
    PerformanceMiddleware,
    ErrorHandlingMiddleware,
)
from modules.backend.config.logging_config import setup_logging

# Get logger
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Initialize logging first
    setup_logging(
        app_name="zeblit_platform",
        log_level=settings.log_level,
        environment=settings.environment
    )
    
    # Startup
    logger.info(
        "Starting AI Development Platform",
        version=settings.VERSION,
        environment=settings.environment,
        debug=settings.debug,
    )
    
    # Initialize database
    logger.info("Initializing database")
    await init_db()
    
    # Create necessary directories
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Development Platform")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        openapi_url="/api/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Configure middleware (order matters - outermost first)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(PerformanceMiddleware, slow_request_threshold=3.0)
    app.add_middleware(RequestTrackingMiddleware)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Mount static files if in development
    if settings.debug:
        static_dir = Path("static")
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory="static"), name="static")
    
    logger.info(
        "FastAPI application created",
        routes_count=len(app.routes),
    )
    
    return app


# Create the application instance
app = create_application()


@app.get("/", tags=["root"])
async def root():
    """Root endpoint - redirects to API documentation."""
    return {
        "message": "Welcome to the AI Development Platform API",
        "documentation": f"{settings.API_V1_STR}/docs",
        "version": settings.VERSION,
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.environment,
    }


@app.get("/v1/models", tags=["compatibility"])
async def models_compatibility():
    """
    OpenAI-compatible models endpoint.
    
    This endpoint provides compatibility with tools that expect
    the models endpoint at /v1/models instead of /api/v1/models.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "claude-3-5-sonnet-20241022",
                "object": "model",
                "created": 1640995200,
                "owned_by": "anthropic",
                "permission": [],
                "root": "claude-3-5-sonnet-20241022",
                "parent": None
            },
            {
                "id": "gpt-4o-mini",
                "object": "model", 
                "created": 1640995200,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-4o-mini",
                "parent": None
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    ) 