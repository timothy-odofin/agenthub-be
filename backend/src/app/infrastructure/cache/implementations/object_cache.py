"""
Object cache provider for caching non-serializable Python objects.

This cache provider is designed specifically for objects that cannot be
pickled/serialized (e.g., objects containing locks, network connections,
file handles, etc.).

Unlike Redis/Memcached which store serialized data, this provider stores
direct Python object references in memory with LRU eviction.

Use Cases:
- LLM provider instances (contain locks, network connections)
- Agent instances (contain stateful LLM clients)
- Database connection pools
- Compiled regex patterns
- Any object with unpicklable state
"""

import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Set

from app.core.core_enums import CacheType
from app.core.utils.logger import get_logger
from app.infrastructure.cache.base_cache_provider import BaseCacheProvider
from app.infrastructure.cache.cache_registry import CacheRegistry
from app.infrastructure.cache.error_handler import handle_cache_errors

logger = get_logger(__name__)


class ObjectCacheEntry:
    """A cache entry holding an object reference with metadata."""

    def __init__(self, value: Any, expires_at: Optional[float]):
        self.value = value
        self.expires_at = expires_at
        self.access_count = 0
        self.created_at = time.time()

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@CacheRegistry.register(CacheType.OBJECT)
class ObjectCacheProvider(BaseCacheProvider):
    """
    In-memory cache provider for non-serializable Python objects.

    Features:
    - Thread-safe with threading.RLock
    - LRU eviction with configurable max_size
    - Direct object references (no serialization)
    - Optional TTL support
    - Hit/miss telemetry

    Limitations:
    - Not distributed (single process only)
    - No persistence (data lost on restart)
    - Cannot store objects across network boundaries

    Thread Safety:
    Uses threading.RLock (reentrant lock) to allow nested cache operations
    within the same thread while preventing race conditions across threads.

    LRU Eviction:
    When cache reaches max_size, least recently used entry is evicted.
    Access count is tracked to determine LRU candidate.
    """

    def __init__(
        self,
        namespace: str,
        default_ttl: int = None,  # None = no expiration by default
        max_size: int = 50,
    ):
        """
        Initialize object cache provider.

        Args:
            namespace: Namespace prefix for all keys
            default_ttl: Default TTL in seconds (None = no expiration)
            max_size: Maximum number of entries before LRU eviction
        """
        super().__init__(namespace, default_ttl)
        self.max_size = max_size
        self._store: OrderedDict[str, ObjectCacheEntry] = OrderedDict()
        self._indexes: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested operations

        # Telemetry
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.info(
            f"ObjectCacheProvider initialized: namespace='{namespace}', "
            f"max_size={max_size}, default_ttl={default_ttl}"
        )

    @handle_cache_errors(operation="set", default_return=False, suppress_errors=True)
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        indexes: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Store an object reference with optional TTL and indexes.

        WARNING: The object is stored by reference, not copied.
        If you mutate the object after caching, all callers see the mutation.
        For immutable caching, ensure objects are configured before caching.
        """
        cache_key = self._make_key(key)
        ttl_seconds = ttl if ttl is not None else self.default_ttl

        # Calculate expiration time
        expires_at = None if ttl_seconds is None else time.time() + ttl_seconds

        with self._lock:
            # Check if we need to evict (LRU)
            if cache_key not in self._store and len(self._store) >= self.max_size:
                self._evict_lru()

            # Store the entry
            entry = ObjectCacheEntry(value, expires_at)
            self._store[cache_key] = entry
            self._store.move_to_end(cache_key)  # Mark as most recently used

            # Add to indexes
            if indexes:
                for index_name, index_value in indexes.items():
                    index_key = self._make_index_key(index_name, index_value)
                    if index_key not in self._indexes:
                        self._indexes[index_key] = set()
                    self._indexes[index_key].add(key)

        logger.debug(
            f"Stored object in cache: key='{key}', namespace='{self.namespace}', "
            f"ttl={ttl_seconds}, has_indexes={bool(indexes)}"
        )
        return True

    def _evict_lru(self) -> None:
        """
        Evict the least recently used entry.

        Must be called with lock held!
        """
        if not self._store:
            return

        # OrderedDict: first item is least recently used
        lru_key, lru_entry = self._store.popitem(last=False)
        self._evictions += 1

        logger.debug(
            f"Evicted LRU entry: key='{lru_key}', "
            f"age={(time.time() - lru_entry.created_at):.2f}s, "
            f"access_count={lru_entry.access_count}"
        )

    @handle_cache_errors(operation="get", default_return=None, suppress_errors=True)
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Retrieve an object reference.

        Note: deserialize parameter is ignored since we store object references,
        but kept for interface compatibility.
        """
        cache_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(cache_key)

            if entry is None:
                self._misses += 1
                return None

            # Check expiration
            if entry.is_expired():
                del self._store[cache_key]
                self._misses += 1
                logger.debug(f"Key '{key}' expired in namespace '{self.namespace}'")
                return None

            # Update LRU tracking
            entry.access_count += 1
            self._store.move_to_end(cache_key)  # Mark as recently used
            self._hits += 1

            return entry.value

    @handle_cache_errors(operation="delete", default_return=False, suppress_errors=True)
    async def delete(self, key: str, indexes: Optional[Dict[str, str]] = None) -> bool:
        """Delete an object and its indexes."""
        cache_key = self._make_key(key)

        with self._lock:
            if cache_key not in self._store:
                return False

            del self._store[cache_key]

            # Clean up indexes
            if indexes:
                for index_name, index_value in indexes.items():
                    index_key = self._make_index_key(index_name, index_value)
                    if index_key in self._indexes:
                        self._indexes[index_key].discard(key)
                        if not self._indexes[index_key]:
                            del self._indexes[index_key]

        logger.debug(f"Deleted key '{key}' from namespace '{self.namespace}'")
        return True

    @handle_cache_errors(operation="exists", default_return=False, suppress_errors=True)
    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        cache_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(cache_key)
            if entry is None:
                return False

            if entry.is_expired():
                del self._store[cache_key]
                return False

            return True

    @handle_cache_errors(
        operation="get_by_index", default_return=[], suppress_errors=True
    )
    async def get_by_index(self, index_name: str, index_value: str) -> List[Any]:
        """Retrieve all objects matching a secondary index."""
        index_key = self._make_index_key(index_name, index_value)

        with self._lock:
            keys = self._indexes.get(index_key, set()).copy()

        # Fetch all values (handles expiration)
        results = []
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results.append(value)

        return results

    @handle_cache_errors(
        operation="get_keys_by_index", default_return=set(), suppress_errors=True
    )
    async def get_keys_by_index(self, index_name: str, index_value: str) -> Set[str]:
        """Get all keys matching a secondary index."""
        index_key = self._make_index_key(index_name, index_value)

        with self._lock:
            return self._indexes.get(index_key, set()).copy()

    @handle_cache_errors(operation="update", default_return=False, suppress_errors=True)
    async def update(
        self, key: str, updates: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Update fields in a cached object.

        WARNING: This only works if the cached object is a mutable dict/object.
        If you cached an immutable object, this will fail.
        """
        obj = await self.get(key)
        if obj is None:
            return False

        # Update fields if object is a dict
        if isinstance(obj, dict):
            obj.update(updates)
        # Update attributes if object has __dict__
        elif hasattr(obj, "__dict__"):
            for field, value in updates.items():
                setattr(obj, field, value)
        else:
            logger.warning(f"Cannot update immutable object of type {type(obj)}")
            return False

        # Refresh TTL
        if ttl is not None:
            cache_key = self._make_key(key)
            with self._lock:
                if cache_key in self._store:
                    self._store[cache_key].expires_at = time.time() + ttl

        return True

    @handle_cache_errors(
        operation="set_ttl", default_return=False, suppress_errors=True
    )
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Update the TTL of an existing key."""
        cache_key = self._make_key(key)

        with self._lock:
            if cache_key not in self._store:
                return False

            self._store[cache_key].expires_at = time.time() + ttl

        return True

    @handle_cache_errors(operation="get_ttl", default_return=None, suppress_errors=True)
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get the remaining TTL for a key."""
        cache_key = self._make_key(key)

        with self._lock:
            entry = self._store.get(cache_key)
            if entry is None or entry.expires_at is None:
                return None

            remaining = int(entry.expires_at - time.time())
            return max(0, remaining)

    @handle_cache_errors(
        operation="increment", default_return=None, suppress_errors=True
    )
    async def increment(
        self, key: str, amount: int = 1, ttl: Optional[int] = None
    ) -> Optional[int]:
        """
        Increment a numeric value in the cache.

        Note: For object cache, this stores the counter as an integer object.

        Args:
            key: Unique identifier for the counter
            amount: Amount to increment by (default: 1)
            ttl: Optional TTL in seconds

        Returns:
            New value after increment, None on error
        """
        with self._lock:
            cache_key = self._make_key(key)

            # Get current value or initialize to 0
            entry = self._store.get(cache_key)
            if entry is None or not isinstance(entry.value, (int, float)):
                current_value = 0
            else:
                current_value = entry.value

            # Increment
            new_value = current_value + amount

            # Calculate expiration
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            elif entry is not None and entry.expires_at is not None:
                expires_at = entry.expires_at

            # Store new value
            self._store[cache_key] = ObjectCacheEntry(new_value, expires_at)

            # Move to end for LRU
            self._store.move_to_end(cache_key)

            logger.debug(
                f"Incremented {cache_key}: {current_value} + {amount} = {new_value}"
            )
            return new_value

    @handle_cache_errors(
        operation="clear_namespace", default_return=0, suppress_errors=True
    )
    async def clear_namespace(self) -> int:
        """Clear all entries in this namespace."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._indexes.clear()

        logger.info(f"Cleared {count} entries from namespace '{self.namespace}'")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns telemetry data for monitoring and optimization.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "namespace": self.namespace,
                "size": len(self._store),
                "max_size": self.max_size,
                "utilization": f"{(len(self._store) / self.max_size * 100):.1f}%",
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "evictions": self._evictions,
                "total_requests": total_requests,
            }

    def _make_key(self, key: str) -> str:
        """Create namespaced key."""
        return f"{self.namespace}:{key}"

    def _make_index_key(self, index_name: str, index_value: str) -> str:
        """Create namespaced index key."""
        return f"{self.namespace}:index:{index_name}:{index_value}"
