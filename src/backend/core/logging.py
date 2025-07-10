"""
Centralized logging configuration for the backend.

Version: 1.0.0
Author: Zeblit Team

## Changelog
- 1.0.0 (2024-01-09): Initial centralized logging setup with file output
"""

import logging
import logging.handlers
import structlog
from pathlib import Path
from datetime import datetime
import sys
import os

from src.backend.core.config import settings


def setup_logging():
    """Configure centralized logging for the application."""
    
    # Create logs directory structure
    log_dir = Path("logs")
    backend_log_dir = log_dir / "backend"
    backend_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure log file paths
    app_log_file = backend_log_dir / f"app-{datetime.now().strftime('%Y-%m-%d')}.log"
    error_log_file = backend_log_dir / f"errors-{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Configure Python's standard logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
    )
    file_handler.setFormatter(file_formatter)
    
    # Error file handler for ERROR and above
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Log startup message
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging system initialized",
        log_level=root_logger.level,
        app_log_file=str(app_log_file),
        error_log_file=str(error_log_file),
        debug_mode=settings.DEBUG
    )
    
    # Also configure uvicorn logging to use our handlers
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.addHandler(file_handler)
    uvicorn_logger.addHandler(error_handler)
    
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = []
    uvicorn_access_logger.addHandler(console_handler)
    uvicorn_access_logger.addHandler(file_handler)
    
    # Configure SQLAlchemy logging
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)  # Only log warnings and errors
    
    return logger


# Create a module-level logger instance
logger = structlog.get_logger(__name__) 