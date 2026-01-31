"""
Unit tests for CacheFactory.

Tests the cache provider factory system for creating cache instances.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.cache.cache_factory import CacheFactory
from app.services.cache.cache_registry import CacheRegistry
from app.services.cache.base_cache_provider import BaseCacheProvider
from app.core.enums import CacheType


class MockCacheProvider(BaseCacheProvider):
    """Mock cache provider for testing."""
    
    def __init__(self, namespace: str, default_ttl: int = 900):
        super().__init__(namespace, default_ttl)
        self.initialized = True
    
    async def set(self, key, value, ttl=None, indexes=None):
        return True
    
    async def get(self, key, deserialize=True):
        return None
    
    async def delete(self, key, indexes=None):
        return True
    
    async def exists(self, key):
        return False
    
    async def get_by_index(self, index_name, index_value):
        return []
    
    async def get_keys_by_index(self, index_name, index_value):
        return set()
    
    async def update(self, key, updates, ttl=None):
        return True
    
    async def set_ttl(self, key, ttl):
        return True
    
    async def get_ttl(self, key):
        return None
    
    async def increment(self, key, amount=1, ttl=None):
        return amount
    
    async def clear_namespace(self):
        return 0


class TestCacheFactory:
    """Test suite for CacheFactory."""
    
    def setup_method(self):
        """Register mock provider before each test."""
        CacheRegistry.clear_registry()
        CacheRegistry.register(CacheType.IN_MEMORY)(MockCacheProvider)
    
    def teardown_method(self):
        """Clear registry after each test."""
        CacheRegistry.clear_registry()
    
    def test_create_cache_with_explicit_type(self):
        """Test creating a cache with explicit cache type."""
        cache = CacheFactory.create_cache(
            namespace="test",
            cache_type=CacheType.IN_MEMORY,
            default_ttl=600
        )
        
        assert isinstance(cache, MockCacheProvider)
        assert cache.namespace == "test"
        assert cache.default_ttl == 600
        assert cache.initialized is True
    
    def test_create_cache_with_default_ttl(self):
        """Test creating a cache with default TTL."""
        cache = CacheFactory.create_cache(
            namespace="test",
            cache_type=CacheType.IN_MEMORY
        )
        
        assert cache.default_ttl == 900  # Default from CacheFactory
    
    def test_create_cache_with_custom_ttl(self):
        """Test creating a cache with custom TTL."""
        cache = CacheFactory.create_cache(
            namespace="custom_ttl",
            cache_type=CacheType.IN_MEMORY,
            default_ttl=1800
        )
        
        assert cache.default_ttl == 1800
    
    def test_create_cache_with_unregistered_type_raises_error(self):
        """Test that creating cache with unregistered type raises ValueError."""
        with pytest.raises(ValueError, match="not available"):
            CacheFactory.create_cache(
                namespace="test",
                cache_type=CacheType.MEMCACHED
            )
    
    def test_create_cache_with_invalid_namespace(self):
        """Test creating cache with empty namespace."""
        cache = CacheFactory.create_cache(
            namespace="",
            cache_type=CacheType.IN_MEMORY
        )
        
        # Should still create, namespace validation is in provider
        assert cache.namespace == ""
    
    def test_list_available_providers(self):
        """Test listing available cache providers."""
        # Register another provider
        @CacheRegistry.register(CacheType.REDIS)
        class AnotherProvider(MockCacheProvider):
            pass
        
        providers = CacheFactory.list_available_cache_providers()
        
        assert CacheType.IN_MEMORY in providers
        assert CacheType.REDIS in providers
        assert len(providers) == 2
    
    def test_list_available_providers_empty(self):
        """Test listing providers when none are registered."""
        CacheRegistry.clear_registry()
        
        providers = CacheFactory.list_available_cache_providers()
        assert providers == []
    
    def test_is_provider_available_true(self):
        """Test checking if a provider is available."""
        assert CacheFactory.is_cache_provider_available(CacheType.IN_MEMORY) is True
    
    def test_is_provider_available_false(self):
        """Test checking if unavailable provider."""
        assert CacheFactory.is_cache_provider_available(CacheType.MEMCACHED) is False
    
    def test_create_multiple_instances_with_different_namespaces(self):
        """Test creating multiple cache instances with different namespaces."""
        cache1 = CacheFactory.create_cache(
            namespace="namespace1",
            cache_type=CacheType.IN_MEMORY,
            default_ttl=300
        )
        
        cache2 = CacheFactory.create_cache(
            namespace="namespace2",
            cache_type=CacheType.IN_MEMORY,
            default_ttl=600
        )
        
        assert cache1.namespace == "namespace1"
        assert cache2.namespace == "namespace2"
        assert cache1.default_ttl == 300
        assert cache2.default_ttl == 600
        # Should be different instances
        assert cache1 is not cache2
    
    def test_create_cache_with_same_namespace_creates_new_instance(self):
        """Test that creating cache with same namespace creates new instance."""
        cache1 = CacheFactory.create_cache(
            namespace="duplicate",
            cache_type=CacheType.IN_MEMORY
        )
        
        cache2 = CacheFactory.create_cache(
            namespace="duplicate",
            cache_type=CacheType.IN_MEMORY
        )
        
        # Should be different instances (no singleton behavior in factory)
        assert cache1 is not cache2
        assert cache1.namespace == cache2.namespace
    
    def test_create_cache_with_none_cache_type_raises_error(self):
        """Test that None cache_type raises ValueError."""
        with pytest.raises(ValueError, match="not available"):
            CacheFactory.create_cache(
                namespace="test",
                cache_type=None
            )
    
    def test_create_cache_with_zero_ttl(self):
        """Test creating cache with zero TTL."""
        cache = CacheFactory.create_cache(
            namespace="zero_ttl",
            cache_type=CacheType.IN_MEMORY,
            default_ttl=0
        )
        
        assert cache.default_ttl == 0
    
    def test_create_cache_with_negative_ttl(self):
        """Test creating cache with negative TTL."""
        cache = CacheFactory.create_cache(
            namespace="negative_ttl",
            cache_type=CacheType.IN_MEMORY,
            default_ttl=-1
        )
        
        assert cache.default_ttl == -1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
