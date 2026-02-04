"""
Cache provider implementations.

This package contains concrete implementations of the BaseCacheProvider interface.
Importing this module automatically registers all providers with the CacheRegistry.
"""

from app.infrastructure.cache.implementations.redis_cache import RedisCacheProvider
from app.infrastructure.cache.implementations.in_memory_cache import InMemoryCacheProvider

__all__ = [
    "RedisCacheProvider",
    "InMemoryCacheProvider",
]
