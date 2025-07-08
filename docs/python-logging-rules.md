# Python Logging Standards for AI-Assisted Development

## Primary Library Recommendation: structlog

**USE STRUCTLOG** for all Python projects. It provides the best combination of structured logging, performance, and AI-readability. Install with: `pip install structlog python-json-logger`

## Project Logging Structure

All Python projects MUST follow this directory structure:
```
project_root/
├── logs/
│   ├── app.log              # Current application log (symlink)
│   ├── errors.log           # Current errors only (symlink)
│   ├── daily/
│   │   └── app_2025-01-08.log
│   ├── errors/
│   │   └── errors_2025-01-08.log
│   └── modules/
│       ├── auth/
│       ├── database/
│       └── api/
├── src/
│   └── config/
│       └── logging_config.py
└── .cursorrules
```

## Logging Configuration Template

When creating a new Python project, ALWAYS start with this logging configuration:

```python
# src/config/logging_config.py
import structlog
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

def setup_logging(app_name: str = "app", log_level: str = "INFO", environment: str = "development"):
    """
    Setup structured logging for the application.
    
    ALWAYS call this function at the very beginning of your application,
    before any other imports that might fail.
    """
    # Create log directories
    log_base = Path("logs")
    log_dirs = [
        log_base,
        log_base / "daily",
        log_base / "errors",
        log_base / "modules"
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
        add_app_context,  # Custom processor defined below
    ]
    
    # Add appropriate renderer based on environment
    if environment == "development":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
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
        log_base / "daily" / f"{app_name}_{today}.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(app_handler)
    
    # Error-only log
    error_handler = logging.handlers.RotatingFileHandler(
        log_base / "errors" / f"errors_{today}.log",
        maxBytes=5242880,  # 5MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Create symlinks to latest logs
    create_symlinks(log_base, app_name, today)
    
    # Log startup
    logger = structlog.get_logger()
    logger.info(
        "Logging initialized",
        app_name=app_name,
        environment=environment,
        log_level=log_level,
        python_version=sys.version,
    )

def add_app_context(logger, method_name, event_dict):
    """Add application context to all log entries"""
    # Add any global context you want in every log
    event_dict['hostname'] = os.environ.get('HOSTNAME', 'unknown')
    event_dict['environment'] = os.environ.get('ENVIRONMENT', 'development')
    event_dict['app_version'] = os.environ.get('APP_VERSION', '0.0.0')
    return event_dict

def create_symlinks(log_base: Path, app_name: str, today: str):
    """Create symlinks to latest log files"""
    symlinks = [
        (log_base / "app.log", log_base / "daily" / f"{app_name}_{today}.log"),
        (log_base / "errors.log", log_base / "errors" / f"errors_{today}.log"),
    ]
    
    for symlink, target in symlinks:
        if symlink.exists() or symlink.is_symlink():
            symlink.unlink()
        symlink.symlink_to(target.relative_to(symlink.parent))
```

## Module-Specific Logger Pattern

ALWAYS create loggers using this pattern in each Python module:

```python
import structlog

# At the top of each module
logger = structlog.get_logger(__name__)

class YourClass:
    def __init__(self):
        # Bind class-specific context
        self.logger = logger.bind(class_name=self.__class__.__name__)
    
    def your_method(self, user_id: int, action: str):
        # Bind method-specific context
        method_logger = self.logger.bind(
            method="your_method",
            user_id=user_id,
            action=action
        )
        
        try:
            method_logger.info("Starting operation")
            # Your code here
            result = perform_operation()
            method_logger.info("Operation completed", result_size=len(result))
            return result
            
        except Exception as e:
            method_logger.error(
                "Operation failed",
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise
```

## Error Handling Patterns

ALWAYS use these patterns for error handling and logging:

