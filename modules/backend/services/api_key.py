"""
API Key service for multi-client authentication.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial API key service implementation.
"""

import logging
import secrets
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from modules.backend.core.config import settings
from modules.backend.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    ForbiddenError
)
from modules.backend.models.user import User
from modules.backend.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class APIKey:
    """API Key model for multi-client authentication."""
    
    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        name: str,
        key_hash: str,
        prefix: str,
        last_used: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True,
        created_at: datetime = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.key_hash = key_hash
        self.prefix = prefix
        self.last_used = last_used
        self.expires_at = expires_at
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}
    
    @property
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired


class APIKeyService:
    """Service for managing API keys for multi-client authentication."""
    
    def __init__(self, db: AsyncSession):
        """Initialize API key service."""
        self.db = db
        self.user_repo = UserRepository(db)
        # In-memory storage for API keys (in production, use Redis or database)
        self._api_keys: Dict[str, APIKey] = {}
    
    def generate_api_key(self) -> tuple[str, str]:
        """
        Generate a new API key.
        
        Returns:
            Tuple of (api_key, key_hash) where api_key is returned to user
            and key_hash is stored in database
        """
        # Generate random key
        random_bytes = secrets.token_bytes(32)
        
        # Create prefix (first 8 chars of hex)
        prefix = random_bytes.hex()[:8]
        
        # Create full key with prefix
        api_key = f"zbl_{prefix}_{random_bytes.hex()[8:]}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return api_key, key_hash
    
    async def create_api_key(
        self,
        user_id: UUID,
        name: str,
        expires_in_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            name: Descriptive name for the API key
            expires_in_days: Optional expiration in days
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
            if len(user_keys) >= settings.MAX_API_KEYS_PER_USER:
                raise ValidationError(f"Maximum API keys limit reached ({settings.MAX_API_KEYS_PER_USER})")
            
            # Generate API key
            api_key, key_hash = self.generate_api_key()
            prefix = api_key.split('_')[1]
            
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
                metadata=metadata or {}
            )
            
            # Store in memory (in production, store in database/Redis)
            self._api_keys[key_hash] = api_key_obj
            
            logger.info(f"Created API key '{name}' for user {user_id}")
            
            return api_key_obj, api_key
            
        except Exception as e:
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
            
            # Look up the API key
            api_key_obj = self._api_keys.get(key_hash)
            if not api_key_obj:
                return None
            
            # Check if key is valid
            if not api_key_obj.is_valid:
                return None
            
            # Update last used timestamp
            api_key_obj.last_used = datetime.utcnow()
            
            # Get and return user
            user = await self.user_repo.get(api_key_obj.user_id)
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return None
    
    async def revoke_api_key(self, user_id: UUID, api_key_id: UUID) -> bool:
        """
        Revoke an API key.
        
        Args:
            user_id: User ID (for authorization)
            api_key_id: API key ID to revoke
            
        Returns:
            True if revoked successfully
        """
        try:
            # Find the API key
            api_key_obj = None
            key_hash_to_remove = None
            
            for key_hash, key_obj in self._api_keys.items():
                if key_obj.id == api_key_id and key_obj.user_id == user_id:
                    api_key_obj = key_obj
                    key_hash_to_remove = key_hash
                    break
            
            if not api_key_obj:
                raise NotFoundError("API key not found")
            
            # Deactivate the key
            api_key_obj.is_active = False
            
            # Optionally remove from storage
            if key_hash_to_remove:
                del self._api_keys[key_hash_to_remove]
            
            logger.info(f"Revoked API key {api_key_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            raise
    
    async def list_user_api_keys(
        self, 
        user_id: UUID, 
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List API keys for a user.
        
        Args:
            user_id: User ID
            include_inactive: Whether to include inactive keys
            
        Returns:
            List of API key information (without the actual keys)
        """
        try:
            keys = []
            
            for api_key_obj in self._api_keys.values():
                if api_key_obj.user_id != user_id:
                    continue
                
                if not include_inactive and not api_key_obj.is_valid:
                    continue
                
                keys.append({
                    "id": str(api_key_obj.id),
                    "name": api_key_obj.name,
                    "prefix": api_key_obj.prefix,
                    "last_used": api_key_obj.last_used.isoformat() if api_key_obj.last_used else None,
                    "expires_at": api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
                    "is_active": api_key_obj.is_active,
                    "is_expired": api_key_obj.is_expired,
                    "created_at": api_key_obj.created_at.isoformat(),
                    "metadata": api_key_obj.metadata
                })
            
            # Sort by creation date (newest first)
            keys.sort(key=lambda x: x["created_at"], reverse=True)
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            raise
    
    async def get_api_key_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get API key usage statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics about API key usage
        """
        try:
            user_keys = [
                key for key in self._api_keys.values() 
                if key.user_id == user_id
            ]
            
            active_keys = [key for key in user_keys if key.is_valid]
            expired_keys = [key for key in user_keys if key.is_expired]
            recently_used = [
                key for key in user_keys 
                if key.last_used and key.last_used > datetime.utcnow() - timedelta(days=7)
            ]
            
            return {
                "total_keys": len(user_keys),
                "active_keys": len(active_keys),
                "expired_keys": len(expired_keys),
                "recently_used": len(recently_used),
                "max_allowed": settings.MAX_API_KEYS_PER_USER
            }
            
        except Exception as e:
            logger.error(f"Failed to get API key stats: {e}")
            raise
    
    async def cleanup_expired_keys(self) -> int:
        """
        Remove expired API keys from storage.
        
        Returns:
            Number of keys cleaned up
        """
        try:
            expired_hashes = []
            
            for key_hash, api_key_obj in self._api_keys.items():
                if api_key_obj.is_expired:
                    expired_hashes.append(key_hash)
            
            # Remove expired keys
            for key_hash in expired_hashes:
                del self._api_keys[key_hash]
            
            if expired_hashes:
                logger.info(f"Cleaned up {len(expired_hashes)} expired API keys")
            
            return len(expired_hashes)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0


# Global API key service instance
# Note: In production, this should be a singleton with proper dependency injection
api_key_service = None

def get_api_key_service(db: AsyncSession) -> APIKeyService:
    """Get or create API key service instance."""
    return APIKeyService(db)
