"""
Frontend logging endpoint for receiving browser logs.

Version: 1.0.0
Author: Zeblit Team

## Changelog
- 1.0.0 (2024-01-08): Initial implementation with log storage
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.database import get_db
from modules.backend.config.logging_config import get_logger
from modules.backend.models.user import User
from modules.backend.core.dependencies import get_current_user_optional

logger = get_logger(__name__)
router = APIRouter()


class FrontendLogEntry(BaseModel):
    """Single log entry from frontend."""
    timestamp: str
    level: str
    message: str
    data: Optional[dict] = None
    error: Optional[dict] = None


class FrontendLogBatch(BaseModel):
    """Batch of logs from frontend."""
    logs: List[FrontendLogEntry]
    userAgent: str
    url: str
    timestamp: str


@router.post("/frontend-logs", status_code=status.HTTP_204_NO_CONTENT)
async def receive_frontend_logs(
    log_batch: FrontendLogBatch,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> None:
    """
    Receive and store frontend logs.
    
    This endpoint accepts logs from the frontend application and stores them
    in the logs/frontend directory for debugging and monitoring.
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs/frontend")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine log file based on date
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"app-{date_str}.log"
        error_log_file = log_dir / f"errors-{date_str}.log"
        
        # Process each log entry
        for log_entry in log_batch.logs:
            # Format log entry
            user_info = f"user_id={current_user.id}" if current_user else "anonymous"
            log_line = (
                f"[{log_entry.timestamp}] "
                f"[{log_entry.level}] "
                f"{log_entry.message} "
                f"[{user_info}] "
                f"[url={log_batch.url}] "
                f"[userAgent={log_batch.userAgent}]"
            )
            
            if log_entry.data:
                log_line += f" [data={json.dumps(log_entry.data)}]"
            
            if log_entry.error:
                log_line += f" [error={json.dumps(log_entry.error)}]"
            
            log_line += "\n"
            
            # Write to appropriate log file
            if log_entry.level in ["ERROR", "CRITICAL"]:
                with open(error_log_file, "a") as f:
                    f.write(log_line)
                    if log_entry.error and log_entry.error.get("stack"):
                        f.write(f"Stack trace:\n{log_entry.error['stack']}\n\n")
            
            # Write all logs to general log file
            with open(log_file, "a") as f:
                f.write(log_line)
        
        # Log that we received frontend logs
        logger.info(
            "Received frontend logs",
            log_count=len(log_batch.logs),
            user_id=current_user.id if current_user else None,
            url=log_batch.url
        )
        
    except Exception as e:
        logger.error(
            "Failed to process frontend logs",
            error=str(e),
            user_id=current_user.id if current_user else None
        )
        # Don't raise exception - we don't want frontend logging failures
        # to break the frontend application 