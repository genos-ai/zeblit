"""
Authentication service for user authentication and authorization.

Handles JWT token generation, password hashing, and authentication logic.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import AuthenticationError, AuthorizationError, ValidationError
from models import User
from models.enums import UserRole
from repositories import UserRepository

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication and authorization operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize auth service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    def create_access_token(
        self,
        user_id: UUID,
        email: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User's ID
            email: User's email
            role: User's role
            expires_delta: Optional expiration time
            
        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user_id: User's ID
            expires_delta: Optional expiration time
            
        Returns:
            JWT refresh token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise AuthenticationError("Invalid authentication token")
    
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = await self.user_repo.authenticate(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str,
        **kwargs
    ) -> User:
        """
        Register a new user.
        
        Args:
            email: User's email
            username: User's username
            password: Plain text password
            full_name: User's full name
            **kwargs: Additional user fields
            
        Returns:
            Created user
            
        Raises:
            ValidationError: If email or username already exists
        """
        # Check if email exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")
        
        # Check if username exists
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise ValidationError("Username already taken")
        
        # Validate password strength
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Create user
        password_hash = self.get_password_hash(password)
        user = await self.user_repo.create_user(
            email=email,
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            **kwargs
        )
        
        logger.info(f"Registered new user: {user.email}")
        return user
    
    async def login(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Login a user and generate tokens.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = await self.authenticate_user(email, password)
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        # Update last login
        await self.user_repo.update_last_login(user.id)
        
        # Generate tokens
        access_token = self.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        refresh_token = self.create_refresh_token(user_id=user.id)
        
        logger.info(f"User logged in: {user.email}")
        return user, access_token, refresh_token
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Tuple[User, str]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            Tuple of (user, new_access_token)
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = self.decode_token(refresh_token)
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        # Get user
        user_id = UUID(payload.get("sub"))
        user = await self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Generate new access token
        access_token = self.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        
        return user, access_token
    
    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.
        
        Args:
            token: JWT access token
            
        Returns:
            Current user
            
        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        payload = self.decode_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        
        # Get user
        user_id = UUID(payload.get("sub"))
        user = await self.user_repo.get(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        return user
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> User:
        """
        Change user's password.
        
        Args:
            user_id: User's ID
            current_password: Current password
            new_password: New password
            
        Returns:
            Updated user
            
        Raises:
            AuthenticationError: If current password is wrong
            ValidationError: If new password is invalid
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Update password
        new_password_hash = self.get_password_hash(new_password)
        user = await self.user_repo.update_password(user_id, new_password_hash)
        
        logger.info(f"Password changed for user: {user.email}")
        return user
    
    async def reset_password(
        self,
        email: str,
        reset_token: str,
        new_password: str
    ) -> User:
        """
        Reset user's password with a reset token.
        
        Args:
            email: User's email
            reset_token: Password reset token
            new_password: New password
            
        Returns:
            Updated user
            
        Raises:
            AuthenticationError: If token is invalid
            ValidationError: If new password is invalid
        """
        # Decode reset token
        try:
            payload = self.decode_token(reset_token)
            if payload.get("type") != "reset" or payload.get("email") != email:
                raise AuthenticationError("Invalid reset token")
        except AuthenticationError:
            raise AuthenticationError("Invalid or expired reset token")
        
        # Get user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise AuthenticationError("User not found")
        
        # Validate new password
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Update password
        new_password_hash = self.get_password_hash(new_password)
        user = await self.user_repo.update_password(user.id, new_password_hash)
        
        logger.info(f"Password reset for user: {user.email}")
        return user
    
    def create_password_reset_token(self, email: str) -> str:
        """
        Create a password reset token.
        
        Args:
            email: User's email
            
        Returns:
            Password reset token
        """
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
        to_encode = {
            "email": email,
            "exp": expire,
            "type": "reset"
        }
        
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        ) 