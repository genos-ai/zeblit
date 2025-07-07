"""
Dependency injection functions for the AI Development Platform.

This module provides reusable dependencies for FastAPI routes,
including database sessions, authentication, and pagination.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.exceptions import AuthenticationError


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session that auto-closes after use
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Request ID for tracking
    """
    return getattr(request.state, "request_id", "unknown")


class PaginationParams:
    """Common pagination parameters."""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page


class SortingParams:
    """Common sorting parameters."""
    
    def __init__(
        self,
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
        sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order")
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order


class FilterParams:
    """Common filter parameters."""
    
    def __init__(
        self,
        search: Optional[str] = Query(None, description="Search term"),
        status: Optional[str] = Query(None, description="Filter by status"),
        created_after: Optional[str] = Query(None, description="Filter by creation date"),
        created_before: Optional[str] = Query(None, description="Filter by creation date")
    ):
        self.search = search
        self.status = status
        self.created_after = created_after
        self.created_before = created_before


# Placeholder for authentication dependencies
# These will be implemented when we build the auth system
async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise None.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[dict]: User data if authenticated
    """
    # TODO: Implement JWT token validation
    return None


async def get_current_user(request: Request) -> dict:
    """
    Get current authenticated user.
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: Current user data
        
    Raises:
        AuthenticationError: If user is not authenticated
    """
    user = await get_current_user_optional(request)
    if not user:
        raise AuthenticationError("Not authenticated")
    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user.
    
    Args:
        current_user: Current user from auth
        
    Returns:
        dict: Current active user data
        
    Raises:
        AuthenticationError: If user is not active
    """
    if not current_user.get("is_active", True):
        raise AuthenticationError("User account is inactive")
    return current_user


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current admin user.
    
    Args:
        current_user: Current user from auth
        
    Returns:
        dict: Current admin user data
        
    Raises:
        AuthenticationError: If user is not an admin
    """
    if current_user.get("role") != "admin":
        raise AuthenticationError("Admin access required")
    return current_user 