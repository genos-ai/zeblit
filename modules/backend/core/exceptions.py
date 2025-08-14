"""
Custom exceptions for the AI Development Platform.

This module defines custom exception classes that provide consistent
error handling and response formatting across the application.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception class for all API exceptions."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_type = error_type


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_type="AuthenticationError",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(BaseAPIException):
    """Raised when user lacks permission for an action."""
    
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_type="AuthorizationError"
        )


class ForbiddenError(BaseAPIException):
    """Raised when an action is forbidden."""
    
    def __init__(self, detail: str = "Action forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_type="ForbiddenError"
        )


class NotFoundError(BaseAPIException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found",
            error_type="NotFoundError"
        )


class ValidationError(BaseAPIException):
    """Raised when request validation fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_type="ValidationError"
        )


class ConflictError(BaseAPIException):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_type="ConflictError"
        )


class EmailAlreadyExistsError(ConflictError):
    """Raised when attempting to use an email that already exists."""
    
    def __init__(self, email: Optional[str] = None):
        detail = f"Email '{email}' is already registered" if email else "Email is already registered"
        super().__init__(detail=detail)


class UsernameAlreadyExistsError(ConflictError):
    """Raised when attempting to use a username that already exists."""
    
    def __init__(self, username: Optional[str] = None):
        detail = f"Username '{username}' is already taken" if username else "Username is already taken"
        super().__init__(detail=detail)


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_type="RateLimitError"
        )


class ExternalServiceError(BaseAPIException):
    """Raised when an external service fails."""
    
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External service '{service}' error: {detail}",
            error_type="ExternalServiceError"
        )


class ContainerError(BaseAPIException):
    """Raised when container operations fail."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Container operation failed: {detail}",
            error_type="ContainerError"
        )


class AIAgentError(BaseAPIException):
    """Raised when AI agent operations fail."""
    
    def __init__(self, agent: str, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI agent '{agent}' error: {detail}",
            error_type="AIAgentError"
        )


class DatabaseError(BaseAPIException):
    """Raised when database operations fail."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {detail}",
            error_type="DatabaseError"
        )


class CostLimitError(BaseAPIException):
    """Raised when user exceeds cost limits."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
            error_type="CostLimitError"
        )


class ServiceError(BaseAPIException):
    """Raised when a service operation fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_type="ServiceError"
        )


# Aliases for consistency with imported code
ResourceNotFoundError = NotFoundError  # Alias for backwards compatibility
UnauthorizedError = AuthorizationError  # Alias for consistency 