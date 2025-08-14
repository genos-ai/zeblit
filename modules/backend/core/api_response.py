"""
Unified API response format for all endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial unified API response format.
"""

import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field
from fastapi import status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class APIMetadata(BaseModel):
    """Metadata for API responses."""
    
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    version: str = Field(default="1.0")
    processing_time_ms: Optional[float] = None


class APIResponse(BaseModel):
    """Unified API response format."""
    
    success: bool = Field(description="Whether the request was successful")
    data: Optional[Union[Dict[str, Any], List[Any], str, int, float, bool]] = Field(
        default=None, 
        description="Response data"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Error information if request failed"
    )
    metadata: APIMetadata = Field(
        default_factory=APIMetadata,
        description="Request metadata"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APIError(BaseModel):
    """Standardized error format."""
    
    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    field_errors: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Field-specific validation errors"
    )


def create_success_response(
    data: Any = None,
    request_id: Optional[str] = None,
    processing_time_ms: Optional[float] = None
) -> APIResponse:
    """
    Create a successful API response.
    
    Args:
        data: Response data
        request_id: Optional request ID
        processing_time_ms: Optional processing time
        
    Returns:
        Standardized success response
    """
    metadata = APIMetadata()
    if request_id:
        metadata.request_id = request_id
    if processing_time_ms is not None:
        metadata.processing_time_ms = processing_time_ms
    
    return APIResponse(
        success=True,
        data=data,
        metadata=metadata
    )


def create_error_response(
    error_code: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None,
    field_errors: Optional[Dict[str, List[str]]] = None,
    request_id: Optional[str] = None,
    processing_time_ms: Optional[float] = None
) -> APIResponse:
    """
    Create an error API response.
    
    Args:
        error_code: Error code
        error_message: Error message
        details: Additional error details
        field_errors: Field validation errors
        request_id: Optional request ID
        processing_time_ms: Optional processing time
        
    Returns:
        Standardized error response
    """
    metadata = APIMetadata()
    if request_id:
        metadata.request_id = request_id
    if processing_time_ms is not None:
        metadata.processing_time_ms = processing_time_ms
    
    error = APIError(
        code=error_code,
        message=error_message,
        details=details,
        field_errors=field_errors
    )
    
    return APIResponse(
        success=False,
        error=error.dict(),
        metadata=metadata
    )


def create_json_response(
    response: APIResponse,
    status_code: int = status.HTTP_200_OK,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a FastAPI JSONResponse with unified format.
    
    Args:
        response: API response object
        status_code: HTTP status code
        headers: Optional headers
        
    Returns:
        FastAPI JSONResponse
    """
    return JSONResponse(
        content=response.dict(),
        status_code=status_code,
        headers=headers
    )


def success_response(
    data: Any = None,
    status_code: int = status.HTTP_200_OK,
    request_id: Optional[str] = None,
    processing_time_ms: Optional[float] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Convenience function for successful responses.
    
    Args:
        data: Response data
        status_code: HTTP status code
        request_id: Optional request ID
        processing_time_ms: Optional processing time
        headers: Optional headers
        
    Returns:
        FastAPI JSONResponse with success format
    """
    response = create_success_response(
        data=data,
        request_id=request_id,
        processing_time_ms=processing_time_ms
    )
    return create_json_response(response, status_code, headers)


def error_response(
    error_code: str,
    error_message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None,
    field_errors: Optional[Dict[str, List[str]]] = None,
    request_id: Optional[str] = None,
    processing_time_ms: Optional[float] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Convenience function for error responses.
    
    Args:
        error_code: Error code
        error_message: Error message
        status_code: HTTP status code
        details: Additional error details
        field_errors: Field validation errors
        request_id: Optional request ID
        processing_time_ms: Optional processing time
        headers: Optional headers
        
    Returns:
        FastAPI JSONResponse with error format
    """
    response = create_error_response(
        error_code=error_code,
        error_message=error_message,
        details=details,
        field_errors=field_errors,
        request_id=request_id,
        processing_time_ms=processing_time_ms
    )
    return create_json_response(response, status_code, headers)


# Common error codes
class ErrorCodes:
    """Standard error codes for the API."""
    
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    API_KEY_INVALID = "API_KEY_INVALID"
    API_KEY_EXPIRED = "API_KEY_EXPIRED"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Business logic errors
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"


# HTTP status code mappings
STATUS_CODE_MAP = {
    ErrorCodes.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCodes.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCodes.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCodes.API_KEY_INVALID: status.HTTP_401_UNAUTHORIZED,
    ErrorCodes.API_KEY_EXPIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCodes.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCodes.MISSING_FIELD: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCodes.INVALID_FORMAT: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ErrorCodes.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCodes.ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCodes.CONFLICT: status.HTTP_409_CONFLICT,
    ErrorCodes.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCodes.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCodes.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCodes.INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
    ErrorCodes.RESOURCE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCodes.OPERATION_NOT_ALLOWED: status.HTTP_400_BAD_REQUEST,
}


def get_status_code_for_error(error_code: str) -> int:
    """Get appropriate HTTP status code for an error code."""
    return STATUS_CODE_MAP.get(error_code, status.HTTP_400_BAD_REQUEST)
