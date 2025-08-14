"""
Unit tests for database functionality.

Tests database connections, sessions, and basic operations.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from modules.backend.models.user import User
from modules.backend.models.project import Project
from modules.backend.core.database import Base


@pytest.mark.unit
@pytest.mark.asyncio
class TestDatabase:
    """Test database functionality."""
    
    async def test_database_connection(self, db_session: AsyncSession):
        """Test that we can connect to the database."""
        # Execute a simple query
        result = await db_session.execute(text("SELECT 1"))
        value = result.scalar()
        
        assert value == 1
    
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user in the database."""
        user = User(
            email="dbtest@example.com",
            username="dbtest",
            full_name="Database Test User",
            hashed_password="hashed",
            is_active=True,
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "dbtest@example.com"
        assert user.created_at is not None
    
    async def test_query_user(self, db_session: AsyncSession, test_user: User):
        """Test querying a user from the database."""
        # Query the user
        result = await db_session.execute(
            select(User).where(User.id == test_user.id)
        )
        found_user = result.scalar_one()
        
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
    
    async def test_relationships(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project
    ):
        """Test model relationships."""
        # Query project with user relationship
        result = await db_session.execute(
            select(Project)
            .where(Project.id == test_project.id)
            .options()  # Can add joinedload here if needed
        )
        project = result.scalar_one()
        
        assert project.user_id == test_user.id
    
    async def test_transaction_rollback(self, db_session: AsyncSession):
        """Test that transactions can be rolled back."""
        user = User(
            email="rollback@example.com",
            username="rollback",
            full_name="Rollback User",
            hashed_password="hashed",
        )
        
        db_session.add(user)
        await db_session.flush()
        
        # User should have an ID
        assert user.id is not None
        
        # Rollback the transaction
        await db_session.rollback()
        
        # Query should not find the user
        result = await db_session.execute(
            select(User).where(User.email == "rollback@example.com")
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is None 