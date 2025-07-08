"""
Pytest configuration and fixtures for backend tests.

Provides common test fixtures for database sessions, authenticated clients,
and test data generation.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from fastapi import FastAPI

from src.backend.core.database import Base
from src.backend.core.config import settings
from src.backend.main import app
from src.backend.core.auth import create_access_token, get_password_hash
from src.backend.models.user import User
from src.backend.models.project import Project
from src.backend.models.agent import Agent, AgentType
from src.backend.core.redis_client import redis_client
from src.backend.config.logging_config import setup_logging

# Setup test logging
setup_logging(
    app_name="test",
    log_level="DEBUG",
    environment="test"
)

# Override settings for testing
settings.database_url = settings.database_url.replace("/zeblit", "/zeblit_test")
settings.redis_url = "redis://localhost:6379/1"  # Use Redis DB 1 for tests

# Create test database engine
test_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,  # Disable connection pooling for tests
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override."""
    # Override the get_db dependency
    from src.backend.core.database import get_db
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Clear Redis before each test
    await redis_client.flushdb()
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True,
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin test user."""
    user = User(
        email="admin@example.com",
        username="adminuser",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_verified=True,
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    access_token = create_access_token(
        subject=str(test_user.id),
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict:
    """Create authentication headers for admin user."""
    access_token = create_access_token(
        subject=str(admin_user.id),
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, auth_headers: dict) -> AsyncClient:
    """Create an authenticated test client."""
    client.headers.update(auth_headers)
    return client


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient, admin_headers: dict) -> AsyncClient:
    """Create an authenticated admin test client."""
    client.headers.update(admin_headers)
    return client


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        name="Test Project",
        description="A test project for unit tests",
        user_id=test_user.id,
        template="blank",
        settings={
            "language": "python",
            "framework": "fastapi"
        },
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_agents(db_session: AsyncSession) -> list[Agent]:
    """Create test agents of each type."""
    agents = []
    
    for agent_type in AgentType:
        agent = Agent(
            type=agent_type,
            name=f"{agent_type.value.replace('_', ' ').title()} Agent",
            description=f"Test {agent_type.value} agent",
            model="claude-3-sonnet-20240229",
            is_active=True,
            capabilities={
                "languages": ["python", "javascript"],
                "frameworks": ["fastapi", "react"],
            },
        )
        db_session.add(agent)
        agents.append(agent)
    
    await db_session.commit()
    for agent in agents:
        await db_session.refresh(agent)
    
    return agents


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_user_data(email: str = None) -> dict:
        """Create user registration data."""
        timestamp = datetime.now().timestamp()
        return {
            "email": email or f"user{timestamp}@example.com",
            "username": f"user{timestamp}",
            "password": "testpassword123",
            "full_name": "Test User",
        }
    
    @staticmethod
    def create_project_data(name: str = None) -> dict:
        """Create project data."""
        timestamp = datetime.now().timestamp()
        return {
            "name": name or f"Project {timestamp}",
            "description": "Test project description",
            "template": "blank",
            "is_public": False,
            "settings": {
                "language": "python",
                "framework": "fastapi",
            },
        }
    
    @staticmethod
    def create_task_data(project_id: str, agent_id: str) -> dict:
        """Create task data."""
        return {
            "project_id": project_id,
            "agent_id": agent_id,
            "type": "code_generation",
            "description": "Generate a test function",
            "input_data": {
                "requirements": "Create a function that adds two numbers",
                "language": "python",
            },
        }


@pytest.fixture
def test_factory() -> TestDataFactory:
    """Provide test data factory."""
    return TestDataFactory()


# Markers for different test types
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    ) 