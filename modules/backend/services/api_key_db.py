"""
Database-backed API Key service for multi-client authentication.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Database-backed API key service implementation.
"""

import logging
import secrets
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, delete
from sqlalchemy.orm import selectinload

from modules.backend.core.config import settings
from modules.backend.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    ForbiddenError
)
from modules.backend.models.user import User
from modules.backend.models.api_key import APIKey
from modules.backend.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class APIKeyServiceDB:
    """Database-backed service for managing API keys for multi-client authentication."""
    
    def __init__(self, db: AsyncSession):
        """Initialize API key service."""
        self.db = db
        self.user_repo = UserRepository(db)
    
    def generate_api_key(self) -> Tuple[str, str]:
        """
        Generate a new API key and its hash.
        
        Returns:
            Tuple of (api_key, key_hash)
        """
        # Generate random prefix (8 chars)
        prefix = secrets.token_hex(4)
        
        # Generate main key (32 chars)
        main_key = secrets.token_hex(16)
        
        # Format: zbl_prefix_mainkey
        api_key = f"zbl_{prefix}_{main_key}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return api_key, key_hash
    
    async def create_api_key(
        self,
        user_id: UUID,
        name: str,
        expires_in_days: Optional[int] = None,
        client_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            name: Descriptive name for the key
            expires_in_days: Optional expiration in days
            client_type: Type of client (cli, telegram, web, etc.)
            metadata: Optional metadata (client type, etc.)
            
        Returns:
            Tuple of (APIKey object, actual_api_key_string)
        """
        try:
            # Verify user exists
            user = await self.user_repo.get(user_id)
            if not user:
                raise NotFoundError("User not found")
            
            # Check user's API key limit
            user_keys = await self.list_user_api_keys(user_id, include_inactive=False)
            max_keys = getattr(settings, 'MAX_API_KEYS_PER_USER', 10)
            if len(user_keys) >= max_keys:
                raise ValidationError(f"Maximum API keys limit reached ({max_keys})")
            
            # Generate API key
            api_key, key_hash = self.generate_api_key()
            prefix = api_key.split('_')[1]  # Extract prefix from zbl_prefix_mainkey
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create API key object
            api_key_obj = APIKey(
                id=uuid4(),
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                prefix=prefix,
                expires_at=expires_at,
                client_type=client_type,
                key_metadata=metadata or {}
            )
            
            # Save to database
            self.db.add(api_key_obj)
            await self.db.commit()
            await self.db.refresh(api_key_obj)
            
            logger.info(f"Created API key '{name}' for user {user_id}")
            
            return api_key_obj, api_key
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create API key: {e}")
            raise
    
    async def validate_api_key(self, api_key: str) -> Optional[User]:
        """
        Validate an API key and return the associated user.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            User object if valid, None otherwise
        """
        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find the API key in database
            stmt = select(APIKey).options(selectinload(APIKey.user)).where(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True
                )
            )
            result = await self.db.execute(stmt)
            api_key_obj = result.scalar_one_or_none()
            
            if not api_key_obj:
                return None
            
            # Check if expired
            if api_key_obj.is_expired:
                logger.warning(f"API key {api_key_obj.prefix} is expired")
                return None
            
            # Update last used timestamp
            await self.db.execute(
                update(APIKey)
                .where(APIKey.id == api_key_obj.id)
                .values(last_used=datetime.utcnow())
            )
            await self.db.commit()
            
            # Check if user is active
            user = api_key_obj.user
            if not user or not user.is_active:
                logger.warning(f"User for API key {api_key_obj.prefix} is inactive")
                return None
            
            logger.debug(f"API key {api_key_obj.prefix} validated for user {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return None
    
    async def list_user_api_keys(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all API keys for a user.
        
        Args:
            user_id: User ID
            include_inactive: Include inactive keys
            
        Returns:
            List of API key information (without the actual keys)
        """
        try:
            filters = [APIKey.user_id == user_id]
            if not include_inactive:
                filters.append(APIKey.is_active == True)
            
            stmt = select(APIKey).where(and_(*filters)).order_by(APIKey.created_at.desc())
            result = await self.db.execute(stmt)
            api_keys = result.scalars().all()
            
            # Convert to dictionary format
            keys = []
            for api_key_obj in api_keys:
                keys.append({
                    "id": str(api_key_obj.id),
                    "name": api_key_obj.name,
                    "prefix": api_key_obj.prefix,
                    "last_used": api_key_obj.last_used.isoformat() if api_key_obj.last_used else None,
                    "expires_at": api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
                    "is_active": api_key_obj.is_active,
                    "is_expired": api_key_obj.is_expired,
                    "created_at": api_key_obj.created_at.isoformat(),
                    "metadata": api_key_obj.metadata or {}
                })
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list API keys for user {user_id}: {e}")
            return []
    
    async def revoke_api_key(self, key_id: UUID, user_id: UUID) -> bool:
        """
        Revoke (deactivate) an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for security)
            
        Returns:
            True if revoked successfully
        """
        try:
            stmt = select(APIKey).where(
                and_(
                    APIKey.id == key_id,
                    APIKey.user_id == user_id
                )
            )
            result = await self.db.execute(stmt)
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                raise NotFoundError("API key not found")
            
            # Update to inactive
            await self.db.execute(
                update(APIKey)
                .where(APIKey.id == key_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            await self.db.commit()
            
            logger.info(f"Revoked API key {api_key.name} for user {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to revoke API key: {e}")
            return False
    
    async def delete_api_key(self, key_id: UUID, user_id: UUID) -> bool:
        """
        Permanently delete an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for security)
            
        Returns:
            True if deleted successfully
        """
        try:
            stmt = select(APIKey).where(
                and_(
                    APIKey.id == key_id,
                    APIKey.user_id == user_id
                )
            )
            result = await self.db.execute(stmt)
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                raise NotFoundError("API key not found")
            
            # Delete permanently
            await self.db.execute(
                delete(APIKey).where(APIKey.id == key_id)
            )
            await self.db.commit()
            
            logger.info(f"Deleted API key {api_key.name} for user {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete API key: {e}")
            return False
    
    async def get_api_key_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get API key statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get all keys
            stmt = select(APIKey).where(APIKey.user_id == user_id)
            result = await self.db.execute(stmt)
            all_keys = result.scalars().all()
            
            # Calculate stats
            total_keys = len(all_keys)
            active_keys = len([k for k in all_keys if k.is_active])
            expired_keys = len([k for k in all_keys if k.is_expired])
            
            # Last used
            last_used = None
            for key in all_keys:
                if key.last_used:
                    if not last_used or key.last_used > last_used:
                        last_used = key.last_used
            
            return {
                "total_keys": total_keys,
                "active_keys": active_keys,
                "expired_keys": expired_keys,
                "last_used": last_used.isoformat() if last_used else None,
                "max_allowed": getattr(settings, 'MAX_API_KEYS_PER_USER', 10)
            }
            
        except Exception as e:
            logger.error(f"Failed to get API key stats for user {user_id}: {e}")
            return {}


def get_api_key_service(db: AsyncSession) -> APIKeyServiceDB:
    """Get API key service instance."""
    return APIKeyServiceDB(db)
