"""
User service for user management business logic.

Handles user profiles, preferences, usage tracking, and user-related operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ValidationError, AuthorizationError
from models import User
from models.enums import UserRole
from repositories import UserRepository, ProjectRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize user service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.project_repo = ProjectRepository(db)
    
    async def get_user(self, user_id: UUID) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User instance
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user
    
    async def get_user_profile(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user profile with statistics.
        
        Args:
            user_id: User's ID
            
        Returns:
            User profile data
        """
        user = await self.get_user(user_id)
        
        # Get user's projects count
        owned_projects = await self.project_repo.count({"owner_id": user_id})
        collaborated_projects = await self.project_repo.get_collaborated_projects(user_id)
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "preferences": user.preferences,
            "statistics": {
                "owned_projects": owned_projects,
                "collaborated_projects": len(collaborated_projects),
                "tokens_used_this_month": user.tokens_used_this_month,
                "monthly_token_limit": user.monthly_token_limit,
                "api_calls_count": user.api_calls_count
            }
        }
    
    async def update_profile(
        self,
        user_id: UUID,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Update user profile.
        
        Args:
            user_id: User's ID
            full_name: New full name
            avatar_url: New avatar URL
            preferences: Updated preferences
            
        Returns:
            Updated user
        """
        updates = {}
        
        if full_name is not None:
            updates["full_name"] = full_name
        if avatar_url is not None:
            updates["avatar_url"] = avatar_url
        if preferences is not None:
            # Merge with existing preferences
            user = await self.get_user(user_id)
            current_prefs = user.preferences or {}
            current_prefs.update(preferences)
            updates["preferences"] = current_prefs
        
        user = await self.user_repo.update(user_id, **updates)
        if not user:
            raise NotFoundError("User", user_id)
        
        logger.info(f"Updated profile for user: {user.email}")
        return user
    
    async def update_email(
        self,
        user_id: UUID,
        new_email: str
    ) -> User:
        """
        Update user's email address.
        
        Args:
            user_id: User's ID
            new_email: New email address
            
        Returns:
            Updated user
            
        Raises:
            ValidationError: If email already exists
        """
        # Check if email is already taken
        existing = await self.user_repo.get_by_email(new_email)
        if existing and existing.id != user_id:
            raise ValidationError("Email already registered")
        
        # Update email and mark as unverified
        user = await self.user_repo.update(
            user_id,
            email=new_email.lower(),
            email_verified=False,
            email_verified_at=None
        )
        
        if not user:
            raise NotFoundError("User", user_id)
        
        logger.info(f"Updated email for user: {user.username}")
        return user
    
    async def verify_email(
        self,
        user_id: UUID,
        verification_token: str
    ) -> User:
        """
        Verify user's email address.
        
        Args:
            user_id: User's ID
            verification_token: Email verification token
            
        Returns:
            Updated user
            
        Raises:
            ValidationError: If token is invalid
        """
        # TODO: Implement token verification logic
        # For now, just mark as verified
        
        user = await self.user_repo.verify_email(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        logger.info(f"Email verified for user: {user.email}")
        return user
    
    async def search_users(
        self,
        search_term: str,
        current_user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """
        Search for users (for collaboration invites).
        
        Args:
            search_term: Search term
            current_user_id: Current user's ID (to exclude)
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of matching users
        """
        users = await self.user_repo.search_users(
            search_term=search_term,
            skip=skip,
            limit=limit,
            include_inactive=False
        )
        
        # Filter out current user
        return [u for u in users if u.id != current_user_id]
    
    async def get_user_usage(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user's current usage statistics.
        
        Args:
            user_id: User's ID
            
        Returns:
            Usage statistics
        """
        user = await self.get_user(user_id)
        
        return {
            "tokens": {
                "used_this_month": user.tokens_used_this_month,
                "monthly_limit": user.monthly_token_limit,
                "percentage_used": (
                    (user.tokens_used_this_month / user.monthly_token_limit * 100)
                    if user.monthly_token_limit > 0 else 0
                ),
                "remaining": max(0, user.monthly_token_limit - user.tokens_used_this_month)
            },
            "api_calls": {
                "total": user.api_calls_count,
                "today": 0  # TODO: Implement daily tracking
            },
            "cost_estimate": {
                "current_month_usd": user.tokens_used_this_month * 0.00002,  # Rough estimate
                "monthly_limit_usd": user.monthly_cost_limit_usd
            }
        }
    
    async def update_usage(
        self,
        user_id: UUID,
        tokens_used: int,
        api_calls: int = 1
    ) -> User:
        """
        Update user's usage statistics.
        
        Args:
            user_id: User's ID
            tokens_used: Number of tokens used
            api_calls: Number of API calls made
            
        Returns:
            Updated user
            
        Raises:
            ValidationError: If user exceeds limits
        """
        user = await self.get_user(user_id)
        
        # Check token limit
        new_token_usage = user.tokens_used_this_month + tokens_used
        if new_token_usage > user.monthly_token_limit:
            raise ValidationError("Monthly token limit exceeded")
        
        # Update usage
        user = await self.user_repo.update_usage_stats(
            user_id=user_id,
            tokens_used=tokens_used,
            api_calls=api_calls
        )
        
        return user
    
    async def activate_user(self, user_id: UUID) -> User:
        """
        Activate a user account.
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user
        """
        user = await self.user_repo.update(user_id, is_active=True)
        if not user:
            raise NotFoundError("User", user_id)
        
        logger.info(f"Activated user: {user.email}")
        return user
    
    async def deactivate_user(self, user_id: UUID) -> User:
        """
        Deactivate a user account.
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user
        """
        user = await self.user_repo.update(user_id, is_active=False)
        if not user:
            raise NotFoundError("User", user_id)
        
        logger.info(f"Deactivated user: {user.email}")
        return user
    
    async def update_user_role(
        self,
        user_id: UUID,
        new_role: UserRole,
        admin_user_id: UUID
    ) -> User:
        """
        Update user's role (admin only).
        
        Args:
            user_id: User's ID to update
            new_role: New role
            admin_user_id: Admin making the change
            
        Returns:
            Updated user
            
        Raises:
            AuthorizationError: If not admin
        """
        # Verify admin
        admin = await self.get_user(admin_user_id)
        if admin.role != UserRole.ADMIN:
            raise AuthorizationError("Only admins can change user roles")
        
        # Update role
        user = await self.user_repo.update(user_id, role=new_role)
        if not user:
            raise NotFoundError("User", user_id)
        
        logger.info(f"Role updated for user {user.email} to {new_role.value} by admin {admin.email}")
        return user
    
    async def get_admin_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get user statistics for admin dashboard.
        
        Returns:
            User statistics
        """
        return await self.user_repo.get_user_statistics()
    
    async def delete_user(
        self,
        user_id: UUID,
        requesting_user_id: UUID
    ) -> bool:
        """
        Delete a user account.
        
        Args:
            user_id: User to delete
            requesting_user_id: User requesting deletion
            
        Returns:
            True if deleted
            
        Raises:
            AuthorizationError: If not authorized
        """
        # Users can only delete their own account
        # Admins can delete any account
        if user_id != requesting_user_id:
            requesting_user = await self.get_user(requesting_user_id)
            if requesting_user.role != UserRole.ADMIN:
                raise AuthorizationError("Can only delete your own account")
        
        # TODO: Implement proper cleanup (projects, files, etc.)
        success = await self.user_repo.delete(user_id)
        
        if success:
            logger.info(f"Deleted user: {user_id}")
        
        return success 