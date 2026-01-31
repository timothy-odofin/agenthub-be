"""
Base cache provider abstract class.

Defines the interface that all cache providers must implement.
Follows the same pattern as BaseConnectionManager and BaseSessionRepository.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union


class BaseCacheProvider(ABC):
    """
    Abstract base class for all cache providers.
    
    All cache implementations (Redis, Memcached, In-Memory, etc.) must extend
    this class and implement all abstract methods.
    
    Attributes:
        namespace: Key prefix for this cache instance (e.g., "confirmation", "signup")
        default_ttl: Default time-to-live in seconds for cached items
    """
    
    def __init__(self, namespace: str, default_ttl: int = 900):
        """
        Initialize the cache provider.
        
        Args:
            namespace: Namespace prefix for all keys (prevents collisions)
            default_ttl: Default TTL in seconds (default: 15 minutes)
        """
        self.namespace = namespace
        self.default_ttl = default_ttl
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        indexes: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Store a value in the cache with optional TTL and secondary indexes.
        
        Args:
            key: Unique identifier for the item
            value: Data to store (will be JSON-serialized if not a string)
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
            True
        """
        pass
    
    @abstractmethod
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: Unique identifier for the item
            deserialize: If True, attempts to parse JSON; if False, returns raw string
        
        Returns:
            Deserialized value if found and not expired, None otherwise
        
        Example:
            >>> data = await cache.get("action_123")
            >>> print(data["user"])
            "alice"
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str, indexes: Optional[Dict[str, str]] = None) -> bool:
        """
        Delete a value from the cache and clean up its indexes.
        
        Args:
            key: Unique identifier for the item
            indexes: Optional dict of index_name -> index_value to clean up
                    Should match the indexes used when setting the value
        
        Returns:
            True if deleted, False if not found or error
        
        Example:
            >>> await cache.delete("action_123", indexes={"user": "alice"})
            True
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Unique identifier for the item
        
        Returns:
            True if key exists and hasn't expired, False otherwise
        
        Example:
            >>> if await cache.exists("action_123"):
            ...     print("Action exists")
        """
        pass
    
    @abstractmethod
    async def get_by_index(self, index_name: str, index_value: str) -> List[Any]:
        """
        Retrieve all items matching a secondary index.
        
        This is useful for finding all items belonging to a user, session, etc.
        Only returns non-expired items.
        
        Args:
            index_name: Name of the index (e.g., "user", "session")
            index_value: Value to search for (e.g., user_id)
        
        Returns:
            List of deserialized items (empty list if none found)
        
        Example:
            >>> actions = await cache.get_by_index("user", "alice")
            >>> print(f"Alice has {len(actions)} pending actions")
        """
        pass
    
    @abstractmethod
    async def get_keys_by_index(self, index_name: str, index_value: str) -> Set[str]:
        """
        Get all keys (identifiers) matching a secondary index.
        
        Similar to get_by_index but returns only keys, not values.
        Useful when you need to know what items exist without fetching them.
        
        Args:
            index_name: Name of the index (e.g., "user", "session")
            index_value: Value to search for (e.g., user_id)
        
        Returns:
            Set of keys (empty set if none found)
        
        Example:
            >>> keys = await cache.get_keys_by_index("user", "alice")
            >>> print(f"Keys: {keys}")
        """
        pass
    
    @abstractmethod
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
            True if successful, False if item not found or not a dict
        
        Example:
            >>> await cache.update("action_123", {"status": "confirmed"})
            True
        """
        pass
    
    @abstractmethod
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Update the TTL of an existing key.
        
        Args:
            key: Unique identifier for the item
            ttl: New time-to-live in seconds
        
        Returns:
            True if successful, False if key doesn't exist
        
        Example:
            >>> await cache.set_ttl("action_123", 1800)  # Extend to 30 minutes
            True
        """
        pass
    
    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining TTL of a key.
        
        Args:
            key: Unique identifier for the item
        
        Returns:
            Remaining seconds if key exists, None if key doesn't exist
            Special values: -1 if key has no expiration
        
        Example:
            >>> ttl = await cache.get_ttl("action_123")
            >>> print(f"Expires in {ttl} seconds")
        """
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> Optional[int]:
        """
        Increment a numeric value in the cache.
        
        Useful for counters, rate limiting, etc.
        Creates the key with value=amount if it doesn't exist.
        
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
        pass
    
    @abstractmethod
    async def clear_namespace(self) -> int:
        """
        Delete all keys in this cache's namespace.
        
        **Use with caution!** This will delete all data for this namespace.
        
        Returns:
            Number of keys deleted
        
        Example:
            >>> deleted = await cache.clear_namespace()
            >>> print(f"Cleared {deleted} items from cache")
        """
        pass
    
    def _make_key(self, key: str) -> str:
        """
        Generate namespaced cache key.
        
        This is a helper method that implementations can use or override.
        
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
        Generate namespaced cache key for index (set).
        
        This is a helper method that implementations can use or override.
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