```python
import structlog
import traceback
import sys
from typing import Any, Dict, Optional
from functools import wraps

logger = structlog.get_logger(__name__)

def log_exceptions(func):
    """Decorator to automatically log exceptions with full context"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_logger = logger.bind(
            function=func.__name__,
            module=func.__module__,
        )
        
        try:
            func_logger.debug("Function called", args=args, kwargs=kwargs)
            result = func(*args, **kwargs)
            func_logger.debug("Function completed successfully")
            return result
            
        except Exception as e:
            # Capture full error context
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # Extract local variables from the error frame
            tb_frame = exc_traceback.tb_frame if exc_traceback else None
            local_vars = {}
            if tb_frame:
                # Safely stringify local variables
                for var_name, var_value in tb_frame.f_locals.items():
                    if not var_name.startswith('_'):
                        try:
                            local_vars[var_name] = str(var_value)[:200]
                        except:
                            local_vars[var_name] = "<unable to serialize>"
            
            func_logger.error(
                "Function raised exception",
                error_type=type(e).__name__,
                error_message=str(e),
                error_file=tb_frame.f_code.co_filename if tb_frame else None,
                error_line=exc_traceback.tb_lineno if exc_traceback else None,
                local_variables=local_vars,
                stack_trace=traceback.format_exc(),
                exc_info=True
            )
            raise
    
    return wrapper

# Usage example
@log_exceptions
def process_user_data(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Example function with automatic exception logging"""
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data).__name__}")
    
    # Process data...
    return {"processed": True, "user_id": user_id}
```

## Web Framework Integration (FastAPI/Flask)

For web applications, ALWAYS implement request tracking:

```python
import structlog
import uuid
import time
from contextvars import ContextVar
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

logger = structlog.get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            logger.info(
                "request_completed",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                "request_failed",
                request_id=request_id,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=round(duration_ms, 2),
                exc_info=True
            )
            raise

# Configure app
app = FastAPI()
app.add_middleware(LoggingMiddleware)

# In route handlers, always include request context
@app.post("/api/users/{user_id}/action")
async def user_action(user_id: int, request: Request):
    # Get request ID from context
    request_id = request_id_var.get()
    
    # Create logger with bound context
    route_logger = logger.bind(
        request_id=request_id,
        user_id=user_id,
        endpoint="user_action"
    )
    
    route_logger.info("Processing user action")
    # Your logic here
```

## Startup Error Handling

ALWAYS implement comprehensive startup error handling:

```python
import structlog
import sys
import traceback

logger = structlog.get_logger(__name__)

def safe_import(module_name: str, critical: bool = True):
    """Safely import modules with error logging"""
    try:
        logger.debug(f"Importing module", module=module_name)
        module = __import__(module_name)
        logger.debug(f"Successfully imported module", module=module_name)
        return module
    except ImportError as e:
        logger.error(
            "Failed to import module",
            module=module_name,
            error_type="ImportError",
            error_message=str(e),
            missing_dependency=e.name if hasattr(e, 'name') else None,
            stack_trace=traceback.format_exc()
        )
        if critical:
            logger.critical("Critical import failed, exiting", module=module_name)
            sys.exit(1)
        return None

def initialize_application():
    """Initialize application with comprehensive error handling"""
    logger.info("Starting application initialization")
    
    try:
        # Setup logging first
        from config.logging_config import setup_logging
        setup_logging()
        
        # Import dependencies with error handling
        critical_modules = [
            'database.connection',
            'config.settings',
            'api.routes'
        ]
        
        for module in critical_modules:
            safe_import(module, critical=True)
        
        # Initialize components
        logger.info("Initializing database connection")
        # Your initialization code here
        
        logger.info("Application initialization completed successfully")
        
    except Exception as e:
        logger.critical(
            "Application initialization failed",
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc(),
            exc_info=True
        )
        sys.exit(1)

if __name__ == "__main__":
    initialize_application()
```

## AI Assistant Instructions for Log Analysis

When analyzing logs in this project:

1. **ALWAYS check these locations first:**
   - `logs/errors.log` - For recent errors
   - `logs/app.log` - For general application flow
   - `logs/modules/*/` - For module-specific issues

2. **Look for these patterns in JSON logs:**
   - `"level": "error"` or `"level": "critical"` - For errors
   - `"exc_info":` - For stack traces
   - `"error_type":` - For exception types
   - `"local_variables":` - For debugging context
   - `"request_id":` - For tracing specific requests

3. **When debugging errors:**
   - Find the error entry by searching for the error message
   - Look for the request_id to trace the full request flow
   - Check local_variables for the state when error occurred
   - Use stack_trace to identify the exact error location

4. **Common error patterns to recognize:**
   ```json
   {
     "level": "error",
     "error_type": "ImportError",
     "error_message": "No module named 'core'",
     "error_file": "/path/to/file.py",
     "error_line": 14
   }
   ```

5. **To trace a request:**
   ```bash
   # Search for all logs with a specific request_id
   grep "request_id.*abc-123" logs/app.log | jq '.'
   ```

