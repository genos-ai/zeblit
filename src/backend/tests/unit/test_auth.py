"""
Unit tests for authentication functionality.

Tests user registration, login, JWT token generation, and password hashing.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.backend.core.config import settings
from src.backend.models.user import User
from src.backend.services.auth import AuthService
from src.backend.repositories.user import UserRepository
from src.backend.schemas.auth import UserCreate


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_password_hash_creates_different_hashes(self):
        """Test that same password creates different hashes."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("wrongpassword", hashed) is False
    
    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token generation and validation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        subject = "user123"
        token = create_access_token(subject=subject)
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        assert payload["sub"] == subject
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry."""
        subject = "user123"
        expires_delta = timedelta(minutes=5)
        token = create_access_token(
            subject=subject,
            expires_delta=expires_delta
        )
        
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Check expiry is approximately 5 minutes
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        delta = exp_time - now
        
        assert 4 < delta.total_seconds() / 60 < 6
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        subject = "user123"
        token = create_refresh_token(subject=subject)
        
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"
        assert "exp" in payload
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        subject = "user123"
        token = create_access_token(subject=subject)
        
        payload = decode_token(token)
        
        assert payload["sub"] == subject
        assert payload["type"] == "access"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")
    
    def test_decode_expired_token(self):
        """Test decoding expired token."""
        subject = "user123"
        # Create token that expires immediately
        token = create_access_token(
            subject=subject,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(JWTError):
            decode_token(token)


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuthService:
    """Test authentication service."""
    
    async def test_register_user(self, db_session: AsyncSession, test_factory):
        """Test user registration."""
        auth_service = AuthService(db_session)
        user_data = test_factory.create_user_data()
        
        # Register user
        user, tokens = await auth_service.register(
            UserCreate(**user_data)
        )
        
        assert user.email == user_data["email"]
        assert user.username == user_data["username"]
        assert user.full_name == user_data["full_name"]
        assert user.is_active is True
        assert user.is_verified is False
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
    
    async def test_register_duplicate_email(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_factory
    ):
        """Test registration with duplicate email."""
        auth_service = AuthService(db_session)
        user_data = test_factory.create_user_data(email=test_user.email)
        
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register(UserCreate(**user_data))
    
    async def test_register_duplicate_username(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_factory
    ):
        """Test registration with duplicate username."""
        auth_service = AuthService(db_session)
        user_data = test_factory.create_user_data()
        user_data["username"] = test_user.username
        
        with pytest.raises(ValueError, match="Username already taken"):
            await auth_service.register(UserCreate(**user_data))
    
    async def test_authenticate_valid_credentials(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test authentication with valid credentials."""
        auth_service = AuthService(db_session)
        
        # Authenticate with email
        authenticated = await auth_service.authenticate(
            email=test_user.email,
            password="testpassword123"
        )
        
        assert authenticated is not None
        assert authenticated.id == test_user.id
        assert authenticated.email == test_user.email
    
    async def test_authenticate_invalid_password(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test authentication with invalid password."""
        auth_service = AuthService(db_session)
        
        authenticated = await auth_service.authenticate(
            email=test_user.email,
            password="wrongpassword"
        )
        
        assert authenticated is None
    
    async def test_authenticate_nonexistent_user(
        self,
        db_session: AsyncSession
    ):
        """Test authentication with non-existent user."""
        auth_service = AuthService(db_session)
        
        authenticated = await auth_service.authenticate(
            email="nonexistent@example.com",
            password="anypassword"
        )
        
        assert authenticated is None
    
    async def test_authenticate_inactive_user(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test authentication with inactive user."""
        # Make user inactive
        test_user.is_active = False
        await db_session.commit()
        
        auth_service = AuthService(db_session)
        authenticated = await auth_service.authenticate(
            email=test_user.email,
            password="testpassword123"
        )
        
        assert authenticated is None
    
    async def test_verify_email_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test email verification token."""
        auth_service = AuthService(db_session)
        
        # Generate verification token
        token = auth_service.create_email_verification_token(test_user.email)
        
        # Verify token
        verified_user = await auth_service.verify_email(token)
        
        assert verified_user is not None
        assert verified_user.id == test_user.id
        assert verified_user.is_verified is True
    
    async def test_verify_invalid_email_token(
        self,
        db_session: AsyncSession
    ):
        """Test invalid email verification token."""
        auth_service = AuthService(db_session)
        
        with pytest.raises(ValueError):
            await auth_service.verify_email("invalid.token.here")
    
    async def test_refresh_tokens(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test token refresh."""
        auth_service = AuthService(db_session)
        
        # Create refresh token
        refresh_token = create_refresh_token(subject=str(test_user.id))
        
        # Refresh tokens
        new_tokens = await auth_service.refresh_tokens(refresh_token)
        
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"
        
        # Verify new access token works
        payload = decode_token(new_tokens["access_token"])
        assert payload["sub"] == str(test_user.id)


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    async def test_register_endpoint(
        self,
        client: AsyncClient,
        test_factory
    ):
        """Test user registration endpoint."""
        user_data = test_factory.create_user_data()
        
        response = await client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data
    
    async def test_login_endpoint(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test login endpoint."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"
    
    async def test_me_endpoint(
        self,
        auth_client: AsyncClient,
        test_user: User
    ):
        """Test get current user endpoint."""
        response = await auth_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    async def test_me_endpoint_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test get current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_refresh_endpoint(
        self,
        client: AsyncClient,
        test_user: User
    ):
        """Test token refresh endpoint."""
        # First login to get refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer" 