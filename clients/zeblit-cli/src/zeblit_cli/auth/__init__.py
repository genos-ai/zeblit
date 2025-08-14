"""Authentication package for Zeblit CLI."""

from .manager import AuthManager, get_auth_manager

__all__ = ["AuthManager", "get_auth_manager"]
