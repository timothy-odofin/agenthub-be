"""
In-memory cache provider implementation.

A simple dict-based cache implementation for testing and development.
Not suitable for production use in distributed systems.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Set

from app.infrastructure.cache.base_cache_provider import BaseCacheProvider
from app.infrastructure.cache.cache_registry import CacheRegistry
from app.infrastructure.cache.error_handler import handle_cache_errors
from app.core.enums import CacheType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """A cache entry with value and expiration time."""
    
    def __init__(self, value: Any, expires_at: Optional[float]):
        self.value = value
        self.expires_at = expires_at
    
    def is_expired(self) -> bool:
        """Check if this entry has expired. Returns False if no expiration set."""
        if self.expires_at is None:
            return False  # No expiration means never expires
        return time.time() > self.expires_at


@CacheRegistry.register(CacheType.IN_MEMORY)
class InMemoryCacheProvider(BaseCacheProvider):
    """
    In-memory cache provider using Python dict.
    
    Features:
    - Thread-safe with asyncio.Lock
    - Automatic expiration checking
    - Secondary indexing support
    - JSON serialization/deserialization
    
    Limitations:
    - Not distributed (single process only)
    - No persistence (data lost on restart)
    - Memory-based (limited by RAM)
    - No TTL cleanup background task (expired items removed on access)
    
    Use Cases:
    - Unit testing
    - Development
    - Single-instance deployments
    - Caching non-critical data
    """
    
    def __init__(self, namespace: str, default_ttl: int = 900):
        """
        Initialize in-memory cache provider.
        
        Args:
            namespace: Namespace prefix for all keys
            default_ttl: Default TTL in seconds (default: 15 minutes)
        """
        super().__init__(namespace, default_ttl)
        self._store: Dict[str, CacheEntry] = {}
        self._indexes: Dict[str, Set[str]] = {}  # index_key -> set of keys
        self._lock = asyncio.Lock()
        logger.debug(f"InMemoryCacheProvider initialized with namespace '{namespace}'")
    
    @handle_cache_errors(operation="set", default_return=False, suppress_errors=True)
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        indexes: Optional[Dict[str, str]] = None
    ) -> bool:
        """Store a value with optional TTL and indexes."""
        cache_key = self._make_key(key)
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        
        # Calculate expiration time (None means no expiration)
        expires_at = None if ttl_seconds is None else time.time() + ttl_seconds
        
        # Serialize value to ensure consistency with Redis
        if not isinstance(value, str):
            serialized_value = json.dumps(value)
        else:
            serialized_value = value
        
        async with self._lock:
            # Store the entry
            self._store[cache_key] = CacheEntry(serialized_value, expires_at)
            
            # Add to indexes
            if indexes:
                for index_name, index_value in indexes.items():
                    index_key = self._make_index_key(index_name, index_value)
                    if index_key not in self._indexes:
                        self._indexes[index_key] = set()
                    self._indexes[index_key].add(key)
        
        logger.debug(f"Set key '{key}' in namespace '{self.namespace}' with TTL {ttl_seconds}s")
        return True
    
    @handle_cache_errors(operation="get", default_return=None, suppress_errors=True)
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Retrieve a value."""
        cache_key = self._make_key(key)
        
        async with self._lock:
            entry = self._store.get(cache_key)
            
            if entry is None:
                return None
            
            # Check expiration
            if entry.is_expired():
                # Clean up expired entry
                del self._store[cache_key]
                logger.debug(f"Key '{key}' expired in namespace '{self.namespace}'")
                return None
            
            value = entry.value
        
        # Deserialize if requested
        if deserialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            return value
    
    @handle_cache_errors(operation="delete", default_return=False, suppress_errors=True)
    async def delete(self, key: str, indexes: Optional[Dict[str, str]] = None) -> bool:
        """Delete a value and its indexes."""
        cache_key = self._make_key(key)
        
        async with self._lock:
            if cache_key not in self._store:
                return False
            
            # Delete main key
            del self._store[cache_key]
            
            # Remove from indexes
            if indexes:
                for index_name, index_value in indexes.items():
                    index_key = self._make_index_key(index_name, index_value)
                    if index_key in self._indexes:
                        self._indexes[index_key].discard(key)
                        # Clean up empty index sets
                        if not self._indexes[index_key]:
                            del self._indexes[index_key]
        
        logger.debug(f"Deleted key '{key}' from namespace '{self.namespace}'")
        return True
    
    @handle_cache_errors(operation="exists", default_return=False, suppress_errors=True)
    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        cache_key = self._make_key(key)
        
        async with self._lock:
            entry = self._store.get(cache_key)
            
            if entry is None:
                return False
            
            # Check expiration
            if entry.is_expired():
                del self._store[cache_key]
                return False
            
            return True
    
    @handle_cache_errors(operation="get_by_index", default_return=[], suppress_errors=True)
    async def get_by_index(self, index_name: str, index_value: str) -> List[Any]:
        """Retrieve all items matching an index."""
        index_key = self._make_index_key(index_name, index_value)
        
        async with self._lock:
            keys = self._indexes.get(index_key, set()).copy()
        
        if not keys:
            return []
        
        # Retrieve each item (automatically filters out expired)
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
        """Get all keys matching an index."""
        index_key = self._make_index_key(index_name, index_value)
        
        async with self._lock:
            keys = self._indexes.get(index_key, set()).copy()
        
        return keys
    
    @handle_cache_errors(operation="update", default_return=False, suppress_errors=True)
    async def update(
        self,
        key: str,
        updates: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Update specific fields in a stored dict."""
        existing = await self.get(key)
        if existing is None:
            logger.warning(f"Cannot update - key '{key}' not found in namespace '{self.namespace}'")
            return False
        
        if not isinstance(existing, dict):
            logger.error(f"Cannot update - key '{key}' is not a dict")
            return False
        
        existing.update(updates)
        return await self.set(key, existing, ttl=ttl)
    
    @handle_cache_errors(operation="set_ttl", default_return=False, suppress_errors=True)
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Update the TTL of an existing key."""
        cache_key = self._make_key(key)
        
        async with self._lock:
            entry = self._store.get(cache_key)
            
            if entry is None or entry.is_expired():
                return False
            
            # Update expiration time
            entry.expires_at = time.time() + ttl
        
        logger.debug(f"Updated TTL for key '{key}' to {ttl}s in namespace '{self.namespace}'")
        return True
    
    @handle_cache_errors(operation="get_ttl", default_return=None, suppress_errors=True)
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get the remaining TTL of a key. Returns None if key doesn't exist or has no expiration."""
        cache_key = self._make_key(key)
        
        async with self._lock:
            entry = self._store.get(cache_key)
            
            if entry is None:
                return None  # Key doesn't exist
            
            if entry.is_expired():
                del self._store[cache_key]
                return None  # Key expired (doesn't exist)
            
            if entry.expires_at is None:
                return -1  # No expiration (like Redis convention)
            
            remaining = int(entry.expires_at - time.time())
            return max(0, remaining)
    
    @handle_cache_errors(operation="increment", default_return=None, suppress_errors=True)
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> Optional[int]:
        """Increment a numeric value."""
        cache_key = self._make_key(key)
        
        async with self._lock:
            entry = self._store.get(cache_key)
            
            if entry is None or entry.is_expired():
                # Create new entry
                new_value = amount
                ttl_seconds = ttl or self.default_ttl
                expires_at = time.time() + ttl_seconds
                self._store[cache_key] = CacheEntry(str(new_value), expires_at)
            else:
                # Increment existing value
                try:
                    current_value = int(entry.value)
                    new_value = current_value + amount
                    entry.value = str(new_value)
                except ValueError:
                    logger.error(f"Cannot increment - key '{key}' is not numeric")
                    return None
        
        return new_value
    
    @handle_cache_errors(operation="clear_namespace", default_return=0, suppress_errors=True)
    async def clear_namespace(self) -> int:
        """Delete all keys in this namespace."""
        prefix = f"{self.namespace}:"
        
        async with self._lock:
            # Find all keys with this namespace
            keys_to_delete = [k for k in self._store.keys() if k.startswith(prefix)]
            
            # Delete them
            for key in keys_to_delete:
                del self._store[key]
            
            # Clean up indexes
            index_keys_to_delete = [k for k in self._indexes.keys() if k.startswith(prefix)]
            for index_key in index_keys_to_delete:
                del self._indexes[index_key]
            
            count = len(keys_to_delete)
        
        logger.warning(f"Cleared namespace '{self.namespace}' - deleted {count} keys")
        return count
    
    @handle_cache_errors(operation="cleanup_expired", default_return=0, suppress_errors=True)
    async def cleanup_expired(self) -> int:
        """
        Manually remove all expired entries.
        
        This is useful for testing or periodic cleanup.
        In production, expired entries are removed lazily on access.
        
        Returns:
            Number of expired entries removed
        """
        async with self._lock:
            expired_keys = [
                k for k, entry in self._store.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._store[key]
            
            count = len(expired_keys)
        
        if count > 0:
            logger.debug(f"Cleaned up {count} expired entries from namespace '{self.namespace}'")
        
        return count
