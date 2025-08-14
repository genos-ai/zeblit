"""
Authentication schemas.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial authentication schemas implementation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="User's full name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class Token(BaseModel):
    """Schema for authentication tokens."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenData(BaseModel):
    """Schema for token payload data."""
    
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role")
    exp: datetime = Field(..., description="Token expiration time")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newsecurepassword456"
            }
        }


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="Email address for password reset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token-from-email",
                "new_password": "newsecurepassword789"
            }
        } 