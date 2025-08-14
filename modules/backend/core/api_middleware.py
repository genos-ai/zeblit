"""
API middleware for request/response processing.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial API middleware implementation.
"""

import time
import logging
from typing import Callable, Dict, Any
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from modules.backend.core.api_response import (
    create_error_response,
    create_json_response,
    ErrorCodes
)

logger = logging.getLogger(__name__)


class APIResponseMiddleware(BaseHTTPMiddleware):
    """Middleware to standardize API responses and add request tracking."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and standardize response format.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Standardized response
        """
        # Generate request ID
        request_id = str(uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time-MS"] = str(round(processing_time_ms, 2))
            
            # For API endpoints, ensure unified format
            if (
                request.url.path.startswith("/api/") and 
                isinstance(response, JSONResponse) and
                response.status_code < 400
            ):
                # Add metadata to successful responses if not already present
                content = response.body.decode() if response.body else "{}"
                try:
                    import json
                    data = json.loads(content)
                    
                    # If response doesn't follow our standard format, wrap it
                    if not isinstance(data, dict) or "success" not in data:
                        from modules.backend.core.api_response import create_success_response
                        
                        standardized_response = create_success_response(
                            data=data,
                            request_id=request_id,
                            processing_time_ms=processing_time_ms
                        )
                        
                        response = JSONResponse(
                            content=standardized_response.dict(),
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                        
                except (json.JSONDecodeError, Exception):
                    # If we can't parse the response, leave it as is
                    pass
            
            return response
            
        except Exception as e:
            # Handle uncaught exceptions
            processing_time_ms = (time.time() - start_time) * 1000
            
            logger.error(f"Unhandled exception in request {request_id}: {e}", exc_info=True)
            
            # Create standardized error response
            error_response = create_error_response(
                error_code=ErrorCodes.INTERNAL_ERROR,
                error_message="An internal server error occurred",
                details={"exception": str(e)} if logger.isEnabledFor(logging.DEBUG) else None,
                request_id=request_id,
                processing_time_ms=processing_time_ms
            )
            
            return create_json_response(error_response, 500, {
                "X-Request-ID": request_id,
                "X-Processing-Time-MS": str(round(processing_time_ms, 2))
            })


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests and responses."""
    
    def __init__(self, app: ASGIApp, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Response from next middleware/endpoint
        """
        # Get request ID from state (set by APIResponseMiddleware)
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request
        if self.log_requests:
            logger.info(
                f"API Request: {request.method} {request.url.path} "
                f"[{request_id}] from {request.client.host if request.client else 'unknown'}"
            )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        # Log response
        if self.log_responses or response.status_code >= 400:
            level = logging.ERROR if response.status_code >= 400 else logging.INFO
            logger.log(
                level,
                f"API Response: {request.method} {request.url.path} "
                f"[{request_id}] -> {response.status_code} "
                f"({processing_time*1000:.2f}ms)"
            )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(
        self, 
        app: ASGIApp, 
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # In-memory storage (in production, use Redis)
        self._request_counts: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting based on client IP.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Response or rate limit error
        """
        # Skip rate limiting for health checks and static files
        if (
            request.url.path in ["/health", "/api/v1/health"] or
            request.url.path.startswith("/static/") or
            request.url.path.startswith("/docs") or
            request.url.path.startswith("/redoc")
        ):
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limits
        if self._is_rate_limited(client_ip):
            request_id = getattr(request.state, "request_id", str(uuid4()))
            
            error_response = create_error_response(
                error_code=ErrorCodes.RATE_LIMITED,
                error_message="Rate limit exceeded. Please try again later.",
                details={
                    "limits": {
                        "per_minute": self.requests_per_minute,
                        "per_hour": self.requests_per_hour
                    }
                },
                request_id=request_id
            )
            
            return create_json_response(error_response, 429, {
                "X-Request-ID": request_id,
                "Retry-After": "60"
            })
        
        return await call_next(request)
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        import time
        from collections import defaultdict
        
        now = time.time()
        
        # Initialize client data if not exists
        if client_ip not in self._request_counts:
            self._request_counts[client_ip] = {
                "minute": defaultdict(int),
                "hour": defaultdict(int)
            }
        
        client_data = self._request_counts[client_ip]
        
        # Current minute and hour buckets
        current_minute = int(now // 60)
        current_hour = int(now // 3600)
        
        # Clean old data (keep last 2 minutes and 2 hours for safety)
        cutoff_minute = current_minute - 2
        cutoff_hour = current_hour - 2
        
        client_data["minute"] = {
            k: v for k, v in client_data["minute"].items() 
            if k > cutoff_minute
        }
        client_data["hour"] = {
            k: v for k, v in client_data["hour"].items() 
            if k > cutoff_hour
        }
        
        # Check limits
        minute_count = client_data["minute"][current_minute]
        hour_count = sum(client_data["hour"].values())
        
        if (minute_count >= self.requests_per_minute or 
            hour_count >= self.requests_per_hour):
            return True
        
        # Increment counters
        client_data["minute"][current_minute] += 1
        client_data["hour"][current_hour] += 1
        
        return False
