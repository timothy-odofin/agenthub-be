"""
Cache service wrapper for easy dependency injection.

Provides a simple wrapper around CacheFactory for use in FastAPI dependency injection.
Don't use pre-configured instances - create cache per use case instead.

Usage in services:
    from app.infrastructure.cache import CacheService
    
    class BusinessPlanService:
        def __init__(self):
            self.cache = CacheService(namespace="business_plans", default_ttl=600)
        
        async def get_plan(self, plan_id: int):
            cached = await self.cache.get(f"plan_{plan_id}")
            if cached:
                return cached
            # ... fetch from DB, cache it
            
    # Or use with specific cache type
    class AnalyticsService:
        def __init__(self):
            self.cache = CacheService(
                namespace="analytics",
                default_ttl=3600,
                cache_type=CacheType.REDIS
            )
"""

from typing import Any, Optional, Dict, List
from app.infrastructure.cache.cache_factory import CacheFactory
from app.core.enums import CacheType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Convenience wrapper around cache providers.
    
    Makes it easy to use caching in services without dealing with factory directly.
    Each service gets its own cache instance with appropriate namespace.
    
    This is a thin wrapper that delegates all operations to the underlying cache provider.
    Use this in your business logic services for cleaner dependency injection.
    """
    
    def __init__(
        self,
        namespace: str,
        default_ttl: int = 900,
        cache_type: Optional[CacheType] = None
    ):
        """
        Initialize cache service.
        
        Args:
            namespace: Cache namespace (e.g., "business_plans", "corrections", "user_sessions")
            default_ttl: Default TTL in seconds (default: 15 minutes = 900 seconds)
            cache_type: Optional cache type (defaults to config from application-db.yaml)
            
        Example:
            >>> # Auto-detect from config
            >>> cache = CacheService(namespace="orders", default_ttl=1800)
            
            >>> # Explicit cache type
            >>> cache = CacheService(
            ...     namespace="sessions",
            ...     default_ttl=3600,
            ...     cache_type=CacheType.REDIS
            ... )
        """
        self.namespace = namespace
        self.default_ttl = default_ttl
        self._provider = CacheFactory.create_cache(
            cache_type=cache_type,
            namespace=namespace,
            default_ttl=default_ttl
        )
        logger.debug(f"CacheService initialized with namespace '{namespace}', TTL={default_ttl}s")
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        indexes: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to store (will be JSON serialized)
            ttl: Optional TTL override (seconds)
            indexes: Optional secondary indexes for lookup
            
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> await cache.set("user_123", {"name": "Alice", "email": "alice@example.com"})
            >>> await cache.set("order_456", order_data, ttl=3600)
            >>> await cache.set("action_789", data, indexes={"user_id": "123"})
        """
        return await self._provider.set(key, value, ttl, indexes)
    
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            deserialize: Whether to deserialize JSON (default: True)
            
        Returns:
            Cached value or None if not found
            
        Example:
            >>> user = await cache.get("user_123")
            >>> if user:
            ...     print(user["name"])
        """
        return await self._provider.get(key, deserialize)
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if key didn't exist
            
        Example:
            >>> await cache.delete("user_123")
        """
        return await self._provider.delete(key)
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
            
        Example:
            >>> if await cache.exists("user_123"):
            ...     print("User is cached")
        """
        return await self._provider.exists(key)
    
    async def get_by_index(
        self,
        index_name: str,
        index_value: str,
        deserialize: bool = True
    ) -> List[Any]:
        """
        Get all values matching an index.
        
        Useful for querying all cache entries associated with a secondary key.
        
        Args:
            index_name: Name of the index (e.g., "user_id")
            index_value: Value to match (e.g., "123")
            deserialize: Whether to deserialize JSON (default: True)
            
        Returns:
            List of matching values
            
        Example:
            >>> # Get all actions for a user
            >>> actions = await cache.get_by_index("user_id", "123")
            >>> for action in actions:
            ...     print(action["type"])
        """
        return await self._provider.get_by_index(index_name, index_value, deserialize)
    
    async def delete_by_index(self, index_name: str, index_value: str) -> int:
        """
        Delete all values matching an index.
        
        Args:
            index_name: Name of the index
            index_value: Value to match
            
        Returns:
            Number of items deleted
            
        Example:
            >>> # Delete all actions for a user
            >>> count = await cache.delete_by_index("user_id", "123")
            >>> print(f"Deleted {count} actions")
        """
        return await self._provider.delete_by_index(index_name, index_value)
    
    async def clear_namespace(self) -> int:
        """
        Clear all keys in this namespace.
        
        ⚠️ WARNING: This deletes ALL cache entries in this namespace!
        
        Returns:
            Number of keys deleted
            
        Example:
            >>> # Clear all business plan cache
            >>> count = await cache.clear_namespace()
            >>> print(f"Cleared {count} cached plans")
        """
        return await self._provider.clear_namespace()
    
    def get_provider_type(self) -> CacheType:
        """
        Get the underlying cache provider type.
        
        Returns:
            CacheType enum value
            
        Example:
            >>> cache = CacheService(namespace="test")
            >>> print(cache.get_provider_type())  # CacheType.REDIS
        """
        return self._provider.__class__.__name__


__all__ = ["CacheService"]
