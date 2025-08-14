"""
Debug utilities for Zeblit development.

*Version: 1.0.0*
*Author: Zeblit Team*

## Changelog
- 1.0.0 (2025-01-09): Initial debug utilities for development.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Dict, Optional
import traceback
import inspect

from rich.console import Console
from rich.table import Table
from rich.traceback import install
from rich.pretty import pretty_repr
import structlog

# Install rich traceback handler for better error display
install(show_locals=True)

console = Console()
logger = structlog.get_logger(__name__)


def debug_print(title: str, data: Any, style: str = "bold cyan") -> None:
    """Pretty print debug data with rich formatting."""
    console.print(f"\n[{style}]{title}[/{style}]")
    console.print(pretty_repr(data, max_width=120, indent_size=2))


def timer(func: Callable) -> Callable:
    """Decorator to time function execution."""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(
                f"{func.__name__} completed",
                duration_ms=round(elapsed * 1000, 2),
                args=args[:2] if args else None,  # Log first 2 args only
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(
                f"{func.__name__} failed",
                duration_ms=round(elapsed * 1000, 2),
                error=str(e),
                traceback=traceback.format_exc(),
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(
                f"{func.__name__} completed",
                duration_ms=round(elapsed * 1000, 2),
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(
                f"{func.__name__} failed",
                duration_ms=round(elapsed * 1000, 2),
                error=str(e),
            )
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def trace_calls(cls):
    """Class decorator to trace all method calls."""
    for name, method in inspect.getmembers(cls, inspect.ismethod):
        if not name.startswith('_'):
            setattr(cls, name, timer(method))
    return cls


class DebugContext:
    """Context manager for debugging specific code blocks."""
    
    def __init__(self, name: str, log_locals: bool = True):
        self.name = name
        self.log_locals = log_locals
        self.start_time = None
        self.locals_before = {}
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        if self.log_locals:
            # Capture local variables before block
            frame = inspect.currentframe().f_back
            self.locals_before = dict(frame.f_locals)
        
        console.print(f"\n[green]>>> Entering {self.name}[/green]")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        
        if exc_type:
            console.print(f"[red]<<< {self.name} failed after {elapsed:.3f}s[/red]")
            console.print_exception()
        else:
            console.print(f"[green]<<< {self.name} completed in {elapsed:.3f}s[/green]")
        
        if self.log_locals:
            # Show changed variables
            frame = inspect.currentframe().f_back
            locals_after = dict(frame.f_locals)
            
            changes = {}
            for key, value in locals_after.items():
                if key not in self.locals_before or self.locals_before[key] != value:
                    changes[key] = value
            
            if changes:
                debug_print("Local variable changes:", changes)


def inspect_request(request: Any) -> Dict[str, Any]:
    """Extract and format request details for debugging."""
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "path_params": request.path_params,
        "query_params": dict(request.query_params),
        "client": f"{request.client.host}:{request.client.port}" if request.client else None,
    }


def create_debug_table(title: str, data: Dict[str, Any]) -> Table:
    """Create a rich table for debug output."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    for key, value in data.items():
        table.add_row(key, str(value))
    
    return table


# Environment-specific debug settings
DEBUG_MODE = True  # Set from environment
SQL_ECHO = False   # Echo SQL queries
LOG_REQUESTS = True  # Log all HTTP requests
LOG_RESPONSES = True  # Log all HTTP responses


# Quick debug helpers
def breakpoint():
    """Enhanced breakpoint with context."""
    import pdb
    frame = inspect.currentframe().f_back
    
    console.print("\n[red bold]🔴 BREAKPOINT HIT[/red bold]")
    console.print(f"File: {frame.f_code.co_filename}:{frame.f_lineno}")
    console.print(f"Function: {frame.f_code.co_name}")
    
    # Show local variables
    debug_print("Local Variables:", frame.f_locals)
    
    pdb.set_trace()


# Export commonly used debugging functions
__all__ = [
    "debug_print",
    "timer",
    "trace_calls",
    "DebugContext",
    "inspect_request",
    "create_debug_table",
    "breakpoint",
    "console",
] 