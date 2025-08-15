"""
Progress utilities for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial progress utilities implementation.
"""

import asyncio
import time
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager

from rich.console import Console
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.spinner import Spinner

console = Console()


class ProgressManager:
    """Manager for various progress indicators."""
    
    def __init__(self):
        """Initialize progress manager."""
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None
    
    @asynccontextmanager
    async def spinner(self, message: str, success_message: str = None):
        """
        Show a spinner for async operations.
        
        Args:
            message: Message to show during operation
            success_message: Message to show on success
        """
        with console.status(f"[blue]{message}[/blue]", spinner="dots") as status:
            try:
                yield status
                if success_message:
                    console.print(f"✅ [green]{success_message}[/green]")
            except Exception as e:
                console.print(f"❌ [red]Failed: {str(e)}[/red]")
                raise
    
    @asynccontextmanager
    async def progress_bar(
        self, 
        description: str, 
        total: Optional[int] = None,
        show_speed: bool = False
    ):
        """
        Show a progress bar for operations with known total.
        
        Args:
            description: Description of the operation
            total: Total number of items (None for indeterminate)
            show_speed: Whether to show transfer speed
        """
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ]
        
        if total is not None:
            columns.extend([
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
            ])
        
        with Progress(*columns, console=console) as progress:
            self._progress = progress
            self._task_id = progress.add_task(description, total=total)
            
            try:
                yield self
            finally:
                self._progress = None
                self._task_id = None
    
    def advance(self, amount: int = 1):
        """Advance the progress bar."""
        if self._progress and self._task_id is not None:
            self._progress.advance(self._task_id, amount)
    
    def update(self, completed: int = None, description: str = None):
        """Update progress bar state."""
        if self._progress and self._task_id is not None:
            kwargs = {}
            if completed is not None:
                kwargs["completed"] = completed
            if description is not None:
                kwargs["description"] = description
            
            if kwargs:
                self._progress.update(self._task_id, **kwargs)


# Global progress manager instance
progress_manager = ProgressManager()


async def with_progress(
    coro,
    message: str = "Processing...",
    success_message: str = None
):
    """
    Run a coroutine with a progress spinner.
    
    Args:
        coro: Coroutine to run
        message: Message to show during operation
        success_message: Message to show on success
        
    Returns:
        Result of the coroutine
    """
    async with progress_manager.spinner(message, success_message):
        return await coro


def show_error(message: str, details: str = None, suggestion: str = None):
    """
    Show a formatted error message.
    
    Args:
        message: Main error message
        details: Additional error details
        suggestion: Suggestion for fixing the error
    """
    console.print(f"❌ [red]Error:[/red] {message}")
    
    if details:
        console.print(f"   [dim]{details}[/dim]")
    
    if suggestion:
        console.print(f"💡 [blue]Suggestion:[/blue] {suggestion}")


def show_warning(message: str, details: str = None):
    """
    Show a formatted warning message.
    
    Args:
        message: Warning message
        details: Additional warning details
    """
    console.print(f"⚠️  [yellow]Warning:[/yellow] {message}")
    
    if details:
        console.print(f"   [dim]{details}[/dim]")


def show_success(message: str, details: str = None):
    """
    Show a formatted success message.
    
    Args:
        message: Success message
        details: Additional success details
    """
    console.print(f"✅ [green]Success:[/green] {message}")
    
    if details:
        console.print(f"   [dim]{details}[/dim]")


def show_info(message: str, details: str = None):
    """
    Show a formatted info message.
    
    Args:
        message: Info message
        details: Additional info details
    """
    console.print(f"ℹ️  [blue]Info:[/blue] {message}")
    
    if details:
        console.print(f"   [dim]{details}[/dim]")


async def simulate_progress_task(
    task_func: Callable,
    total_items: int,
    description: str = "Processing items..."
):
    """
    Simulate a progress task for operations that don't have built-in progress.
    
    Args:
        task_func: Function to call for each item
        total_items: Total number of items to process
        description: Description for the progress bar
        
    Returns:
        List of results from task_func
    """
    results = []
    
    async with progress_manager.progress_bar(description, total_items) as pm:
        for i in range(total_items):
            result = await task_func(i) if asyncio.iscoroutinefunction(task_func) else task_func(i)
            results.append(result)
            pm.advance(1)
            
            # Small delay to make progress visible
            await asyncio.sleep(0.01)
    
    return results


class FileTransferProgress:
    """Progress tracker for file transfers."""
    
    def __init__(self, filename: str, total_size: int):
        """Initialize file transfer progress."""
        self.filename = filename
        self.total_size = total_size
        self.transferred = 0
        self.start_time = time.time()
    
    def update(self, bytes_transferred: int):
        """Update transfer progress."""
        self.transferred += bytes_transferred
        
        # Calculate speed
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            speed = self.transferred / elapsed
            speed_str = self._format_bytes(speed) + "/s"
        else:
            speed_str = "0 B/s"
        
        # Calculate percentage
        if self.total_size > 0:
            percentage = (self.transferred / self.total_size) * 100
            console.print(
                f"📁 {self.filename}: {percentage:.1f}% "
                f"({self._format_bytes(self.transferred)}/{self._format_bytes(self.total_size)}) "
                f"at {speed_str}",
                end="\r"
            )
        else:
            console.print(
                f"📁 {self.filename}: {self._format_bytes(self.transferred)} at {speed_str}",
                end="\r"
            )
    
    def complete(self):
        """Mark transfer as complete."""
        elapsed = time.time() - self.start_time
        avg_speed = self.transferred / elapsed if elapsed > 0 else 0
        
        console.print(
            f"✅ {self.filename}: {self._format_bytes(self.transferred)} "
            f"in {elapsed:.1f}s (avg {self._format_bytes(avg_speed)}/s)"
        )
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} TB"
