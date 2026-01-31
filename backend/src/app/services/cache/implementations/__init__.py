"""
Cache provider implementations.

This package contains concrete implementations of the BaseCacheProvider interface.
Importing this module automatically registers all providers with the CacheRegistry.
"""

from app.services.cache.implementations.redis_cache import RedisCacheProvider
from app.services.cache.implementations.in_memory_cache import InMemoryCacheProvider

__all__ = [
    "RedisCacheProvider",
    "InMemoryCacheProvider",
]
