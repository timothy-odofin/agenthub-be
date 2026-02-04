"""
Unit tests for RedisCacheProvider.

Tests the Redis cache implementation including all operations,
TTL handling, index operations, JSON serialization, and error handling.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.cache.implementations.redis_cache import RedisCacheProvider
from app.core.exceptions import CacheError


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    
    # Mock storage for testing
    mock._storage = {}
    mock._ttls = {}
    mock._indexes = {}
    
    # Mock set method
    async def mock_set(key, value, ex=None):
        mock._storage[key] = value
        if ex:
            mock._ttls[key] = ex
        return True
    
    # Mock get method
    async def mock_get(key):
        return mock._storage.get(key)
    
    # Mock delete method
    async def mock_delete(key):
        if key in mock._storage:
            del mock._storage[key]
            return 1
        return 0
    
    # Mock exists method
    async def mock_exists(key):
        return 1 if key in mock._storage else 0
    
    # Mock ttl method
    async def mock_ttl(key):
        return mock._ttls.get(key, -1)
    
    # Mock expire method
    async def mock_expire(key, seconds):
        if key in mock._storage:
            mock._ttls[key] = seconds
            return 1
        return 0
    
    # Mock keys method
    async def mock_keys(pattern):
        matching = [k for k in mock._storage.keys() if pattern.replace('*', '') in k]
        return matching
    
    # Mock sadd method
    async def mock_sadd(key, *values):
        if key not in mock._indexes:
            mock._indexes[key] = set()
        mock._indexes[key].update(values)
        return len(values)
    
    # Mock smembers method
    async def mock_smembers(key):
        return mock._indexes.get(key, set())
    
    # Mock srem method
    async def mock_srem(key, *values):
        if key in mock._indexes:
            removed = len(mock._indexes[key].intersection(values))
            mock._indexes[key].difference_update(values)
            return removed
        return 0
    
    # Mock incr method
    async def mock_incr(key):
        current = mock._storage.get(key)
        if current is None:
            mock._storage[key] = '1'
            return 1
        try:
            value = int(current) + 1
            mock._storage[key] = str(value)
            return value
        except (ValueError, TypeError):
            raise Exception("value is not an integer")
    
    # Mock incrby method
    async def mock_incrby(key, amount):
        current = mock._storage.get(key)
        if current is None:
            mock._storage[key] = str(amount)
            return amount
        try:
            value = int(current) + amount
            mock._storage[key] = str(value)
            return value
        except (ValueError, TypeError):
            raise Exception("value is not an integer")
    
    mock.set = mock_set
    mock.get = mock_get
    mock.delete = mock_delete
    mock.exists = mock_exists
    mock.ttl = mock_ttl
    mock.expire = mock_expire
    mock.keys = mock_keys
    mock.sadd = mock_sadd
    mock.smembers = mock_smembers
    mock.srem = mock_srem
    mock.incr = mock_incr
    mock.incrby = mock_incrby
    
    return mock


@pytest.fixture
def cache(mock_redis):
    """Create a Redis cache instance with mocked Redis client."""
    cache_instance = RedisCacheProvider(namespace="test", default_ttl=60)
    cache_instance.client = mock_redis
    return cache_instance


class TestRedisCacheBasicOperations:
    """Test basic cache operations."""
    
    @pytest.mark.asyncio
    async def test_set_and_get_string(self, cache):
        """Test setting and getting a string value."""
        result = await cache.set("key1", "value1")
        assert result is True
        
        value = await cache.get("key1")
        assert value == "value1"
    
    @pytest.mark.asyncio
    async def test_set_and_get_dict(self, cache):
        """Test setting and getting a dictionary."""
        data = {"name": "John", "age": 30}
        result = await cache.set("user", data)
        assert result is True
        
        value = await cache.get("user")
        assert value == data
    
    @pytest.mark.asyncio
    async def test_set_and_get_list(self, cache):
        """Test setting and getting a list."""
        data = [1, 2, 3, 4, 5]
        result = await cache.set("numbers", data)
        assert result is True
        
        value = await cache.get("numbers")
        assert value == data
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache):
        """Test getting a key that doesn't exist."""
        value = await cache.get("nonexistent")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_get_with_deserialize_false(self, cache):
        """Test getting raw string without deserialization."""
        data = {"key": "value"}
        await cache.set("json_data", data)
        
        raw_value = await cache.get("json_data", deserialize=False)
        assert isinstance(raw_value, str)
        assert json.loads(raw_value) == data
    
    @pytest.mark.asyncio
    async def test_exists_returns_true(self, cache):
        """Test exists returns True for existing key."""
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
    
    @pytest.mark.asyncio
    async def test_exists_returns_false(self, cache):
        """Test exists returns False for non-existing key."""
        assert await cache.exists("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_delete_existing_key(self, cache):
        """Test deleting an existing key."""
        await cache.set("key1", "value1")
        result = await cache.delete("key1")
        assert result is True
        assert await cache.exists("key1") is False
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache):
        """Test deleting a non-existing key."""
        result = await cache.delete("nonexistent")
        assert result is False


