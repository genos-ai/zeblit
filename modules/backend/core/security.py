"""
Security utilities and middleware.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2025-07-09): Added security headers and rate limiting
- 1.0.0 (2024-01-XX): Initial security utilities implementation.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import structlog

from modules.backend.core.config import settings

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT bearer scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Token payload data
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss: http://localhost:* https://api.zeblit.com; "
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HSTS (only in production)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    # API endpoints
    "/api/v1/auth/login": {"calls": 5, "period": 300},  # 5 calls per 5 minutes
    "/api/v1/auth/register": {"calls": 3, "period": 3600},  # 3 calls per hour
    "/api/v1/auth/forgot-password": {"calls": 3, "period": 3600},  # 3 calls per hour
    
    # General API rate limit
    "/api/v1": {"calls": 100, "period": 60},  # 100 calls per minute
    
    # WebSocket connections
    "/api/v1/ws": {"calls": 10, "period": 60},  # 10 connections per minute
}


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Returns dict with:
    - valid: bool
    - errors: list of error messages
    - score: password strength score (0-5)
    """
    errors = []
    score = 0
    
    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    else:
        score += 1
        if len(password) >= 12:
            score += 1
    
    # Character type checks
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_lower:
        errors.append("Password must contain lowercase letters")
    else:
        score += 1
    
    if not has_upper:
        errors.append("Password must contain uppercase letters")
    else:
        score += 1
    
    if not has_digit:
        errors.append("Password must contain numbers")
    else:
        score += 1
    
    if has_special:
        score += 1
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "score": min(score, 5)
    } 