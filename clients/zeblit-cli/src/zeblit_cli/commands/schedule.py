"""
Scheduled task management commands for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial schedule commands.
"""

import asyncio
import logging
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.panel import Panel

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import get_auth_manager
from zeblit_cli.api.client import ZeblitAPIClient, APIError
from zeblit_cli.utils import (
    with_progress,
    show_error,
    show_success,
    show_info,
    project_id_completion
)

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def schedule_commands():
    """Scheduled task management commands."""
    pass


@schedule_commands.command("create")
@click.argument("name")
@click.argument("command")
@click.option("--schedule", "-s", required=True, help="Cron expression (e.g., '0 0 * * *')")
@click.option("--project", "-p", help="Project ID")
@click.option("--description", "-d", help="Task description")
@click.option("--working-dir", "-w", default="/workspace", help="Working directory")
@click.option("--timeout", "-t", default=300, type=int, help="Timeout in seconds")
@click.option("--retries", "-r", default=3, type=int, help="Maximum retry attempts")
@click.option("--preset", help="Use preset schedule (daily, hourly, weekly)")
def create_task(
    name: str,
    command: str,
    schedule: Optional[str],
    project: Optional[str],
    description: Optional[str],
    working_dir: str,
    timeout: int,
    retries: int,
    preset: Optional[str]
):
    """Create a new scheduled task."""
    asyncio.run(create_task_cmd(
        name, command, schedule, project, description, 
        working_dir, timeout, retries, preset
    ))


async def create_task_cmd(
    name: str,
    command: str,
    schedule: Optional[str],
    project_id: Optional[str],
    description: Optional[str],
    working_dir: str,
    timeout: int,
    retries: int,
    preset: Optional[str]
):
    """Create scheduled task command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        # Use current project if not specified
        if not project_id:
            project_id = settings.current_project_id
            if not project_id:
                show_error("No project specified", 
                          suggestion="Use --project or set active project with 'zeblit use <project-id>'")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            # Use preset if specified
            if preset:
                task_data = {
                    "name": name,
                    "project_id": project_id,
                    "preset": preset,
                    "command": command
                }
                if schedule and preset == "custom":
                    task_data["custom_schedule"] = schedule
                
                task = await with_progress(
                    api_client._request("POST", "/scheduled-tasks/quick", task_data),
                    f"Creating scheduled task '{name}' with {preset} preset...",
                    "Task created successfully!"
                )
            else:
                if not schedule:
                    show_error("Schedule is required", 
                              suggestion="Use --schedule or --preset option")
                    return
                
                task_data = {
                    "name": name,
                    "project_id": project_id,
                    "schedule": schedule,
                    "command": command,
                    "working_directory": working_dir,
                    "timeout_seconds": timeout,
                    "max_retries": retries
                }
                if description:
                    task_data["description"] = description
                
                task = await with_progress(
                    api_client._request("POST", "/scheduled-tasks/", task_data),
                    f"Creating scheduled task '{name}'...",
                    "Task created successfully!"
                )
            
            task_info = task.get("data", task)
            
            show_success(f"Scheduled task '{task_info.get('name')}' created!")
            show_info(f"Task ID: {task_info.get('id')}")
            show_info(f"Schedule: {task_info.get('schedule')}")
            show_info(f"Next run: {task_info.get('next_run_at', 'N/A')}")
            
            console.print("\n💡 [blue]Quick commands:[/blue]")
            console.print(f"  • [bold]zeblit schedule list[/bold] - View all tasks")
            console.print(f"  • [bold]zeblit schedule run {task_info.get('id')[:8]}[/bold] - Run immediately")
            console.print(f"  • [bold]zeblit schedule status {task_info.get('id')[:8]}[/bold] - Check status")
            
    except APIError as e:
        show_error("Failed to create scheduled task", str(e))
    except Exception as e:
        show_error("Unexpected error", str(e))


@schedule_commands.command("list")
@click.option("--project", "-p", help="Project ID")
@click.option("--enabled-only", is_flag=True, help="Only show enabled tasks")
def list_tasks(project: Optional[str], enabled_only: bool):
    """List scheduled tasks."""
    asyncio.run(list_tasks_cmd(project, enabled_only))


async def list_tasks_cmd(project_id: Optional[str], enabled_only: bool):
    """List tasks command implementation."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            params = {}
            if project_id:
                params["project_id"] = project_id
            if enabled_only:
                params["enabled_only"] = "true"
            
            tasks = await api_client._request("GET", "/scheduled-tasks/", params=params)
            task_list = tasks.get("data", tasks)
            
            if not task_list:
                console.print("📋 No scheduled tasks found")
                if not project_id:
                    console.print("💡 Create one with: [bold]zeblit schedule create <name> <command> --schedule '0 9 * * *'[/bold]")
                return
            
            # Create table
            table = Table(title=f"Scheduled Tasks ({len(task_list)})")
            table.add_column("Name", style="cyan", min_width=20)
            table.add_column("Schedule", style="green")
            table.add_column("Status", justify="center")
            table.add_column("Last Run", style="dim")
            table.add_column("Success Rate", justify="right")
            table.add_column("ID", style="dim", min_width=8)
            
            for task in task_list:
                # Status with emoji
                status = "🟢 Enabled" if task.get("is_enabled") else "🔴 Disabled"
                if task.get("is_overdue"):
                    status = "⏰ Overdue"
                
                # Last run time
                last_run = task.get("last_run_at")
                if last_run:
                    last_run = last_run.split("T")[0]  # Just date
                else:
                    last_run = "Never"
                
                # Success rate
                success_rate = f"{task.get('success_rate', 0):.1f}%"
                
                table.add_row(
                    task.get("name", "N/A"),
                    task.get("schedule", "N/A"),
                    status,
                    last_run,
                    success_rate,
                    task.get("id", "")[:8]
                )
            
            console.print(table)
            
            # Show summary
            enabled_count = sum(1 for t in task_list if t.get("is_enabled"))
            overdue_count = sum(1 for t in task_list if t.get("is_overdue"))
            
            summary_panel = Panel(
                f"📊 Summary: {enabled_count} enabled, {len(task_list) - enabled_count} disabled"
                + (f", {overdue_count} overdue" if overdue_count > 0 else ""),
                title="Task Overview"
            )
            console.print(summary_panel)
            
    except Exception as e:
        show_error("Failed to list scheduled tasks", str(e))