class TestRedisCacheTTL:
    """Test TTL functionality."""
    
    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache):
        """Test setting a value with custom TTL."""
        result = await cache.set("key1", "value1", ttl=120)
        assert result is True
        
        ttl = await cache.get_ttl("key1")
        assert ttl == 120
    
    @pytest.mark.asyncio
    async def test_set_with_default_ttl(self, cache):
        """Test setting a value with default TTL."""
        await cache.set("key1", "value1")
        
        ttl = await cache.get_ttl("key1")
        assert ttl == 60
    
    @pytest.mark.asyncio
    async def test_set_ttl_on_existing_key(self, cache):
        """Test updating TTL on existing key."""
        await cache.set("key1", "value1", ttl=60)
        result = await cache.set_ttl("key1", 120)
        assert result is True
        
        ttl = await cache.get_ttl("key1")
        assert ttl == 120
    
    @pytest.mark.asyncio
    async def test_set_ttl_on_nonexistent_key(self, cache):
        """Test setting TTL on non-existing key."""
        result = await cache.set_ttl("nonexistent", 120)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_ttl_returns_none_for_nonexistent_key(self, cache):
        """Test getting TTL for non-existing key."""
        ttl = await cache.get_ttl("nonexistent")
        assert ttl is None


class TestRedisCacheIndexOperations:
    """Test index-based operations."""
    
    @pytest.mark.asyncio
    async def test_set_with_single_index(self, cache):
        """Test setting a value with a single index."""
        indexes = {"user_id": "123"}
        data = {"data": "value"}
        await cache.set("session:abc", data, indexes=indexes)
        
        # Retrieve by index - returns values, not keys
        items = await cache.get_by_index("user_id", "123")
        assert data in items
    
    @pytest.mark.asyncio
    async def test_set_with_multiple_indexes(self, cache):
        """Test setting a value with multiple indexes."""
        indexes = {"user_id": "123", "session_type": "web"}
        data = {"data": "value"}
        await cache.set("session:abc", data, indexes=indexes)
        
        # Retrieve by first index - returns values, not keys
        items1 = await cache.get_by_index("user_id", "123")
        assert data in items1
        
        # Retrieve by second index - returns values, not keys
        items2 = await cache.get_by_index("session_type", "web")
        assert data in items2
    
    @pytest.mark.asyncio
    async def test_get_by_index_returns_empty_list(self, cache):
        """Test getting by non-existing index."""
        keys = await cache.get_by_index("user_id", "999")
        assert keys == []
    
    @pytest.mark.asyncio
    async def test_get_keys_by_index(self, cache):
        """Test getting keys set by index."""
        indexes = {"user_id": "123"}
        await cache.set("session:1", {"data": "value1"}, indexes=indexes)
        await cache.set("session:2", {"data": "value2"}, indexes=indexes)
        
        keys = await cache.get_keys_by_index("user_id", "123")
        assert isinstance(keys, set)
        assert "session:1" in keys
        assert "session:2" in keys
    
    @pytest.mark.asyncio
    async def test_delete_removes_from_indexes(self, cache):
        """Test that deleting a key removes it from indexes."""
        indexes = {"user_id": "123"}
        data = {"data": "value"}
        await cache.set("session:abc", data, indexes=indexes)
        
        # Verify it's in the index - returns values
        items_before = await cache.get_by_index("user_id", "123")
        assert data in items_before
        
        # Delete the key with indexes
        await cache.delete("session:abc", indexes=indexes)
        
        # Should be removed from index
        items_after = await cache.get_by_index("user_id", "123")
        assert data not in items_after


