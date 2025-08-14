"""
Application middleware for the AI Development Platform.

Includes request tracking, performance monitoring, and error handling.
"""

from datetime import datetime
from typing import Callable, Optional, Dict, Any
from uuid import UUID
import uuid
import time
import json

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from modules.backend.core.config import settings
from modules.backend.core.exceptions import BaseAPIException
from modules.backend.core.auth import decode_token
from modules.backend.config.logging_config import set_request_id, clear_request_id, get_logger

logger = get_logger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking requests with unique IDs and logging."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_id(request_id)
        
        # Start timing
        start_time = time.time()
        
        # Get user info if authenticated
        user_id = None
        try:
            if auth_header := request.headers.get("authorization"):
                token = auth_header.replace("Bearer ", "")
                payload = decode_token(token)
                user_id = payload.get("sub")
        except:
            pass  # Ignore auth errors in middleware
        
        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            user_id=user_id,
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the error
            logger.error(
                "request_failed",
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )
            
            # Return error response
            if isinstance(e, BaseAPIException):
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "detail": e.detail,
                        "error_type": e.error_type,
                        "request_id": request_id,
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "error_type": "InternalError",
                        "request_id": request_id,
                    }
                )
        finally:
            # Clear request context
            clear_request_id()


class CORSMiddleware:
    """CORS middleware with proper handling of preflight requests."""
    
    def __init__(
        self,
        app,
        allow_origins: list = None,
        allow_credentials: bool = True,
        allow_methods: list = None,
        allow_headers: list = None,
    ):
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        headers = dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode()
        
        if scope["method"] == "OPTIONS":
            # Handle preflight request
            response_headers = [
                (b"access-control-allow-origin", origin.encode()),
                (b"access-control-allow-credentials", b"true"),
                (b"access-control-allow-methods", ", ".join(self.allow_methods).encode()),
                (b"access-control-allow-headers", ", ".join(self.allow_headers).encode()),
                (b"access-control-max-age", b"600"),
            ]
            
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": response_headers,
            })
            await send({
                "type": "http.response.body",
                "body": b"",
            })
        else:
            # Handle actual request
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"access-control-allow-origin", origin.encode()))
                    headers.append((b"access-control-allow-credentials", b"true"))
                    headers.append((b"access-control-expose-headers", b"*"))
                    message["headers"] = headers
                await send(message)
            
            await self.app(scope, receive, send_wrapper)


async def performance_middleware(request: Request, call_next):
    """
    Middleware to monitor request performance.
    
    Logs slow requests and tracks performance metrics.
    """
    start_time = time.time()
    
    # Add request ID to context
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log performance data
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=round(duration, 3),
        request_id=request_id,
        slow_request=duration > 1.0  # Flag requests taking more than 1 second
    )
    
    # Add performance headers
    response.headers["X-Response-Time"] = f"{duration:.3f}"
    response.headers["X-Request-ID"] = request_id
    
    return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and exceptions."""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and handle any exceptions."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(
                "unhandled_exception",
                error=str(e),
                error_type=type(e).__name__,
                path=request.url.path,
                method=request.method,
                exc_info=True
            )
            
            # Return a generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_id": request.state.request_id if hasattr(request.state, "request_id") else None
                }
            )


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request performance."""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and monitor performance."""
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log slow requests
        if process_time > self.slow_request_threshold:
            logger.warning(
                "slow_request",
                path=request.url.path,
                method=request.method,
                process_time=process_time,
                threshold=self.slow_request_threshold,
                request_id=getattr(request.state, "request_id", None)
            )
        
        return response 