"""
Generic Redis cache service for temporary data storage.

This service provides a reusable abstraction for storing temporary/cached data
in Redis across the application. It follows the repository pattern and supports:

- Key-value storage with TTL
- JSON serialization/deserialization
- User-scoped data indexing
- Automatic expiration
- Batch operations

Use Cases:
- Confirmation workflow pending actions
- Signup session data
- Temporary authentication tokens
- Rate limiting counters
- Any temporary application state

Example:
    >>> cache = RedisCacheService(namespace="confirmation", default_ttl=900)
    >>> await cache.set("action_123", {"user": "alice", "action": "create"})
    >>> data = await cache.get("action_123")
    >>> await cache.delete("action_123")
"""

import json
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timedelta

from app.connections.factory.connection_factory import ConnectionFactory
from app.connections.base import ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCacheService:
    """
    Generic Redis-backed cache service for temporary data storage.
    
    This service provides a consistent interface for storing temporary data
    across the application. Each instance is scoped to a namespace to prevent
    key collisions.
    
    Attributes:
        namespace: Key prefix for this cache instance (e.g., "confirmation", "signup")
        default_ttl: Default time-to-live in seconds (default: 900 = 15 minutes)
    """
    
    def __init__(self, namespace: str, default_ttl: int = 900):
        """
        Initialize Redis cache service with a namespace.
        
        Args:
            namespace: Namespace prefix for all keys (e.g., "confirmation", "signup")
            default_ttl: Default TTL in seconds for cached items (default: 15 minutes)
        
        Example:
            >>> cache = RedisCacheService("confirmation", default_ttl=900)
        """
        self.namespace = namespace
        self.default_ttl = default_ttl
        self._redis_manager = None
        logger.info(f"RedisCacheService initialized with namespace '{namespace}' and TTL {default_ttl}s")
    
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
    
    def _make_key(self, key: str) -> str:
        """
        Generate namespaced Redis key.
        
        Args:
            key: Item identifier
            
        Returns:
            Namespaced key: "{namespace}:{key}"
            
        Example:
            >>> cache._make_key("action_123")
            "confirmation:action_123"
        """
        return f"{self.namespace}:{key}"
    
    def _make_index_key(self, index_name: str, index_value: str) -> str:
        """
        Generate namespaced Redis key for index (set).
        
        Used for tracking items by secondary keys (e.g., user_id).
        
        Args:
            index_name: Name of the index (e.g., "user", "session")
            index_value: Value to index by (e.g., user_id)
            
        Returns:
            Namespaced index key: "{namespace}:{index_name}:{index_value}"
            
        Example:
            >>> cache._make_index_key("user", "alice")
            "confirmation:user:alice"
        """
        return f"{self.namespace}:{index_name}:{index_value}"
    
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
        
        Args:
            key: Unique identifier for the item
            value: Data to store (dict, list, str, int, etc.)
            ttl: Time-to-live in seconds (uses default_ttl if not specified)
            indexes: Optional dict of index_name -> index_value for secondary lookups
                    Example: {"user": "alice", "session": "sess_123"}
        
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> await cache.set(
            ...     "action_123",
            ...     {"user": "alice", "action": "create"},
            ...     ttl=600,
            ...     indexes={"user": "alice"}
            ... )
        """
        try:
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
            
        except Exception as e:
            logger.error(f"Failed to set key '{key}' in namespace '{self.namespace}': {e}", exc_info=True)
            return False
    
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Retrieve a value from Redis.
        
        Args:
            key: Unique identifier for the item
            deserialize: If True, attempts to parse JSON; if False, returns raw string
        
        Returns:
            Deserialized value if found, None if not found or expired
            
        Example:
            >>> data = await cache.get("action_123")
            >>> print(data["user"])
            "alice"
        """
        try:
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
                
        except Exception as e:
            logger.error(f"Failed to get key '{key}' in namespace '{self.namespace}': {e}", exc_info=True)
            return None
    
    async def delete(self, key: str, indexes: Optional[Dict[str, str]] = None) -> bool:
        """
        Delete a value from Redis and its indexes.
        
        Args:
            key: Unique identifier for the item
            indexes: Optional dict of index_name -> index_value to clean up
                    Should match the indexes used when setting the value
        
        Returns:
            True if deleted, False if not found or error
            
        Example:
            >>> await cache.delete("action_123", indexes={"user": "alice"})
        """
        try:
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
                
        except Exception as e:
            logger.error(f"Failed to delete key '{key}' in namespace '{self.namespace}': {e}", exc_info=True)
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Unique identifier for the item
        
        Returns:
            True if key exists, False otherwise
            
        Example:
            >>> if await cache.exists("action_123"):
            ...     print("Action exists")
        """
        try:
            redis_key = self._make_key(key)
            result = await self.redis.exists(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check existence of key '{key}': {e}", exc_info=True)
            return False
    
    async def get_by_index(self, index_name: str, index_value: str) -> List[Any]:
        """
        Retrieve all items matching an index.
        
        This is useful for finding all items belonging to a user, session, etc.
        
        Args:
            index_name: Name of the index (e.g., "user", "session")
            index_value: Value to search for (e.g., user_id)
        
        Returns:
            List of deserialized items (only non-expired items)
            
        Example:
            >>> actions = await cache.get_by_index("user", "alice")
            >>> print(f"Alice has {len(actions)} pending actions")
        """
        try:
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
            
        except Exception as e:
            logger.error(
                f"Failed to get items by index '{index_name}:{index_value}' "
                f"in namespace '{self.namespace}': {e}",
                exc_info=True
            )
            return []
    
    async def get_keys_by_index(self, index_name: str, index_value: str) -> Set[str]:
        """
        Get all keys (identifiers) matching an index.
        
        Similar to get_by_index but returns only keys, not values.
        Useful when you need to know what items exist without fetching them.
        
        Args:
            index_name: Name of the index (e.g., "user", "session")
            index_value: Value to search for (e.g., user_id)
        
        Returns:
            Set of keys
            
        Example:
            >>> keys = await cache.get_keys_by_index("user", "alice")
            >>> print(f"Keys: {keys}")
        """
        try:
            index_key = self._make_index_key(index_name, index_value)
            keys = await self.redis.smembers(index_key)
            return keys if keys else set()
        except Exception as e:
            logger.error(
                f"Failed to get keys by index '{index_name}:{index_value}': {e}",
                exc_info=True
            )
            return set()
    
    async def update(
        self,
        key: str,
        updates: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Update specific fields in a stored dict/object.
        
        This retrieves the existing value, updates the specified fields,
        and saves it back with a refreshed TTL.
        
        Args:
            key: Unique identifier for the item
            updates: Dictionary of fields to update
            ttl: Optional new TTL (refreshes with default if not specified)
        
        Returns:
            True if successful, False if item not found or error
            
        Example:
            >>> await cache.update("action_123", {"status": "confirmed"})
        """
        try:
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
            
        except Exception as e:
            logger.error(f"Failed to update key '{key}' in namespace '{self.namespace}': {e}", exc_info=True)
            return False
    
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Update the TTL of an existing key.
        
        Args:
            key: Unique identifier for the item
            ttl: New time-to-live in seconds
        
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> await cache.set_ttl("action_123", 1800)  # Extend to 30 minutes
        """
        try:
            redis_key = self._make_key(key)
            result = await self.redis.expire(redis_key, ttl)
            
            if result:
                logger.debug(f"Updated TTL for key '{key}' to {ttl}s in namespace '{self.namespace}'")
            else:
                logger.warning(f"Failed to update TTL - key '{key}' not found")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to set TTL for key '{key}': {e}", exc_info=True)
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining TTL of a key.
        
        Args:
            key: Unique identifier for the item
        
        Returns:
            Remaining seconds, -1 if no TTL, -2 if key doesn't exist
            
        Example:
            >>> ttl = await cache.get_ttl("action_123")
            >>> print(f"Expires in {ttl} seconds")
        """
        try:
            redis_key = self._make_key(key)
            # Note: Redis returns TTL in seconds, or special values:
            # -2 if key doesn't exist, -1 if key has no expiration
            ttl = await self.redis.ttl(redis_key)
            return ttl if ttl >= -2 else None
        except Exception as e:
            logger.error(f"Failed to get TTL for key '{key}': {e}", exc_info=True)
            return None
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> Optional[int]:
        """
        Increment a numeric value in Redis.
        
        Useful for counters, rate limiting, etc.
        
        Args:
            key: Unique identifier for the counter
            amount: Amount to increment by (default: 1)
            ttl: Optional TTL for the key if it's created
        
        Returns:
            New value after increment, None on error
            
        Example:
            >>> count = await cache.increment("rate_limit:alice")
            >>> if count > 100:
            ...     print("Rate limit exceeded")
        """
        try:
            redis_key = self._make_key(key)
            
            # Increment the value
            new_value = await self.redis.incr(redis_key, amount)
            
            # Set TTL if this is a new key and TTL is specified
            if new_value == amount and ttl:
                await self.redis.expire(redis_key, ttl)
            
            return new_value
            
        except Exception as e:
            logger.error(f"Failed to increment key '{key}': {e}", exc_info=True)
            return None
    
    async def clear_namespace(self) -> int:
        """
        Delete all keys in this namespace.
        
        **Use with caution!** This will delete all data for this namespace.
        
        Returns:
            Number of keys deleted
            
        Example:
            >>> deleted = await cache.clear_namespace()
            >>> print(f"Cleared {deleted} items from confirmation cache")
        """
        try:
            # Use SCAN to find all keys with this namespace prefix
            pattern = f"{self.namespace}:*"
            cursor = 0
            deleted_count = 0
            
            # Note: scan_iter might not be available, using basic scan
            # In production, consider using scan_iter for large datasets
            keys_to_delete = []
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    keys_to_delete.extend(keys)
                if cursor == 0:
                    break
            
            if keys_to_delete:
                deleted_count = await self.redis.delete(*keys_to_delete)
            
            logger.warning(
                f"Cleared namespace '{self.namespace}' - deleted {deleted_count} keys"
            )
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear namespace '{self.namespace}': {e}", exc_info=True)
            return 0


# Singleton instances for common use cases
# Can be imported directly: from app.services.redis_cache_service import confirmation_cache

confirmation_cache = RedisCacheService(namespace="confirmation", default_ttl=900)  # 15 minutes
signup_cache = RedisCacheService(namespace="signup", default_ttl=300)  # 5 minutes
session_cache = RedisCacheService(namespace="session", default_ttl=1800)  # 30 minutes
rate_limit_cache = RedisCacheService(namespace="ratelimit", default_ttl=60)  # 1 minute
