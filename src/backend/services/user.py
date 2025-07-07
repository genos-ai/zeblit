"""
User service for user management business logic.

Handles user profiles, preferences, usage tracking, and user-related operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.exceptions import NotFoundError, ValidationError, AuthorizationError, EmailAlreadyExistsError, UsernameAlreadyExistsError
from src.backend.models import User
from src.backend.models.enums import UserRole
from src.backend.repositories import UserRepository, ProjectRepository
from src.backend.schemas.user import UserCreate, UserUpdate, UserStats

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
    
    async def create_user(self, user_create: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_create: User creation data
            
        Returns:
            Created user
            
        Raises:
            EmailAlreadyExistsError: If email already exists
            UsernameAlreadyExistsError: If username already exists
        """
        # Check if email exists
        existing = await self.user_repo.get_by_email(user_create.email)
        if existing:
            raise EmailAlreadyExistsError()
        
        # Check if username exists
        existing = await self.user_repo.get_by_username(user_create.username)
        if existing:
            raise UsernameAlreadyExistsError()
        
        # Hash password
        from src.backend.services.auth import pwd_context
        hashed_password = pwd_context.hash(user_create.password)
        
        # Create user
        user_data = user_create.model_dump(exclude={"password"})
        user = await self.user_repo.create_user(
            email=user_data["email"],
            username=user_data["username"],
            password_hash=hashed_password,
            full_name=user_data.get("full_name"),
            role=user_data.get("role", UserRole.USER)
        )
        
        logger.info(f"Created new user: {user.email}")
        return user
    
    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User instance
            
        Raises:
            NotFoundError: If user not found
        """
        return await self.get_user(user_id)
    
    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> User:
        """
        Update user information.
        
        Args:
            user_id: User's ID
            user_update: Update data
            
        Returns:
            Updated user
            
        Raises:
            EmailAlreadyExistsError: If email already exists
            UsernameAlreadyExistsError: If username already exists
        """
        # Get current user
        user = await self.get_user(user_id)
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Check email uniqueness if updating
        if "email" in update_data and update_data["email"] != user.email:
            existing = await self.user_repo.get_by_email(update_data["email"])
            if existing:
                raise EmailAlreadyExistsError()
        
        # Check username uniqueness if updating
        if "username" in update_data and update_data["username"] != user.username:
            existing = await self.user_repo.get_by_username(update_data["username"])
            if existing:
                raise UsernameAlreadyExistsError()
        
        # Update user
        user = await self.user_repo.update(user_id, **update_data)
        
        logger.info(f"Updated user: {user.email}")
        return user
    
    async def update_password(self, user_id: UUID, new_password: str) -> User:
        """
        Update user's password.
        
        Args:
            user_id: User's ID
            new_password: New password (plain text)
            
        Returns:
            Updated user
        """
        from src.backend.services.auth import pwd_context
        hashed_password = pwd_context.hash(new_password)
        
        user = await self.user_repo.update_password(user_id, hashed_password)
        if not user:
            raise NotFoundError("User", user_id)
        
        logger.info(f"Password updated for user: {user.email}")
        return user
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        List users with optional filtering.
        
        Args:
            skip: Number to skip
            limit: Maximum to return
            is_active: Filter by active status
            
        Returns:
            List of users
        """
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        
        return await self.user_repo.get_multi(
            skip=skip,
            limit=limit,
            **filters
        )
    
    async def get_user_stats(self, user_id: UUID) -> UserStats:
        """
        Get user statistics.
        
        Args:
            user_id: User's ID
            
        Returns:
            User statistics
        """
        user = await self.get_user(user_id)
        
        # Get project counts
        owned_projects = await self.project_repo.count({"owner_id": user_id})
        
        # TODO: Get real task counts from task repository
        task_count = 0
        completed_tasks = 0
        
        # Calculate remaining tokens and cost
        tokens_remaining = max(0, user.monthly_token_limit - user.current_month_tokens)
        cost_remaining = max(0, user.monthly_cost_limit - user.current_month_cost)
        
        return UserStats(
            user_id=user_id,
            tokens_used_this_month=user.current_month_tokens,
            cost_this_month=user.current_month_cost,
            tokens_remaining=tokens_remaining,
            cost_remaining=cost_remaining,
            project_count=owned_projects,
            active_projects=owned_projects,  # TODO: Filter by active status
            task_count=task_count,
            completed_tasks=completed_tasks
        ) 