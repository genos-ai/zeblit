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

from src.backend.api.v1 import api_router
from src.backend.core.config import settings
from src.backend.core.database import init_db
from src.backend.core.middleware import (
    RequestTrackingMiddleware,
    PerformanceMiddleware,
    ErrorHandlingMiddleware,
    CORSMiddleware as CustomCORSMiddleware,
)
from src.backend.config.logging_config import setup_logging, get_logger

# Initialize logging first before any other imports use it
setup_logging(
    app_name="ai_dev_platform",
    log_level=settings.log_level,
    environment=settings.environment
)

# Get logger after setup
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info(
        "Starting AI Development Platform",
        version=settings.version,
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
        title=settings.project_name,
        version=settings.version,
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
        CustomCORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix=settings.api_v1_str)
    
    # Mount static files if in development
    if settings.debug:
        static_dir = Path("static")
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory="static"), name="static")
    
    logger.info(
        "FastAPI application created",
        routes_count=len(app.routes),
        middleware_count=len(app.middleware),
    )
    
    return app


# Create the application instance
app = create_application()


@app.get("/", tags=["root"])
async def root():
    """Root endpoint - redirects to API documentation."""
    return {
        "message": "Welcome to the AI Development Platform API",
        "documentation": f"{settings.api_v1_str}/docs",
        "version": settings.version,
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.environment,
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