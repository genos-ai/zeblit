"""
Dependency injection functions for the AI Development Platform.

This module provides reusable dependencies for FastAPI routes,
including database sessions, authentication, and pagination.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2024-01-XX): Implement proper JWT authentication dependencies.
- 1.0.0 (2024-01-XX): Initial dependencies module creation.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Query, Request, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from modules.backend.core.database import AsyncSessionLocal
from modules.backend.core.exceptions import AuthenticationError
from modules.backend.core.config import settings
from modules.backend.models.user import User
from modules.backend.repositories.user import UserRepository
from modules.backend.schemas.auth import TokenData


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
# Optional bearer scheme for optional authentication
optional_oauth2_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session that auto-closes after use
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


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


async def get_current_user_optional(
    credentials = Depends(optional_oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.
    
    Args:
        credentials: Bearer token credentials from request
        db: Database session
        
    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if not credentials:
        return None
        
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get(user_id)
        return user
        
    except JWTError:
        return None
    except Exception:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user.
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        User: Current user object
        
    Raises:
        HTTPException: If user is not authenticated
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from auth
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user.
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_user_from_api_key(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from API key authentication.
    
    Args:
        authorization: Authorization header with API key
        db: Database session
        
    Returns:
        User object if API key is valid, None otherwise
    """
    if not authorization:
        return None
    
    # Check for API key format: "Bearer api_key" or "Api-Key api_key"
    if authorization.startswith("Bearer "):
        api_key = authorization[7:]  # Remove "Bearer "
    elif authorization.startswith("Api-Key "):
        api_key = authorization[8:]  # Remove "Api-Key "
    else:
        return None
    
    # Validate API key format (should start with "zbl_")
    if not api_key.startswith("zbl_"):
        return None
    
    try:
        # Import here to avoid circular imports
        from modules.backend.services.api_key import get_api_key_service
        
        api_key_service = get_api_key_service(db)
        user = await api_key_service.validate_api_key(api_key)
        
        return user
        
    except Exception:
        return None


async def get_current_user_multi_auth(
    # Try JWT first
    jwt_user: Optional[User] = Depends(get_current_user_optional),
    # Then try API key
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key),
) -> User:
    """
    Get current user from either JWT token or API key.
    
    This dependency supports both authentication methods:
    - JWT tokens (for web clients)
    - API keys (for CLI, Telegram, mobile clients)
    
    Args:
        jwt_user: User from JWT authentication
        api_key_user: User from API key authentication
        
    Returns:
        User object
        
    Raises:
        HTTPException: If no valid authentication is provided
    """
    user = jwt_user or api_key_user
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user 