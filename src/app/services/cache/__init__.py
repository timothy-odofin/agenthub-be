"""
Cache service module.

Provides a unified caching interface with pluggable backend providers (Redis, In-Memory, etc.).
Uses the registry pattern to allow extensible cache provider implementations.

Public API:
- CacheFactory: Create cache instances
- CacheRegistry: Register/list cache providers
- BaseCacheProvider: Base class for custom providers
- CacheType: Enum of available cache types
- Pre-configured instances: confirmation_cache, signup_cache, session_cache, etc.

Example:
    from app.services.cache import CacheFactory, CacheType
    
    # Auto-detect provider from config
    cache = CacheFactory.create_cache(namespace="my_app")
    
    # Explicitly use Redis
    redis_cache = CacheFactory.create_cache(CacheType.REDIS, namespace="my_app")
    
    # Use pre-configured instances
    from app.services.cache import confirmation_cache
    await confirmation_cache.set("user:123", {"name": "Alice"}, ttl=3600)
    user = await confirmation_cache.get("user:123")
"""

# Import implementations to trigger registration
from app.services.cache import implementations  # noqa: F401

# Public API exports
from app.services.cache.base_cache_provider import BaseCacheProvider
from app.services.cache.cache_registry import CacheRegistry
from app.services.cache.cache_factory import CacheFactory
from app.services.cache.error_handler import handle_cache_errors
from app.core.enums import CacheType

# Pre-configured cache instances
from app.services.cache.instances import (
    confirmation_cache,
    signup_cache,
    session_cache,
    rate_limit_cache,
    temp_cache,
)

__all__ = [
    "BaseCacheProvider",
    "CacheRegistry",
    "CacheFactory",
    "CacheType",
    "handle_cache_errors",
    # Instances
    "confirmation_cache",
    "signup_cache",
    "session_cache",
    "rate_limit_cache",
    "temp_cache",
]

