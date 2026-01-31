"""
Factory for creating cache provider instances.

Provides a centralized factory for creating and managing different
types of cache providers using the registry pattern.

Follows the same pattern as ConnectionFactory.
"""

from typing import Optional, List
from app.core.enums import CacheType
from app.services.cache.cache_registry import CacheRegistry
from app.services.cache.base_cache_provider import BaseCacheProvider
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class CacheFactory:
    """
    Factory class for creating cache provider instances.
    
    This factory uses the registry pattern to create cache providers
    based on configuration or explicit type specification.
    """
    
    _instance: Optional['CacheFactory'] = None
    
    def __new__(cls):
        """Singleton pattern - only one factory instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def create_cache(
        cache_type: Optional[CacheType] = None,
        namespace: str = "default",
        default_ttl: int = 900
    ) -> BaseCacheProvider:
        """
        Create a cache provider instance.
        
        Args:
            cache_type: Type of cache provider to create. If None, will try to
                       detect from configuration (application-db.yaml)
            namespace: Namespace for this cache instance (e.g., "confirmation", "signup")
            default_ttl: Default time-to-live in seconds (default: 15 minutes)
            
        Returns:
            Cache provider instance ready to use
            
        Raises:
            ValueError: If cache type is not available or not registered
            
        Example:
            >>> # Explicit type
            >>> cache = CacheFactory.create_cache(
            ...     cache_type=CacheType.REDIS,
            ...     namespace="confirmation",
            ...     default_ttl=900
            ... )
            
            >>> # Auto-detect from config
            >>> cache = CacheFactory.create_cache(namespace="signup")
        """
        # Auto-detect cache type from configuration if not specified
        if cache_type is None:
            cache_type = CacheFactory._detect_cache_type_from_config()
        
        # Validate cache type is registered
        if not CacheRegistry.is_cache_registered(cache_type):
            available = [ct.value for ct in CacheRegistry.list_cache_providers()]
            raise ValueError(
                f"Cache provider '{cache_type.value}' not available. "
                f"Available: {available}"
            )
        
        # Get cache provider class and create instance
        provider_class = CacheRegistry.get_cache_provider_class(cache_type)
        cache_provider = provider_class(namespace=namespace, default_ttl=default_ttl)
        
        logger.info(
            f"Created cache provider: {cache_type.value} "
            f"(namespace='{namespace}', ttl={default_ttl}s)"
        )
        return cache_provider
    
    @staticmethod
    def _detect_cache_type_from_config() -> CacheType:
        """
        Detect cache type from application configuration.
        
        Reads from application-db.yaml: cache.provider setting.
        
        Returns:
            Detected cache type
            
        Raises:
            ValueError: If configuration is invalid or missing
            
        Note: Uses lazy import to avoid circular dependency:
        app.services.cache → app.core.config.framework.settings → app.services
        Settings are only loaded when determining cache type.
        """
        try:
            from app.core.config.framework.settings import settings
            
            # Try to get cache configuration
            if hasattr(settings, 'db') and hasattr(settings.db, 'cache'):
                cache_config = settings.db.cache
                if hasattr(cache_config, 'provider'):
                    provider_str = cache_config.provider
                    # Convert string to CacheType enum
                    try:
                        return CacheType(provider_str)
                    except ValueError:
                        available = [ct.value for ct in CacheType]
                        raise ValueError(
                            f"Invalid cache provider '{provider_str}' in configuration. "
                            f"Valid options: {available}"
                        )
            
            # Fallback to Redis if no configuration found
            logger.warning(
                "No cache.provider found in configuration. Defaulting to Redis."
            )
            return CacheType.REDIS
            
        except Exception as e:
            logger.warning(
                f"Could not detect cache type from configuration: {e}. "
                f"Defaulting to Redis."
            )
            return CacheType.REDIS
    
    @staticmethod
    def list_available_cache_providers() -> List[CacheType]:
        """
        List all available cache provider types.
        
        Returns:
            List of registered cache types
        """
        return CacheRegistry.list_cache_providers()
    
    @staticmethod
    def is_cache_provider_available(cache_type: CacheType) -> bool:
        """
        Check if a cache provider type is available.
        
        Args:
            cache_type: The cache type to check
            
        Returns:
            True if available, False otherwise
        """
        return CacheRegistry.is_cache_registered(cache_type)
