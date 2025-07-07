"""
User endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial user endpoints implementation.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.dependencies import get_db, get_current_user
from src.backend.services.user import UserService
from src.backend.schemas.user import (
    UserResponse,
    UserUpdate,
    UserProfile,
    UserStats,
)
from src.backend.models.user import User
from src.backend.core.exceptions import (
    ResourceNotFoundError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    UnauthorizedError,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        UserResponse: Current user data.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update current user profile.
    
    Args:
        user_update: User update data.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        UserResponse: Updated user data.
        
    Raises:
        HTTPException: If email or username already exists.
    """
    user_service = UserService(db)
    
    try:
        # Update user
        updated_user = await user_service.update_user(
            user_id=current_user.id,
            user_update=user_update
        )
        
        return UserResponse.model_validate(updated_user)
        
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserStats:
    """
    Get current user usage statistics.
    
    Args:
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        UserStats: User usage statistics.
    """
    user_service = UserService(db)
    
    try:
        stats = await user_service.get_user_stats(current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete current user account.
    
    Args:
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        None: 204 No Content on success.
    """
    user_service = UserService(db)
    
    try:
        await user_service.delete_user(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


# Admin endpoints (require admin role)

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of users to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    """
    List all users (admin only).
    
    Args:
        skip: Number of users to skip.
        limit: Number of users to return.
        is_active: Filter by active status.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        List[UserResponse]: List of users.
        
    Raises:
        HTTPException: If user is not admin.
    """
    # Check admin permission
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_service = UserService(db)
    
    try:
        users = await user_service.list_users(
            skip=skip,
            limit=limit,
            is_active=is_active
        )
        
        return [UserResponse.model_validate(user) for user in users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Get user by ID (admin only or self).
    
    Args:
        user_id: User ID to retrieve.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        UserResponse: User data.
        
    Raises:
        HTTPException: If user not found or unauthorized.
    """
    # Check permission (admin or self)
    if current_user.id != user_id and current_user.role not in ["admin", "superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users"
        )
    
    user_service = UserService(db)
    
    try:
        user = await user_service.get_user_by_id(user_id)
        return UserResponse.model_validate(user)
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete user by ID (admin only).
    
    Args:
        user_id: User ID to delete.
        current_user: Current authenticated user.
        db: Database session.
        
    Returns:
        None: 204 No Content on success.
        
    Raises:
        HTTPException: If user not found or unauthorized.
    """
    # Check admin permission
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user_service = UserService(db)
    
    try:
        await user_service.delete_user(user_id)
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        ) 