@schedule_commands.command("status")
@click.argument("task_id")
@click.option("--runs", "-r", default=10, type=int, help="Number of recent runs to show")
def task_status(task_id: str, runs: int):
    """Show detailed status of a scheduled task."""
    asyncio.run(task_status_cmd(task_id, runs))


async def task_status_cmd(task_id: str, runs: int):
    """Task status command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            params = {"include_runs": "true", "run_limit": str(runs)}
            task = await api_client._request("GET", f"/scheduled-tasks/{task_id}", params=params)
            task_data = task.get("data", task)
            
            # Task info
            console.print(f"\n📋 [bold]Task: {task_data.get('name')}[/bold]")
            console.print(f"🆔 ID: {task_data.get('id')}")
            console.print(f"📅 Schedule: {task_data.get('schedule')}")
            console.print(f"🔧 Command: {task_data.get('command')}")
            
            # Status
            status = "🟢 Enabled" if task_data.get("is_enabled") else "🔴 Disabled"
            if task_data.get("is_overdue"):
                status = "⏰ Overdue"
            console.print(f"📊 Status: {status}")
            
            # Timing
            next_run = task_data.get("next_run_at", "N/A")
            last_run = task_data.get("last_run_at", "Never")
            console.print(f"⏰ Next run: {next_run}")
            console.print(f"🕐 Last run: {last_run}")
            
            # Statistics
            console.print(f"\n📈 [bold]Statistics[/bold]")
            console.print(f"Total runs: {task_data.get('total_runs', 0)}")
            console.print(f"Successful: {task_data.get('successful_runs', 0)}")
            console.print(f"Failed: {task_data.get('failed_runs', 0)}")
            console.print(f"Success rate: {task_data.get('success_rate', 0):.1f}%")
            
            # Recent runs
            task_runs = task_data.get("task_runs", [])
            if task_runs:
                console.print(f"\n🔄 [bold]Recent Runs[/bold]")
                
                runs_table = Table()
                runs_table.add_column("Started", style="dim")
                runs_table.add_column("Status", justify="center")
                runs_table.add_column("Duration", justify="right")
                runs_table.add_column("Exit Code", justify="center")
                
                for run in task_runs[:runs]:
                    # Status with emoji
                    status_emoji = {
                        "success": "✅",
                        "failed": "❌", 
                        "running": "🔄",
                        "timeout": "⏱️"
                    }.get(run.get("status", "unknown"), "❓")
                    
                    # Duration
                    duration = run.get("duration_seconds")
                    if duration:
                        duration_str = f"{duration:.1f}s"
                    else:
                        duration_str = "N/A"
                    
                    # Started time
                    started = run.get("started_at", "")
                    if started:
                        started = started.split("T")[1][:8]  # Just time
                    
                    runs_table.add_row(
                        started,
                        f"{status_emoji} {run.get('status', 'unknown')}",
                        duration_str,
                        str(run.get("exit_code", "N/A"))
                    )
                
                console.print(runs_table)
            else:
                console.print("\n🔄 No execution history")
            
    except Exception as e:
        show_error("Failed to get task status", str(e))


@schedule_commands.command("run")
@click.argument("task_id")
def run_task(task_id: str):
    """Execute a scheduled task immediately."""
    asyncio.run(run_task_cmd(task_id))


async def run_task_cmd(task_id: str):
    """Run task command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            result = await with_progress(
                api_client._request("POST", f"/scheduled-tasks/{task_id}/execute"),
                "Starting task execution...",
                "Task execution started!"
            )
            
            result_data = result.get("data", result)
            
            show_success("Task execution initiated")
            show_info(f"Run ID: {result_data.get('run_id')}")
            show_info(f"Status: {result_data.get('status')}")
            
            console.print("\n💡 Check status with: [bold]zeblit schedule status " + task_id[:8] + "[/bold]")
            
    except Exception as e:
        show_error("Failed to execute task", str(e))


