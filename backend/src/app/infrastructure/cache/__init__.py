"""
Cache service module.

Provides a unified caching interface with pluggable backend providers (Redis, In-Memory, etc.).
Uses the registry pattern to allow extensible cache provider implementations.

Public API:
- CacheService: Convenience wrapper for business logic (RECOMMENDED)
- CacheFactory: Create cache instances
- CacheRegistry: Register/list cache providers
- BaseCacheProvider: Base class for custom providers
- CacheType: Enum of available cache types
- Pre-configured instances: confirmation_cache, signup_cache, session_cache, etc.

Example (Recommended):
    from app.infrastructure.cache import CacheService
    
    # Create cache service for your use case
    class BusinessPlanService:
        def __init__(self):
            self.cache = CacheService(namespace="business_plans", default_ttl=600)
        
        async def get_plan(self, plan_id: int):
            cached = await self.cache.get(f"plan_{plan_id}")
            if cached:
                return cached
            # ... fetch and cache

Example (Advanced - Factory):
    from app.infrastructure.cache import CacheFactory, CacheType
    
    # Auto-detect provider from config
    cache = CacheFactory.create_cache(namespace="my_app")
    
    # Explicitly use Redis
    redis_cache = CacheFactory.create_cache(CacheType.REDIS, namespace="my_app")

Example (Pre-configured instances):
    from app.infrastructure.cache import confirmation_cache
    
    await confirmation_cache.set("user:123", {"name": "Alice"}, ttl=3600)
    user = await confirmation_cache.get("user:123")
"""

# Import implementations to trigger registration
from app.infrastructure.cache import implementations  # noqa: F401

# Public API exports
from app.infrastructure.cache.base_cache_provider import BaseCacheProvider
from app.infrastructure.cache.cache_registry import CacheRegistry
from app.infrastructure.cache.cache_factory import CacheFactory
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.cache.error_handler import handle_cache_errors
from app.core.enums import CacheType

# Pre-configured cache instances
from app.infrastructure.cache.instances import (
    confirmation_cache,
    signup_cache,
    session_cache,
    rate_limit_cache,
    temp_cache,
)

__all__ = [
    # Recommended for business logic
    "CacheService",
    # Advanced usage
    "BaseCacheProvider",
    "CacheRegistry",
    "CacheFactory",
    "CacheType",
    "handle_cache_errors",
    # Pre-configured instances
    "confirmation_cache",
    "signup_cache",
    "session_cache",
    "rate_limit_cache",
    "temp_cache",
]

