"""
Authentication endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial authentication endpoints implementation.
"""

from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.config import settings
from modules.backend.core.dependencies import get_db, get_current_user
from modules.backend.services.auth import AuthService
from modules.backend.services.user import UserService
from modules.backend.schemas.auth import (
    Token,
    TokenData,
    UserRegister,
    UserLogin,
    RefreshTokenRequest,
    PasswordChangeRequest,
)
from modules.backend.schemas.user import UserCreate, UserResponse
from modules.backend.models.user import User
from modules.backend.core.exceptions import (
    AuthenticationError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    ResourceNotFoundError,
)

router = APIRouter(
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.
    
    Args:
        user_data: User registration data including email, username, and password.
        db: Database session.
        
    Returns:
        UserResponse: Created user data.
        
    Raises:
        HTTPException: If email or username already exists.
    """
    user_service = UserService(db)
    
    try:
        # Create user data object
        user_create = UserCreate(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password=user_data.password,
        )
        
        # Create user
        user = await user_service.create_user(user_create)
        
        return UserResponse.model_validate(user)
        
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Login user and return access token.
    
    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.
        
    Returns:
        Token: Access and refresh tokens.
        
    Raises:
        HTTPException: If authentication fails.
    """
    auth_service = AuthService(db)
    
    try:
        # Authenticate user (form_data.username is the email)
        tokens = await auth_service.authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
        
        return Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer"
        )
        
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token request data.
        db: Database session.
        
    Returns:
        Token: New access and refresh tokens.
        
    Raises:
        HTTPException: If refresh token is invalid.
    """
    auth_service = AuthService(db)
    
    try:
        # Refresh tokens
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)
        
        return Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """
    Logout user.
    
    Note: Since we're using JWT tokens, actual logout is handled client-side
    by removing the stored tokens. This endpoint is provided for completeness
    and could be extended to blacklist tokens if needed.
    
    Returns:
        None: 204 No Content on success.
    """
    # In a production system, you might want to:
    # 1. Blacklist the token in Redis
    # 2. Log the logout event
    # 3. Clear any server-side session data
    
    # For now, we just return success
    return None


@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Change user password.
    
    Args:
        password_data: Current and new password.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        dict: Success message.
        
    Raises:
        HTTPException: If current password is incorrect.
    """
    auth_service = AuthService(db)
    user_service = UserService(db)
    
    try:
        # Verify current password
        user = await user_service.get_user_by_id(current_user.id)
        if not auth_service.verify_password(password_data.current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Update password
        await user_service.update_password(user.id, password_data.new_password)
        
        return {"message": "Password changed successfully"}
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        ) 