## Performance Monitoring Patterns

ALWAYS include performance metrics in logs:

```python
import structlog
import time
from contextlib import contextmanager
from functools import wraps

logger = structlog.get_logger(__name__)

@contextmanager
def log_performance(operation_name: str, **context):
    """Context manager for logging operation performance"""
    operation_logger = logger.bind(operation=operation_name, **context)
    operation_logger.info(f"Starting {operation_name}")
    
    start_time = time.time()
    start_memory = get_memory_usage()  # Implement based on your needs
    
    try:
        yield operation_logger
    finally:
        duration_ms = (time.time() - start_time) * 1000
        memory_delta = get_memory_usage() - start_memory
        
        operation_logger.info(
            f"Completed {operation_name}",
            duration_ms=round(duration_ms, 2),
            memory_delta_mb=round(memory_delta / 1024 / 1024, 2)
        )

def log_slow_operations(threshold_ms: float = 1000):
    """Decorator to log slow operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            if duration_ms > threshold_ms:
                logger.warning(
                    "Slow operation detected",
                    function=func.__name__,
                    duration_ms=round(duration_ms, 2),
                    threshold_ms=threshold_ms
                )
            
            return result
        return wrapper
    return decorator

# Usage
with log_performance("database_query", query_type="user_lookup"):
    results = database.query("SELECT * FROM users")

@log_slow_operations(threshold_ms=500)
def process_large_dataset(data):
    # Your processing logic
    pass
```

## Testing and Log Verification

Include log verification in tests:

```python
import structlog
from structlog.testing import LogCapture
import pytest

@pytest.fixture
def log_capture():
    """Fixture to capture structlog output in tests"""
    cap = LogCapture()
    structlog.configure(processors=[cap])
    yield cap
    structlog.reset_defaults()

def test_error_logging(log_capture):
    """Test that errors are logged correctly"""
    logger = structlog.get_logger()
    
    # Trigger an error
    try:
        raise ValueError("Test error")
    except ValueError:
        logger.error("Test error occurred", exc_info=True)
    
    # Verify log output
    assert len(log_capture.entries) == 1
    assert log_capture.entries[0]["event"] == "Test error occurred"
    assert "error_type" in log_capture.entries[0]
    assert log_capture.entries[0]["error_type"] == "ValueError"
```

## Environment-Specific Configuration

```python
import os
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

def get_log_config():
    """Get environment-specific logging configuration"""
    env = Environment(os.getenv("ENVIRONMENT", "development"))
    
    configs = {
        Environment.DEVELOPMENT: {
            "log_level": "DEBUG",
            "format": "console",  # Human-readable
            "log_to_file": True,
            "log_to_console": True,
        },
        Environment.STAGING: {
            "log_level": "INFO",
            "format": "json",
            "log_to_file": True,
            "log_to_console": True,
        },
        Environment.PRODUCTION: {
            "log_level": "WARNING",
            "format": "json",
            "log_to_file": True,
            "log_to_console": False,  # Rely on file logs in production
        }
    }
    
    return configs[env]
```

## CRITICAL RULES FOR AI ASSISTANTS

1. **NEVER use print() for debugging** - Always use proper logging
2. **ALWAYS check for existing loggers** before creating new ones
3. **ALWAYS include exc_info=True** when logging exceptions
4. **ALWAYS use structured logging** (key-value pairs, not string formatting)
5. **NEVER log sensitive information** (passwords, API keys, PII)
6. **ALWAYS create logs directory** before attempting to write logs
7. **ALWAYS use UTC timestamps** in production environments
8. **ALWAYS include request IDs** in web applications
9. **ALWAYS log at appropriate levels**:
   - DEBUG: Detailed information for diagnosing problems
   - INFO: General informational messages
   - WARNING: Warning messages for potentially harmful situations
   - ERROR: Error events that might still allow the application to continue
   - CRITICAL: Critical problems that have caused the application to fail

## Quick Setup for New Projects

```bash
# Install dependencies
pip install structlog python-json-logger

# Create logging structure
mkdir -p logs/{daily,errors,modules}

# Add to your main.py or app.py
from config.logging_config import setup_logging
setup_logging(app_name="myapp")

# Start logging
import structlog
logger = structlog.get_logger(__name__)
logger.info("Application started")
```

Remember: **Good logging is the foundation of effective debugging. When in doubt, log it out!**