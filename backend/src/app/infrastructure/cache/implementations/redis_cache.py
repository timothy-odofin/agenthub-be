"""
Redis cache provider implementation.

Implements the BaseCacheProvider interface using Redis as the backend.
Uses the existing RedisConnectionManager for Redis connectivity.
"""

import json
from typing import Any, Dict, List, Optional, Set

from app.infrastructure.cache.base_cache_provider import BaseCacheProvider
from app.infrastructure.cache.cache_registry import CacheRegistry
from app.infrastructure.cache.error_handler import handle_cache_errors
from app.core.enums import CacheType, ConnectionType
from app.infrastructure.connections.factory.connection_factory import ConnectionFactory
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@CacheRegistry.register(CacheType.REDIS)
class RedisCacheProvider(BaseCacheProvider):
    """
    Redis-backed cache provider.
    
    Uses the existing RedisConnectionManager infrastructure for Redis connectivity.
    Provides high-performance, distributed caching with automatic TTL expiration.
    
    Features:
    - JSON serialization/deserialization
    - Secondary indexing via Redis sets
    - Automatic TTL management
    - Namespace isolation
    - Async/await support
    """
    
    def __init__(self, namespace: str, default_ttl: int = 900):
        """
        Initialize Redis cache provider.
        
        Args:
            namespace: Namespace prefix for all keys
            default_ttl: Default TTL in seconds (default: 15 minutes)
        """
        super().__init__(namespace, default_ttl)
        self._redis_manager = None
        logger.debug(f"RedisCacheProvider initialized with namespace '{namespace}'")
    
    @property
    def redis(self):
        """
        Lazy-load Redis connection manager.
        
        Returns:
            RedisConnectionManager instance
        """
        if self._redis_manager is None:
            self._redis_manager = ConnectionFactory.get_connection_manager(ConnectionType.REDIS)
            logger.debug(f"Connected to Redis for namespace '{self.namespace}'")
        return self._redis_manager
    
    @handle_cache_errors(operation="set", default_return=False, suppress_errors=True)
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        indexes: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Store a value in Redis with optional TTL and indexes.
        
        The value is automatically serialized to JSON. If the value is already
        a string, it's stored as-is.
        """
        redis_key = self._make_key(key)
        ttl_seconds = ttl or self.default_ttl
        
        # Serialize value to JSON if not already a string
        if isinstance(value, str):
            serialized_value = value
        else:
            serialized_value = json.dumps(value)
        
        # Store the value with TTL
        await self.redis.set(redis_key, serialized_value, ex=ttl_seconds)
        
        # Add to indexes if provided
        if indexes:
            for index_name, index_value in indexes.items():
                index_key = self._make_index_key(index_name, index_value)
                await self.redis.sadd(index_key, key)
                await self.redis.expire(index_key, ttl_seconds)
        
        logger.debug(f"Set key '{key}' in namespace '{self.namespace}' with TTL {ttl_seconds}s")
        return True
    
    @handle_cache_errors(operation="get", default_return=None, suppress_errors=True)
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Retrieve a value from Redis.
        """
        redis_key = self._make_key(key)
        value = await self.redis.get(redis_key)
        
        if value is None:
            logger.debug(f"Key '{key}' not found or expired in namespace '{self.namespace}'")
            return None
        
        # Deserialize if requested
        if deserialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # If not valid JSON, return raw string
                return value
        else:
            return value
    
    @handle_cache_errors(operation="delete", default_return=False, suppress_errors=True)
    async def delete(self, key: str, indexes: Optional[Dict[str, str]] = None) -> bool:
        """
        Delete a value from Redis and its indexes.
        """
        redis_key = self._make_key(key)
        
        # Delete the main key
        deleted = await self.redis.delete(redis_key)
        
        # Remove from indexes if provided
        if indexes:
            for index_name, index_value in indexes.items():
                index_key = self._make_index_key(index_name, index_value)
                await self.redis.srem(index_key, key)
        
        if deleted > 0:
            logger.debug(f"Deleted key '{key}' from namespace '{self.namespace}'")
            return True
        else:
            logger.debug(f"Key '{key}' not found in namespace '{self.namespace}'")
            return False
    
    @handle_cache_errors(operation="exists", default_return=False, suppress_errors=True)
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        """
        redis_key = self._make_key(key)
        result = await self.redis.exists(redis_key)
        return result > 0
    
    @handle_cache_errors(operation="get_by_index", default_return=[], suppress_errors=True)
    async def get_by_index(self, index_name: str, index_value: str) -> List[Any]:
        """
        Retrieve all items matching an index.
        """
        index_key = self._make_index_key(index_name, index_value)
        
        # Get all keys from the index set
        keys = await self.redis.smembers(index_key)
        
        if not keys:
            return []
        
        # Retrieve each item (filters out expired items automatically)
        items = []
        for key in keys:
            item = await self.get(key)
            if item is not None:
                items.append(item)
        
        logger.debug(
            f"Retrieved {len(items)} items from index '{index_name}:{index_value}' "
            f"in namespace '{self.namespace}'"
        )
        return items
    
    @handle_cache_errors(operation="get_keys_by_index", default_return=set(), suppress_errors=True)
    async def get_keys_by_index(self, index_name: str, index_value: str) -> Set[str]:
        """
        Get all keys (identifiers) matching an index.
        """
        index_key = self._make_index_key(index_name, index_value)
        keys = await self.redis.smembers(index_key)
        return keys if keys else set()
    
    @handle_cache_errors(operation="update", default_return=False, suppress_errors=True)
    async def update(
        self,
        key: str,
        updates: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Update specific fields in a stored dict/object.
        """
        # Get existing value
        existing = await self.get(key)
        if existing is None:
            logger.warning(f"Cannot update - key '{key}' not found in namespace '{self.namespace}'")
            return False
        
        # Ensure existing value is a dict
        if not isinstance(existing, dict):
            logger.error(f"Cannot update - key '{key}' is not a dict")
            return False
        
        # Update fields
        existing.update(updates)
        
        # Save back with refreshed TTL
        return await self.set(key, existing, ttl=ttl)
    
    @handle_cache_errors(operation="set_ttl", default_return=False, suppress_errors=True)
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Update the TTL of an existing key.
        """
        redis_key = self._make_key(key)
        result = await self.redis.expire(redis_key, ttl)
        
        if result:
            logger.debug(f"Updated TTL for key '{key}' to {ttl}s in namespace '{self.namespace}'")
        else:
            logger.warning(f"Failed to update TTL - key '{key}' not found")
        
        return result
    
    @handle_cache_errors(operation="get_ttl", default_return=None, suppress_errors=True)
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining TTL of a key.
        Returns None if key doesn't exist.
        """
        redis_key = self._make_key(key)
        # Redis returns TTL in seconds, or special values:
        # -2 if key doesn't exist, -1 if key has no expiration
        ttl = await self.redis.ttl(redis_key)
        return None if ttl == -2 else ttl
    
    @handle_cache_errors(operation="increment", default_return=None, suppress_errors=True)
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> Optional[int]:
        """
        Increment a numeric value in Redis.
        """
        redis_key = self._make_key(key)
        
        # Increment the value
        new_value = await self.redis.incr(redis_key, amount)
        
        # Set TTL if this is a new key and TTL is specified
        if new_value == amount and ttl:
            await self.redis.expire(redis_key, ttl)
        
        return new_value
    
    @handle_cache_errors(operation="clear_namespace", default_return=0, suppress_errors=True)
    async def clear_namespace(self) -> int:
        """
        Delete all keys in this namespace.
        """
        # Use SCAN to find all keys with this namespace prefix
        pattern = f"{self.namespace}:*"
        cursor = 0
        deleted_count = 0
        
        # Scan and collect keys
        keys_to_delete = []
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                keys_to_delete.extend(keys)
            if cursor == 0:
                break
        
        # Delete all collected keys
        if keys_to_delete:
            deleted_count = await self.redis.delete(*keys_to_delete)
        
        logger.warning(
            f"Cleared namespace '{self.namespace}' - deleted {deleted_count} keys"
        )
        return deleted_count
