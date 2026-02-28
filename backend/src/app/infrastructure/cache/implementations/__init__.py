"""
Cache provider implementations.

This package contains concrete implementations of the BaseCacheProvider interface.
Importing this module automatically registers all providers with the CacheRegistry.
"""

from app.infrastructure.cache.implementations.in_memory_cache import (
    InMemoryCacheProvider,
)
from app.infrastructure.cache.implementations.object_cache import ObjectCacheProvider
from app.infrastructure.cache.implementations.redis_cache import RedisCacheProvider

__all__ = [
    "RedisCacheProvider",
    "InMemoryCacheProvider",
    "ObjectCacheProvider",
]
