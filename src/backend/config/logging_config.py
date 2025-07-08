"""
Logging configuration for the AI Development Platform.

Sets up structured logging with structlog for better debugging,
especially for AI agent interactions and performance monitoring.
"""

import structlog
import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import json

# Context variable for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

def find_project_root() -> Path:
    """Find the project root by looking for .project_root file."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / ".project_root").exists():
            return current
        current = current.parent
    return Path.cwd()

def add_app_context(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add application context to all log entries."""
    # Add request ID if available
    request_id = request_id_var.get()
    if request_id:
        event_dict['request_id'] = request_id
    
    # Add application metadata
    event_dict['hostname'] = os.environ.get('HOSTNAME', 'unknown')
    event_dict['environment'] = os.environ.get('ENVIRONMENT', 'development')
    event_dict['app_version'] = os.environ.get('APP_VERSION', '0.0.0')
    event_dict['service'] = 'backend'
    
    return event_dict

def setup_logging(
    app_name: str = "ai_dev_platform",
    log_level: str = "INFO",
    environment: str = "development"
):
    """
    Setup structured logging for the application.
    
    Args:
        app_name: Name of the application
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment (development, staging, production)
    """
    # Find project root and create log directories
    project_root = find_project_root()
    log_base = project_root / "logs"
    log_dirs = [
        log_base,
        log_base / "backend",
        log_base / "daily",
        log_base / "errors",
        log_base / "archive"
    ]
    
    for log_dir in log_dirs:
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure timestamp
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_app_context,  # Custom processor for app context
    ]
    
    # Add appropriate renderer based on environment
    if environment == "development":
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Add file handlers
    root_logger = logging.getLogger()
    
    # Main application log
    app_handler = logging.handlers.RotatingFileHandler(
        log_base / "backend" / f"{app_name}_{today}.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(app_handler)
    
    # Error-only log
    error_handler = logging.handlers.RotatingFileHandler(
        log_base / "errors" / f"errors_{today}.log",
        maxBytes=5242880,  # 5MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Daily rotating handler for all logs
    daily_handler = logging.handlers.TimedRotatingFileHandler(
        log_base / "daily" / f"{app_name}.log",
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days
        encoding='utf-8'
    )
    daily_handler.setLevel(logging.INFO)
    root_logger.addHandler(daily_handler)
    
    # Create symlinks to latest logs
    create_symlinks(log_base, app_name, today)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup
    logger = structlog.get_logger()
    logger.info(
        "Logging initialized",
        app_name=app_name,
        environment=environment,
        log_level=log_level,
        python_version=sys.version,
        log_directory=str(log_base),
    )

def create_symlinks(log_base: Path, app_name: str, today: str):
    """Create symlinks to latest log files for easy access."""
    symlinks = [
        (log_base / "app.log", log_base / "backend" / f"{app_name}_{today}.log"),
        (log_base / "errors.log", log_base / "errors" / f"errors_{today}.log"),
    ]
    
    for symlink, target in symlinks:
        try:
            # Remove existing symlink if it exists
            if symlink.exists() or symlink.is_symlink():
                symlink.unlink()
            
            # Create relative symlink
            symlink.symlink_to(target.relative_to(symlink.parent))
        except (OSError, NotImplementedError):
            # Windows or permission issues - skip symlinks
            pass

def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)

def set_request_id(request_id: str):
    """Set the request ID for the current context."""
    request_id_var.set(request_id)

def clear_request_id():
    """Clear the request ID from the current context."""
    request_id_var.set(None)

# Performance monitoring decorator
from functools import wraps
import time
from typing import Callable

def log_performance(threshold_ms: float = 1000):
    """
    Decorator to log slow operations.
    
    Args:
        threshold_ms: Log if operation takes longer than this (milliseconds)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = structlog.get_logger().bind(
                function=func.__name__,
                module=func.__module__,
            )
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        "Slow operation detected",
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=threshold_ms,
                    )
                else:
                    logger.debug(
                        "Operation completed",
                        duration_ms=round(duration_ms, 2),
                    )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "Operation failed",
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = structlog.get_logger().bind(
                function=func.__name__,
                module=func.__module__,
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        "Slow operation detected",
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=threshold_ms,
                    )
                else:
                    logger.debug(
                        "Operation completed",
                        duration_ms=round(duration_ms, 2),
                    )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "Operation failed",
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                )
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Context manager for operation logging
from contextlib import contextmanager
import asyncio

@contextmanager
def log_operation(operation_name: str, **context):
    """Context manager for logging operation performance."""
    logger = structlog.get_logger().bind(operation=operation_name, **context)
    logger.info(f"Starting {operation_name}")
    
    start_time = time.time()
    
    try:
        yield logger
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Completed {operation_name}",
            duration_ms=round(duration_ms, 2),
        )

# Exception logging decorator
def log_exceptions(func: Callable):
    """Decorator to automatically log exceptions with full context."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = structlog.get_logger().bind(
            function=func.__name__,
            module=func.__module__,
        )
        
        try:
            logger.debug("Function called", args_count=len(args), kwargs_keys=list(kwargs.keys()))
            result = func(*args, **kwargs)
            logger.debug("Function completed successfully")
            return result
            
        except Exception as e:
            # Capture exception details
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            
            logger.error(
                "Function raised exception",
                error_type=type(e).__name__,
                error_message=str(e),
                error_file=tb[-1].filename if tb else None,
                error_line=tb[-1].lineno if tb else None,
                error_function=tb[-1].name if tb else None,
                stack_trace=traceback.format_exc(),
                exc_info=True,
            )
            raise
    
    return wrapper

# AI-specific logging contexts
def log_llm_request(
    model: str,
    prompt_tokens: int,
    max_tokens: int,
    temperature: float,
    **kwargs
) -> structlog.BoundLogger:
    """Create a logger with LLM request context."""
    return structlog.get_logger().bind(
        ai_request=True,
        model=model,
        prompt_tokens=prompt_tokens,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )

def log_llm_response(
    logger: structlog.BoundLogger,
    response_tokens: int,
    total_tokens: int,
    cost_usd: float,
    duration_ms: float,
    **kwargs
):
    """Log LLM response with cost and performance metrics."""
    logger.info(
        "LLM request completed",
        response_tokens=response_tokens,
        total_tokens=total_tokens,
        cost_usd=round(cost_usd, 4),
        duration_ms=round(duration_ms, 2),
        tokens_per_second=round(total_tokens / (duration_ms / 1000), 2),
        **kwargs
    ) 