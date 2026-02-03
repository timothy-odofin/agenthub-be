"""
Registry for cache providers.

Provides a centralized registry for discovering and managing different
types of cache providers using the decorator pattern.

Follows the same pattern as ConnectionRegistry, AgentRegistry, and ToolRegistry.
"""

from typing import Dict, Type, List
from app.core.enums import CacheType
from app.infrastructure.cache.base_cache_provider import BaseCacheProvider
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class CacheRegistry:
    """
    Registry for cache provider classes.
    
    Allows cache providers to self-register using a decorator pattern,
    making it easy to add new cache backends without modifying core code.
    """
    
    _registry: Dict[CacheType, Type[BaseCacheProvider]] = {}
    
    @classmethod
    def register(cls, cache_type: CacheType):
        """
        Decorator to register a cache provider class.
        
        Usage:
            @CacheRegistry.register(CacheType.REDIS)
            class RedisCacheProvider(BaseCacheProvider):
                # Implementation
        
        Args:
            cache_type: The type of cache this provider handles
            
        Returns:
            The decorator function
        """
        def decorator(cache_provider_class):
            # Validate that the class extends BaseCacheProvider
            if not issubclass(cache_provider_class, BaseCacheProvider):
                raise TypeError(
                    f"Cache provider {cache_provider_class.__name__} must extend BaseCacheProvider"
                )
            
            # Register the provider class
            cls._registry[cache_type] = cache_provider_class
            logger.info(
                f"Registered cache provider: {cache_type.value} -> {cache_provider_class.__name__}"
            )
            return cache_provider_class
        
        return decorator
    
    @classmethod
    def get_cache_provider_class(cls, cache_type: CacheType) -> Type[BaseCacheProvider]:
        """
        Get the cache provider class for a specific cache type.
        
        Args:
            cache_type: The cache type
            
        Returns:
            The cache provider class
            
        Raises:
            KeyError: If cache type is not registered
        """
        if cache_type not in cls._registry:
            available = [ct.value for ct in cls._registry.keys()]
            raise KeyError(
                f"Cache provider '{cache_type.value}' not registered. "
                f"Available: {available}"
            )
        
        return cls._registry[cache_type]
    
    @classmethod
    def is_cache_registered(cls, cache_type: CacheType) -> bool:
        """
        Check if a cache type is registered.
        
        Args:
            cache_type: The cache type to check
            
        Returns:
            True if registered, False otherwise
        """
        return cache_type in cls._registry
    
    @classmethod
    def list_cache_providers(cls) -> List[CacheType]:
        """
        List all registered cache provider types.
        
        Returns:
            List of registered cache types
        """
        return list(cls._registry.keys())
    
    @classmethod
    def clear_registry(cls) -> None:
        """
        Clear all registered cache providers.
        
        This is primarily useful for testing to ensure a clean state.
        """
        cls._registry.clear()
        logger.info("Cache provider registry cleared")
