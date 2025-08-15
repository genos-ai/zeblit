"""
Utilities for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial utilities package.
"""

from .progress import (
    progress_manager,
    with_progress,
    show_error,
    show_warning,
    show_success,
    show_info,
    FileTransferProgress
)
from .completion import (
    project_id_completion,
    agent_type_completion,
    file_path_completion,
    container_command_completion,
    template_completion,
    local_file_completion,
    setup_completion
)
from .cache import (
    CacheManager,
    api_cache,
    cached_api_call
)

__all__ = [
    "progress_manager",
    "with_progress", 
    "show_error",
    "show_warning",
    "show_success",
    "show_info",
    "FileTransferProgress",
    "project_id_completion",
    "agent_type_completion",
    "file_path_completion",
    "container_command_completion",
    "template_completion",
    "local_file_completion",
    "setup_completion",
    "CacheManager",
    "api_cache",
    "cached_api_call"
]
