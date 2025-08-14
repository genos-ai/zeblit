"""
Authentication manager for Zeblit CLI.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial authentication manager.
"""

import logging
from typing import Optional, Dict, Any
import asyncio

from zeblit_cli.config.settings import get_settings, set_api_key, clear_auth

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication for the CLI."""
    
    def __init__(self):
        """Initialize auth manager."""
        self._api_client = None  # Will be set by dependency injection
    
    def set_api_client(self, api_client):
        """Set the API client (dependency injection)."""
        self._api_client = api_client
    
    async def get_api_key(self) -> Optional[str]:
        """Get the current API key."""
        settings = get_settings()
        return settings.api_key
    
    async def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        api_key = await self.get_api_key()
        if not api_key:
            return False
        
        # Validate key with backend if API client is available
        if self._api_client:
            try:
                await self._api_client.validate_api_key(api_key)
                return True
            except Exception as e:
                logger.debug(f"API key validation failed: {e}")
                return False
        
        # If no API client, just check if key exists
        return True
    
    async def login_with_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Login with an API key.
        
        Args:
            api_key: The API key to use
            
        Returns:
            User information from validation
            
        Raises:
            Exception: If authentication fails
        """
        if not self._api_client:
            raise Exception("API client not configured")
        
        # Validate the API key
        try:
            result = await self._api_client.validate_api_key(api_key)
            
            # Save the API key
            set_api_key(api_key)
            
            logger.info("Successfully authenticated")
            return result
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise Exception(f"Invalid API key: {str(e)}")
    
    async def logout(self) -> None:
        """Logout and clear stored credentials."""
        clear_auth()
        logger.info("Logged out successfully")
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current user."""
        if not await self.is_authenticated():
            return None
        
        if not self._api_client:
            return None
        
        try:
            api_key = await self.get_api_key()
            result = await self._api_client.validate_api_key(api_key)
            return result.get("user", {})
        except Exception as e:
            logger.debug(f"Failed to get user info: {e}")
            return None
    
    async def require_auth(self) -> str:
        """
        Ensure user is authenticated, raise exception if not.
        
        Returns:
            API key
            
        Raises:
            Exception: If not authenticated
        """
        if not await self.is_authenticated():
            raise Exception(
                "Not authenticated. Please run 'zeblit auth login' first."
            )
        
        return await self.get_api_key()


# Global auth manager instance
_auth_manager = AuthManager()


def get_auth_manager() -> AuthManager:
    """Get the global auth manager instance."""
    return _auth_manager
