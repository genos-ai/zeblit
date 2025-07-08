"""
Console service for capturing and managing console logs/errors.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial console service implementation.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

from src.backend.core.redis_client import redis_client
from src.backend.core.message_bus import message_bus, MessageType, Message
from src.backend.schemas.websocket import ConsoleLogPayload, ErrorLogPayload

logger = logging.getLogger(__name__)


class ConsoleService:
    """Service for managing console logs and errors."""
    
    def __init__(self):
        """Initialize console service."""
        self.max_logs_per_project = 1000
        self.console_ttl = 86400  # 24 hours
    
    async def store_console_log(
        self,
        project_id: UUID,
        user_id: UUID,
        log_data: ConsoleLogPayload
    ) -> None:
        """
        Store console log in Redis.
        
        Args:
            project_id: Project ID
            user_id: User ID who generated the log
            log_data: Console log data
        """
        try:
            key = f"console:{project_id}"
            
            # Create log entry
            log_entry = {
                "id": str(uuid4()),
                "user_id": str(user_id),
                "project_id": str(project_id),
                "timestamp": datetime.utcnow().isoformat(),
                "level": log_data.level,
                "message": log_data.message,
                "args": log_data.args,
                "stack_trace": log_data.stack_trace,
                "source": log_data.source,
                "line": log_data.line,
                "column": log_data.column
            }
            
            # Store in Redis list
            await redis_client.lpush(key, log_entry)
            
            # Keep only last N logs
            await redis_client.ltrim(key, 0, self.max_logs_per_project - 1)
            
            # Set TTL on the key
            await redis_client.expire(key, self.console_ttl)
            
            # Publish to message bus for AI agents
            await message_bus.publish(
                f"console:{project_id}",
                Message(
                    type=MessageType.CONSOLE_LOG,
                    sender="console_service",
                    payload=log_entry,
                    project_id=project_id
                )
            )
            
            # Track console statistics
            await self._update_console_stats(project_id, log_data.level)
            
            logger.debug(f"Stored console log for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to store console log: {e}")
    
    async def store_error_log(
        self,
        project_id: UUID,
        user_id: UUID,
        error_data: ErrorLogPayload
    ) -> None:
        """
        Store error log in Redis with special handling.
        
        Args:
            project_id: Project ID
            user_id: User ID who generated the error
            error_data: Error log data
        """
        try:
            # Store as console log with error level
            console_log = ConsoleLogPayload(
                level="error",
                message=error_data.message,
                stack_trace=error_data.stack,
                source=error_data.filename,
                line=error_data.line,
                column=error_data.column
            )
            await self.store_console_log(project_id, user_id, console_log)
            
            # Also store in dedicated error list for quick access
            error_key = f"errors:{project_id}"
            error_entry = {
                "id": str(uuid4()),
                "user_id": str(user_id),
                "project_id": str(project_id),
                "timestamp": datetime.utcnow().isoformat(),
                "message": error_data.message,
                "stack": error_data.stack,
                "type": error_data.type,
                "filename": error_data.filename,
                "line": error_data.line,
                "column": error_data.column,
                "is_unhandled": error_data.is_unhandled
            }
            
            await redis_client.lpush(error_key, error_entry)
            await redis_client.ltrim(error_key, 0, 99)  # Keep last 100 errors
            await redis_client.expire(error_key, self.console_ttl)
            
            # Publish error event
            await message_bus.publish(
                f"errors:{project_id}",
                Message(
                    type=MessageType.ERROR_EVENT,
                    sender="console_service",
                    payload=error_entry,
                    project_id=project_id
                )
            )
            
            logger.debug(f"Stored error log for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to store error log: {e}")
    
    async def get_recent_logs(
        self,
        project_id: UUID,
        count: int = 100,
        level_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent console logs for a project.
        
        Args:
            project_id: Project ID
            count: Number of logs to retrieve
            level_filter: Optional filter by log level
            
        Returns:
            List of log entries
        """
        try:
            key = f"console:{project_id}"
            
            # Get all logs (up to max)
            logs = await redis_client.lrange(key, 0, self.max_logs_per_project - 1)
            
            # Parse logs
            parsed_logs = []
            for log in logs:
                try:
                    if isinstance(log, str):
                        parsed_log = json.loads(log)
                    else:
                        parsed_log = log
                    
                    # Apply level filter if specified
                    if level_filter and parsed_log.get("level") != level_filter:
                        continue
                    
                    parsed_logs.append(parsed_log)
                    
                    # Stop if we have enough
                    if len(parsed_logs) >= count:
                        break
                        
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse log entry: {log}")
            
            return parsed_logs
            
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    async def get_recent_errors(
        self,
        project_id: UUID,
        count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent error logs for a project.
        
        Args:
            project_id: Project ID
            count: Number of errors to retrieve
            
        Returns:
            List of error entries
        """
        try:
            key = f"errors:{project_id}"
            
            # Get errors
            errors = await redis_client.lrange(key, 0, count - 1)
            
            # Parse errors
            parsed_errors = []
            for error in errors:
                try:
                    if isinstance(error, str):
                        parsed_errors.append(json.loads(error))
                    else:
                        parsed_errors.append(error)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse error entry: {error}")
            
            return parsed_errors
            
        except Exception as e:
            logger.error(f"Failed to get recent errors: {e}")
            return []
    
    async def get_console_stats(
        self,
        project_id: UUID
    ) -> Dict[str, int]:
        """
        Get console statistics for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dictionary with log counts by level
        """
        try:
            stats_key = f"console:stats:{project_id}"
            stats = await redis_client.hgetall(stats_key)
            
            # Convert string values to integers
            return {
                level: int(count) 
                for level, count in stats.items()
            }
            
        except Exception as e:
            logger.error(f"Failed to get console stats: {e}")
            return {}
    
    async def clear_logs(
        self,
        project_id: UUID
    ) -> bool:
        """
        Clear all logs for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if successful
        """
        try:
            # Delete console logs
            console_key = f"console:{project_id}"
            await redis_client.delete(console_key)
            
            # Delete error logs
            error_key = f"errors:{project_id}"
            await redis_client.delete(error_key)
            
            # Delete stats
            stats_key = f"console:stats:{project_id}"
            await redis_client.delete(stats_key)
            
            logger.info(f"Cleared all logs for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear logs: {e}")
            return False
    
    async def get_console_context_for_ai(
        self,
        project_id: UUID
    ) -> Dict[str, Any]:
        """
        Get console context formatted for AI analysis.
        
        Args:
            project_id: Project ID
            
        Returns:
            Console context for AI agents
        """
        try:
            # Get recent logs and errors
            logs = await self.get_recent_logs(project_id, count=50)
            errors = await self.get_recent_errors(project_id, count=10)
            warnings = await self.get_recent_logs(project_id, count=10, level_filter="warn")
            stats = await self.get_console_stats(project_id)
            
            # Analyze patterns
            error_types = {}
            for error in errors:
                error_type = error.get("type", "Unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            return {
                "recent_errors": errors,
                "recent_warnings": warnings,
                "recent_logs": logs[-20:],  # Last 20 logs
                "statistics": stats,
                "error_count": len(errors),
                "has_errors": len(errors) > 0,
                "error_types": error_types,
                "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get console context for AI: {e}")
            return {
                "recent_errors": [],
                "recent_warnings": [],
                "recent_logs": [],
                "statistics": {},
                "error_count": 0,
                "has_errors": False
            }
    
    async def _update_console_stats(
        self,
        project_id: UUID,
        level: str
    ) -> None:
        """Update console statistics."""
        try:
            stats_key = f"console:stats:{project_id}"
            await redis_client.hincrby(stats_key, level, 1)
            await redis_client.expire(stats_key, self.console_ttl)
        except Exception as e:
            logger.error(f"Failed to update console stats: {e}")


# Global console service instance
console_service = ConsoleService() 