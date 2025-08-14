"""
User repository for authentication and user management.

Provides user-specific database operations including authentication,
role management, and user preferences.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from modules.backend.models import User
from modules.backend.models.enums import UserRole
from .base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for user-related database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize user repository."""
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by(email=email.lower())
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: User's username
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by(username=username.lower())
    
    async def create_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        full_name: str,
        role: UserRole = UserRole.USER,
        **kwargs
    ) -> User:
        """
        Create a new user.
        
        Args:
            email: User's email address
            username: User's username
            password_hash: Hashed password
            full_name: User's full name
            role: User role (defaults to USER)
            **kwargs: Additional user fields
            
        Returns:
            Created user instance
        """
        # Ensure email and username are lowercase
        email = email.lower()
        username = username.lower()
        
        # Create user
        user = await self.create(
            email=email,
            username=username,
            hashed_password=password_hash,
            full_name=full_name,
            role=role,
            **kwargs
        )
        
        logger.info(f"Created new user: {user.username} ({user.email})")
        return user
    
    async def authenticate(self, email: str) -> Optional[User]:
        """
        Get user for authentication (includes password hash).
        
        Args:
            email: User's email address
            
        Returns:
            User instance with password hash or None
        """
        user = await self.get_by_email(email)
        if user and user.is_active:
            return user
        return None
    
    async def update_last_login(self, user_id: UUID) -> Optional[User]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user instance
        """
        return await self.update(
            user_id,
            last_login=datetime.utcnow()
        )
    
    async def update_password(self, user_id: UUID, password_hash: str) -> Optional[User]:
        """
        Update user's password.
        
        Args:
            user_id: User's ID
            password_hash: New hashed password
            
        Returns:
            Updated user instance
        """
        user = await self.update(
            user_id,
            hashed_password=password_hash
        )
        
        if user:
            logger.info(f"Password updated for user: {user.username}")
        
        return user
    
    async def verify_email(self, user_id: UUID) -> Optional[User]:
        """
        Mark user's email as verified.
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user instance
        """
        return await self.update(
            user_id,
            email_verified=True
        )
    
    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[User]:
        """
        Get active users with optional search.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            search: Optional search term for name/email/username
            
        Returns:
            List of active users
        """
        query = select(User).where(User.is_active == True)
        
        # Add search if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_term),
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        
        # Apply ordering and pagination
        query = query.order_by(User.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_users_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get users by role.
        
        Args:
            role: User role to filter by
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of users with specified role
        """
        return await self.get_many(
            filters={"role": role, "is_active": True},
            skip=skip,
            limit=limit,
            order_by="created_at",
            order_desc=True
        )
    
    async def get_user_with_projects(self, user_id: UUID) -> Optional[User]:
        """
        Get user with their projects loaded.
        
        Args:
            user_id: User's ID
            
        Returns:
            User instance with projects loaded
        """
        return await self.get(
            user_id,
            load_relationships=["projects", "collaborated_projects"]
        )
    
    async def update_usage_stats(
        self,
        user_id: UUID,
        tokens_used: int = 0,
        cost_used: float = 0.0
    ) -> Optional[User]:
        """
        Update user's usage statistics.
        
        Args:
            user_id: User's ID
            tokens_used: Tokens to add to current month's usage
            cost_used: Cost to add to current month's usage
            
        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if not user:
            return None
        
        # Update usage stats
        current_tokens = user.current_month_tokens or 0
        current_cost = user.current_month_cost or 0.0
        
        return await self.update(
            user_id,
            current_month_tokens=current_tokens + tokens_used,
            current_month_cost=current_cost + cost_used
        )
    
    async def reset_monthly_usage(self) -> int:
        """
        Reset monthly usage for all users (called by scheduled job).
        
        Returns:
            Number of users updated
        """
        # This would typically be done with a bulk update query
        # For now, we'll use the ORM approach
        users = await self.get_many(limit=10000)  # Get all users
        
        count = 0
        for user in users:
            if user.current_month_tokens > 0:
                await self.update(user.id, current_month_tokens=0, current_month_cost=0.0)
                count += 1
        
        logger.info(f"Reset monthly usage for {count} users")
        return count
    
    async def search_users(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20,
        include_inactive: bool = False
    ) -> List[User]:
        """
        Search users by name, email, or username.
        
        Args:
            search_term: Text to search for
            skip: Number of records to skip
            limit: Maximum records to return
            include_inactive: Whether to include inactive users
            
        Returns:
            List of matching users
        """
        filters = {} if include_inactive else {"is_active": True}
        
        return await self.search(
            search_fields=["email", "username", "full_name"],
            search_term=search_term,
            filters=filters,
            skip=skip,
            limit=limit
        )
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics for admin dashboard.
        
        Returns:
            Dictionary with user statistics
        """
        # Total users
        total_users = await self.count()
        
        # Active users
        active_users = await self.count({"is_active": True})
        
        # Users by role
        query = select(
            User.role,
            func.count(User.id).label("count")
        ).group_by(User.role)
        
        result = await self.db.execute(query)
        role_distribution = {row.role.value: row.count for row in result}
        
        # Users registered in last 30 days
        thirty_days_ago = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        thirty_days_ago = thirty_days_ago.replace(day=1)  # Start of month
        
        new_users = await self.count({
            "created_at": (">=", thirty_days_ago)
        })
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_distribution,
            "new_users_this_month": new_users
        } 