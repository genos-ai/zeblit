"""
Caching decorators and utilities.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial caching implementation.
"""

import json
import hashlib
import functools
import logging
from typing import Any, Optional, Callable, Union
from datetime import timedelta

from modules.backend.core.redis_client import redis_client
from modules.backend.core.config import settings

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        prefix: Cache key prefix
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a string representation of arguments
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, 'id'):  # Handle model instances
            key_parts.append(f"id:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):
            key_parts.append(f"{k}:id:{v.id}")
        else:
            key_parts.append(f"{k}:{v}")
    
    # Create hash for complex keys
    key_string = ":".join(key_parts)
    if len(key_string) > 200:  # Redis key length limit
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:hash:{key_hash}"
    
    return key_string


def cache(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """
    Cache decorator for async functions.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default from settings)
        key_builder: Custom key builder function
        
    Example:
        @cache("user", ttl=3600)
        async def get_user(user_id: UUID) -> User:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if Redis is not available
            if not redis_client._client:
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_builder:
                cache_key = key_builder(prefix, *args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            try:
                cached_value = await redis_client.get(cache_key)
                if cached_value:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    # Try to deserialize JSON
                    try:
                        return json.loads(cached_value)
                    except json.JSONDecodeError:
                        return cached_value
            except Exception as e:
                logger.warning(f"Cache get error: {e}")
            
            # Call the function
            result = await func(*args, **kwargs)
            
            # Cache the result
            try:
                # Determine TTL
                cache_ttl = ttl or settings.REDIS_CACHE_TTL_SECONDS
                
                # Serialize result if needed
                if isinstance(result, (dict, list)):
                    cache_value = json.dumps(result)
                elif hasattr(result, 'model_dump'):  # Pydantic models
                    cache_value = json.dumps(result.model_dump())
                else:
                    cache_value = str(result)
                
                await redis_client.set(cache_key, cache_value, ttl=cache_ttl)
                logger.debug(f"Cached result for key: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set error: {e}")
            
            return result
        
        # Add cache management methods
        wrapper.cache_clear = lambda: redis_client.delete(f"{prefix}:*")
        wrapper.cache_prefix = prefix
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> None:
    """
    Invalidate cache entries matching pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "user:*")
    """
    async def _invalidate():
        try:
            keys = await redis_client.keys(pattern)
            if keys:
                for key in keys:
                    await redis_client.delete(key)
                logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    # Run async invalidation
    import asyncio
    asyncio.create_task(_invalidate())


class CacheManager:
    """
    Cache manager for more complex caching scenarios.
    """
    
    def __init__(self, namespace: str):
        """Initialize cache manager with namespace."""
        self.namespace = namespace
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        full_key = f"{self.namespace}:{key}"
        value = await redis_client.get(full_key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        full_key = f"{self.namespace}:{key}"
        cache_ttl = ttl or settings.REDIS_CACHE_TTL_SECONDS
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif hasattr(value, 'model_dump'):
            value = json.dumps(value.model_dump())
        
        return await redis_client.set(full_key, value, ttl=cache_ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        full_key = f"{self.namespace}:{key}"
        return await redis_client.delete(full_key)
    
    async def clear(self) -> int:
        """Clear all cache entries in namespace."""
        pattern = f"{self.namespace}:*"
        keys = await redis_client.keys(pattern)
        count = 0
        for key in keys:
            if await redis_client.delete(key):
                count += 1
        return count
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        full_key = f"{self.namespace}:{key}"
        return await redis_client.exists(full_key)


# Specialized cache managers
user_cache = CacheManager("user")
project_cache = CacheManager("project")
agent_cache = CacheManager("agent") 