class TestRedisCacheUpdate:
    """Test update operations."""
    
    @pytest.mark.asyncio
    async def test_update_existing_dict(self, cache):
        """Test updating an existing dictionary."""
        original = {"name": "John", "age": 30}
        await cache.set("user", original)
        
        updates = {"age": 31, "city": "NYC"}
        result = await cache.update("user", updates)
        assert result is True
        
        updated = await cache.get("user")
        assert updated["name"] == "John"
        assert updated["age"] == 31
        assert updated["city"] == "NYC"
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_key(self, cache):
        """Test updating a non-existing key."""
        result = await cache.update("nonexistent", {"key": "value"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_non_dict_value(self, cache):
        """Test updating a non-dictionary value."""
        await cache.set("key1", "string_value")
        
        result = await cache.update("key1", {"key": "value"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_with_custom_ttl(self, cache):
        """Test updating with custom TTL."""
        await cache.set("user", {"name": "John"}, ttl=60)
        
        result = await cache.update("user", {"age": 30}, ttl=120)
        assert result is True
        
        ttl = await cache.get_ttl("user")
        assert ttl == 120


class TestRedisCacheIncrement:
    """Test increment operations."""
    
    @pytest.mark.asyncio
    async def test_increment_new_key(self, cache):
        """Test incrementing a new key."""
        # Use unique key to avoid interference from other tests
        unique_key = "counter_new_unique"
        result = await cache.increment(unique_key)
        assert result == 1
        
        value = await cache.get(unique_key)
        assert value == 1
    
    @pytest.mark.asyncio
    async def test_increment_existing_key(self, cache):
        """Test incrementing an existing key."""
        await cache.set("counter", 5)
        
        result = await cache.increment("counter")
        assert result == 6
        
        value = await cache.get("counter")
        assert value == 6
    
    @pytest.mark.asyncio
    async def test_increment_by_custom_amount(self, cache):
        """Test incrementing by custom amount."""
        await cache.set("counter", 10)
        
        result = await cache.increment("counter", amount=5)
        assert result == 15
    
    @pytest.mark.asyncio
    async def test_increment_with_ttl(self, cache, mock_redis):
        """Test incrementing with TTL."""
        # Reset storage to ensure clean state
        mock_redis._storage.clear()
        mock_redis._ttls.clear()
        
        unique_key = "counter_ttl_unique_2"
        result = await cache.increment(unique_key, ttl=120)
        assert result == 1
        
        ttl = await cache.get_ttl(unique_key)
        assert ttl == 120
    
    @pytest.mark.asyncio
    async def test_increment_non_numeric_value(self, cache):
        """Test incrementing a non-numeric value."""
        await cache.set("key1", "string_value")
        
        result = await cache.increment("key1")
        assert result is None


class TestRedisCacheClearNamespace:
    """Test namespace clearing."""
    
    @pytest.mark.asyncio
    async def test_clear_namespace(self):
        """Test clearing all keys in namespace."""
        # Use a unique cache instance to avoid interference
        cache_instance = RedisCacheProvider(namespace="test_clear", default_ttl=60)
        
        await cache_instance.set("key1", "value1")
        await cache_instance.set("key2", "value2")
        await cache_instance.set("key3", "value3")
        
        count = await cache_instance.clear_namespace()
        assert count == 3
        
        # Verify keys are deleted
        assert await cache_instance.exists("key1") is False
        assert await cache_instance.exists("key2") is False
        assert await cache_instance.exists("key3") is False
    
    @pytest.mark.asyncio
    async def test_clear_empty_namespace(self):
        """Test clearing an empty namespace."""
        # Use a unique cache instance to avoid interference
        cache_instance = RedisCacheProvider(namespace="test_empty_clear", default_ttl=60)
        
        count = await cache_instance.clear_namespace()
        assert count == 0


class TestRedisCacheJSONSerialization:
    """Test JSON serialization and deserialization."""
    
    @pytest.mark.asyncio
    async def test_serialize_complex_object(self, cache):
        """Test serializing complex nested object."""
        data = {
            "user": {
                "name": "John",
                "address": {
                    "street": "123 Main St",
                    "city": "NYC"
                },
                "tags": ["developer", "python"]
            },
            "timestamp": "2025-01-01T00:00:00"
        }
        
        await cache.set("complex", data)
        result = await cache.get("complex")
        assert result == data
    
    @pytest.mark.asyncio
    async def test_serialize_datetime(self, cache):
        """Test that datetime objects are serialized properly."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "value": "test"
        }
        
        await cache.set("with_datetime", data)
        result = await cache.get("with_datetime")
        assert result["timestamp"] == data["timestamp"]
    
    @pytest.mark.asyncio
    async def test_deserialize_invalid_json(self, cache, mock_redis):
        """Test handling of invalid JSON."""
        # Set invalid JSON directly
        await mock_redis.set("test:invalid", "not valid json {")
        
        # Should return None on deserialization error
        result = await cache.get("invalid")
        assert result is None


class TestRedisCacheErrorHandling:
    """Test error handling with decorator."""
    
    @pytest.mark.asyncio
    async def test_connection_error_returns_default(self, cache):
        """Test that connection errors return default values."""
        # Mock a connection error on the Redis client's get method
        async def mock_conn_error(*args, **kwargs):
            raise ConnectionError("Connection failed")
        
        cache.redis.get = mock_conn_error
        
        # Should return None (default) instead of raising
        result = await cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_timeout_error_returns_default(self, cache):
        """Test that timeout errors return default values."""
        # Mock a timeout error on the Redis client's set method
        async def mock_timeout(*args, **kwargs):
            raise TimeoutError("Operation timed out")
        
        cache.redis.set = mock_timeout
        
        # Should return False (default) instead of raising
        result = await cache.set("key1", "value1")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