@schedule_commands.command("enable")
@click.argument("task_id")
def enable_task(task_id: str):
    """Enable a scheduled task."""
    asyncio.run(enable_task_cmd(task_id))


async def enable_task_cmd(task_id: str):
    """Enable task command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            await api_client._request("POST", f"/scheduled-tasks/{task_id}/enable")
            show_success("Task enabled successfully")
            
    except Exception as e:
        show_error("Failed to enable task", str(e))


@schedule_commands.command("disable")
@click.argument("task_id")
def disable_task(task_id: str):
    """Disable a scheduled task."""
    asyncio.run(disable_task_cmd(task_id))


async def disable_task_cmd(task_id: str):
    """Disable task command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            await api_client._request("POST", f"/scheduled-tasks/{task_id}/disable")
            show_success("Task disabled successfully")
            
    except Exception as e:
        show_error("Failed to disable task", str(e))


@schedule_commands.command("delete")
@click.argument("task_id")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def delete_task(task_id: str, force: bool):
    """Delete a scheduled task."""
    asyncio.run(delete_task_cmd(task_id, force))


async def delete_task_cmd(task_id: str, force: bool):
    """Delete task command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        await auth_manager.require_auth()
        
        # Confirm deletion unless forced
        if not force:
            if not Confirm.ask(f"Are you sure you want to delete task {task_id[:8]}?"):
                console.print("❌ Deletion cancelled")
                return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            await with_progress(
                api_client._request("DELETE", f"/scheduled-tasks/{task_id}"),
                "Deleting scheduled task...",
                "Task deleted successfully!"
            )
            
    except Exception as e:
        show_error("Failed to delete task", str(e))


@schedule_commands.command("validate")
@click.argument("schedule")
def validate_schedule(schedule: str):
    """Validate a cron schedule expression."""
    asyncio.run(validate_schedule_cmd(schedule))


async def validate_schedule_cmd(schedule: str):
    """Validate schedule command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            data = {"schedule": schedule}
            result = await api_client._request("POST", "/scheduled-tasks/validate-schedule", data)
            validation = result.get("data", result)
            
            if validation.get("is_valid"):
                show_success(f"Schedule '{schedule}' is valid")
                
                # Show next execution times
                next_runs = validation.get("next_runs", [])
                if next_runs:
                    console.print("\n⏰ [bold]Next 5 executions:[/bold]")
                    for i, run_time in enumerate(next_runs[:5], 1):
                        console.print(f"  {i}. {run_time}")
                
                # Show human readable description if available
                human_readable = validation.get("human_readable")
                if human_readable:
                    console.print(f"\n📝 Description: {human_readable}")
            else:
                show_error("Invalid schedule", validation.get("error_message", "Unknown error"))
                
                # Show some examples
                console.print("\n💡 [blue]Common examples:[/blue]")
                console.print("  • [bold]0 9 * * *[/bold] - Daily at 9:00 AM")
                console.print("  • [bold]0 */2 * * *[/bold] - Every 2 hours")
                console.print("  • [bold]0 0 * * 1[/bold] - Weekly on Monday")
                console.print("  • [bold]*/15 * * * *[/bold] - Every 15 minutes")
            
    except Exception as e:
        show_error("Failed to validate schedule", str(e))


@schedule_commands.command("stats")
@click.option("--project", "-p", help="Project ID")
def task_stats(project: Optional[str]):
    """Show scheduled task statistics."""
    asyncio.run(task_stats_cmd(project))


async def task_stats_cmd(project_id: Optional[str]):
    """Task stats command implementation."""
    try:
        auth_manager = get_auth_manager()
        
        await auth_manager.require_auth()
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            auth_manager.set_api_client(api_client)
            
            params = {}
            if project_id:
                params["project_id"] = project_id
            
            stats = await api_client._request("GET", "/scheduled-tasks/stats/overview", params=params)
            stats_data = stats.get("data", stats)
            
            console.print("\n📊 [bold]Scheduled Task Statistics[/bold]")
            
            # Task counts
            console.print(f"📋 Total tasks: {stats_data.get('total_tasks', 0)}")
            console.print(f"🟢 Enabled: {stats_data.get('enabled_tasks', 0)}")
            console.print(f"🔴 Disabled: {stats_data.get('disabled_tasks', 0)}")
            console.print(f"⏰ Overdue: {stats_data.get('overdue_tasks', 0)}")
            
            # Execution stats
            console.print(f"\n🔄 [bold]Execution Summary[/bold]")
            console.print(f"Total runs: {stats_data.get('total_runs_today', 0)}")
            console.print(f"✅ Successful: {stats_data.get('successful_runs_today', 0)}")
            console.print(f"❌ Failed: {stats_data.get('failed_runs_today', 0)}")
            console.print(f"📈 Success rate: {stats_data.get('success_rate_today', 0):.1f}%")
            
    except Exception as e:
        show_error("Failed to get task statistics", str(e))
