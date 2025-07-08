"""
Redis client wrapper for caching, sessions, and pub/sub.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial Redis client implementation.
"""

import json
import logging
from typing import Any, Optional, Union, List, Dict
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from src.backend.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper with connection pooling."""
    
    def __init__(self):
        """Initialize Redis client with connection pool."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._pubsub_client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Establish Redis connection with pool."""
        try:
            # Create connection pool
            self._pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
            )
            
            # Create main client
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Create separate client for pub/sub
            self._pubsub_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
            )
            
            # Test connection
            await self._client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._pubsub_client:
            await self._pubsub_client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connection closed")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return self._client
    
    @property
    def pubsub(self) -> redis.Redis:
        """Get Redis pub/sub client instance."""
        if not self._pubsub_client:
            raise RuntimeError("Redis pubsub client not connected")
        return self._pubsub_client
    
    # Cache operations
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Union[str, int, float, dict, list],
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        try:
            # Convert complex types to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                return await self.client.setex(key, ttl, value)
            else:
                return await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(await self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        try:
            return await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False
    
    # List operations
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the head of a list."""
        try:
            # Convert complex types to JSON
            processed_values = []
            for v in values:
                if isinstance(v, (dict, list)):
                    processed_values.append(json.dumps(v))
                else:
                    processed_values.append(v)
            return await self.client.lpush(key, *processed_values)
        except Exception as e:
            logger.error(f"Redis lpush error for key {key}: {e}")
            return 0
    
    async def llen(self, key: str) -> int:
        """Get length of list."""
        try:
            return await self.client.llen(key)
        except Exception as e:
            logger.error(f"Redis llen error for key {key}: {e}")
            return 0
    
    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        """
        Trim list to specified range.
        
        Args:
            key: List key
            start: Start index (inclusive)
            stop: Stop index (inclusive)
            
        Returns:
            True if successful
        """
        try:
            return await self.client.ltrim(key, start, stop)
        except Exception as e:
            logger.error(f"Redis ltrim error for key {key}: {e}")
            return False
    
    async def lrange(self, key: str, start: int, stop: int) -> List[str]:
        """Get range of elements from list."""
        try:
            return await self.client.lrange(key, start, stop)
        except Exception as e:
            logger.error(f"Redis lrange error for key {key}: {e}")
            return []
    
    # Hash operations
    async def hset(self, name: str, key: str, value: Any) -> int:
        """Set hash field."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return await self.client.hset(name, key, value)
        except Exception as e:
            logger.error(f"Redis hset error for {name}:{key}: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        try:
            return await self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis hget error for {name}:{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all fields and values in a hash."""
        try:
            return await self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis hgetall error for {name}: {e}")
            return {}
    
    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        """
        Increment hash field by amount.
        
        Args:
            name: Hash name
            key: Field key
            amount: Amount to increment by (default 1)
            
        Returns:
            New value after increment
        """
        try:
            return await self.client.hincrby(name, key, amount)
        except Exception as e:
            logger.error(f"Redis hincrby error for {name}:{key}: {e}")
            return 0
    
    # Pub/Sub operations
    async def publish(self, channel: str, message: Union[str, dict]) -> int:
        """Publish message to channel."""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            return await self.pubsub.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis publish error for channel {channel}: {e}")
            return 0
    
    async def subscribe(self, *channels: str):
        """Subscribe to channels."""
        pubsub = self.pubsub.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
    
    # Pattern operations
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        try:
            return await self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []
    
    # Increment operations
    async def incr(self, key: str) -> int:
        """Increment key value."""
        try:
            return await self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return 0
    
    async def incrby(self, key: str, amount: int) -> int:
        """Increment key value by amount."""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis incrby error for key {key}: {e}")
            return 0


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Get Redis client dependency."""
    return redis_client 