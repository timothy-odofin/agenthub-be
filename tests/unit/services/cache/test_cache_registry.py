"""
Unit tests for CacheRegistry.

Tests the cache provider registration system using the decorator pattern.
"""

import pytest
from unittest.mock import MagicMock

from app.services.cache.cache_registry import CacheRegistry
from app.services.cache.base_cache_provider import BaseCacheProvider
from app.core.enums import CacheType


class TestCacheRegistry:
    """Test suite for CacheRegistry."""
    
    def setup_method(self):
        """Clear registry before each test."""
        CacheRegistry.clear_registry()
    
    def teardown_method(self):
        """Clear registry after each test."""
        CacheRegistry.clear_registry()
    
    def test_register_cache_provider(self):
        """Test registering a cache provider."""
        # Create a mock cache provider
        @CacheRegistry.register(CacheType.IN_MEMORY)
        class MockCacheProvider(BaseCacheProvider):
            async def set(self, key, value, ttl=None, indexes=None): pass
            async def get(self, key, deserialize=True): pass
            async def delete(self, key, indexes=None): pass
            async def exists(self, key): pass
            async def get_by_index(self, index_name, index_value): pass
            async def get_keys_by_index(self, index_name, index_value): pass
            async def update(self, key, updates, ttl=None): pass
            async def set_ttl(self, key, ttl): pass
            async def get_ttl(self, key): pass
            async def increment(self, key, amount=1, ttl=None): pass
            async def clear_namespace(self): pass
        
        # Verify registration
        assert CacheRegistry.is_cache_registered(CacheType.IN_MEMORY)
        provider_class = CacheRegistry.get_cache_provider_class(CacheType.IN_MEMORY)
        assert provider_class == MockCacheProvider
    
    def test_register_multiple_providers(self):
        """Test registering multiple cache providers."""
        @CacheRegistry.register(CacheType.IN_MEMORY)
        class InMemoryProvider(BaseCacheProvider):
            async def set(self, key, value, ttl=None, indexes=None): pass
            async def get(self, key, deserialize=True): pass
            async def delete(self, key, indexes=None): pass
            async def exists(self, key): pass
            async def get_by_index(self, index_name, index_value): pass
            async def get_keys_by_index(self, index_name, index_value): pass
            async def update(self, key, updates, ttl=None): pass
            async def set_ttl(self, key, ttl): pass
            async def get_ttl(self, key): pass
            async def increment(self, key, amount=1, ttl=None): pass
            async def clear_namespace(self): pass
        
        @CacheRegistry.register(CacheType.REDIS)
        class RedisProvider(BaseCacheProvider):
            async def set(self, key, value, ttl=None, indexes=None): pass
            async def get(self, key, deserialize=True): pass
            async def delete(self, key, indexes=None): pass
            async def exists(self, key): pass
            async def get_by_index(self, index_name, index_value): pass
            async def get_keys_by_index(self, index_name, index_value): pass
            async def update(self, key, updates, ttl=None): pass
            async def set_ttl(self, key, ttl): pass
            async def get_ttl(self, key): pass
            async def increment(self, key, amount=1, ttl=None): pass
            async def clear_namespace(self): pass
        
        # Verify both are registered
        assert CacheRegistry.is_cache_registered(CacheType.IN_MEMORY)
        assert CacheRegistry.is_cache_registered(CacheType.REDIS)
        
        providers = CacheRegistry.list_cache_providers()
        assert CacheType.IN_MEMORY in providers
        assert CacheType.REDIS in providers
        assert len(providers) == 2
    
    def test_register_invalid_provider_raises_error(self):
        """Test that registering a non-BaseCacheProvider class raises TypeError."""
        with pytest.raises(TypeError, match="must extend BaseCacheProvider"):
            @CacheRegistry.register(CacheType.IN_MEMORY)
            class InvalidProvider:
                pass
    
    def test_get_unregistered_provider_raises_error(self):
        """Test that getting an unregistered provider raises KeyError."""
        with pytest.raises(KeyError, match="not registered"):
            CacheRegistry.get_cache_provider_class(CacheType.MEMCACHED)
    
    def test_is_cache_registered_returns_false_for_unregistered(self):
        """Test that is_cache_registered returns False for unregistered types."""
        assert not CacheRegistry.is_cache_registered(CacheType.MEMCACHED)
        assert not CacheRegistry.is_cache_registered(CacheType.ELASTICACHE)
    
    def test_list_cache_providers_returns_empty_initially(self):
        """Test that list_cache_providers returns empty list initially."""
        providers = CacheRegistry.list_cache_providers()
        assert providers == []
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        @CacheRegistry.register(CacheType.IN_MEMORY)
        class MockProvider(BaseCacheProvider):
            async def set(self, key, value, ttl=None, indexes=None): pass
            async def get(self, key, deserialize=True): pass
            async def delete(self, key, indexes=None): pass
            async def exists(self, key): pass
            async def get_by_index(self, index_name, index_value): pass
            async def get_keys_by_index(self, index_name, index_value): pass
            async def update(self, key, updates, ttl=None): pass
            async def set_ttl(self, key, ttl): pass
            async def get_ttl(self, key): pass
            async def increment(self, key, amount=1, ttl=None): pass
            async def clear_namespace(self): pass
        
        assert CacheRegistry.is_cache_registered(CacheType.IN_MEMORY)
        
        CacheRegistry.clear_registry()
        
        assert not CacheRegistry.is_cache_registered(CacheType.IN_MEMORY)
        assert CacheRegistry.list_cache_providers() == []
    
    def test_register_same_type_twice_overwrites(self):
        """Test that registering the same type twice overwrites the first."""
        @CacheRegistry.register(CacheType.IN_MEMORY)
        class FirstProvider(BaseCacheProvider):
            async def set(self, key, value, ttl=None, indexes=None): pass
            async def get(self, key, deserialize=True): pass
            async def delete(self, key, indexes=None): pass
            async def exists(self, key): pass
            async def get_by_index(self, index_name, index_value): pass
            async def get_keys_by_index(self, index_name, index_value): pass
            async def update(self, key, updates, ttl=None): pass
            async def set_ttl(self, key, ttl): pass
            async def get_ttl(self, key): pass
            async def increment(self, key, amount=1, ttl=None): pass
            async def clear_namespace(self): pass
        
        @CacheRegistry.register(CacheType.IN_MEMORY)
        class SecondProvider(BaseCacheProvider):
            async def set(self, key, value, ttl=None, indexes=None): pass
            async def get(self, key, deserialize=True): pass
            async def delete(self, key, indexes=None): pass
            async def exists(self, key): pass
            async def get_by_index(self, index_name, index_value): pass
            async def get_keys_by_index(self, index_name, index_value): pass
            async def update(self, key, updates, ttl=None): pass
            async def set_ttl(self, key, ttl): pass
            async def get_ttl(self, key): pass
            async def increment(self, key, amount=1, ttl=None): pass
            async def clear_namespace(self): pass
        
        # Should be the second provider
        provider_class = CacheRegistry.get_cache_provider_class(CacheType.IN_MEMORY)
        assert provider_class == SecondProvider
    
    def test_decorator_returns_class(self):
        """Test that the decorator returns the class unchanged."""
        @CacheRegistry.register(CacheType.IN_MEMORY)
        class MockProvider(BaseCacheProvider):
            async def set(self, key, value, ttl=None, indexes=None): pass
            async def get(self, key, deserialize=True): pass
            async def delete(self, key, indexes=None): pass
            async def exists(self, key): pass
            async def get_by_index(self, index_name, index_value): pass
            async def get_keys_by_index(self, index_name, index_value): pass
            async def update(self, key, updates, ttl=None): pass
            async def set_ttl(self, key, ttl): pass
            async def get_ttl(self, key): pass
            async def increment(self, key, amount=1, ttl=None): pass
            async def clear_namespace(self): pass
        
        # Decorator should return the class itself
        assert MockProvider.__name__ == "MockProvider"
        # Should be able to instantiate
        instance = MockProvider("test", 900)
        assert instance.namespace == "test"
        assert instance.default_ttl == 900


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
