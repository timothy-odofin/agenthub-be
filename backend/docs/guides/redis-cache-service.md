# Cache Service Guide

## Overview

The **CacheService** is a unified, factory-based caching service for storing temporary/cached data across the entire application. It provides a consistent, high-level API for common caching patterns while leveraging the infrastructure layer's cache providers (Redis, In-Memory).

> **📝 Note**: This replaces the deprecated `RedisCacheService`. The new implementation uses a factory pattern for better flexibility and testability.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Confirmation │  │    Signup    │  │   Sessions   │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│              ┌─────────────▼─────────────┐                   │
│              │ Pre-configured Instances  │                   │
│              │ (confirmation_cache, etc) │                   │
│              └─────────────┬─────────────┘                   │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  CacheService   │                       │
│                    │   (Wrapper)     │                       │
│                    └───────┬─────────┘                       │
│                            │                                 │
│                    ┌───────▼──────────┐                      │
│                    │  CacheFactory    │                      │
│                    └───────┬──────────┘                      │
│                            │                                 │
│              ┌─────────────┴─────────────┐                   │
│              │                           │                   │
│      ┌───────▼──────────┐    ┌──────────▼─────────┐         │
│      │ RedisCacheProvider│    │InMemoryCacheProvider│        │
│      └───────┬──────────┘    └──────────┬─────────┘         │
└──────────────┼────────────────────────────┼──────────────────┘
               │                            │
        ┌──────▼───────┐           ┌───────▼────────┐
        │ Redis Server │           │ Local Memory   │
        └──────────────┘           └────────────────┘
```

## Key Features

### 1. **Namespace Isolation**
Each service instance operates in its own namespace, preventing key collisions:
- `confirmation:action_123`
- `signup:session_456`
- `session:user_789`

### 2. **Automatic TTL Management**
All data has automatic expiration (no manual cleanup needed):
- Default TTL per namespace
- Custom TTL per item
- TTL refresh on updates

### 3. **Secondary Indexing**
Track items by multiple criteria (user, session, etc.):
```python
await cache.set(
    "action_123",
    {"user": "alice", "data": "..."},
    indexes={"user": "alice", "session": "sess_456"}
)

# Later, retrieve all actions for user
actions = await cache.get_by_index("user", "alice")
```

### 4. **JSON Serialization**
Automatic JSON serialization/deserialization:
```python
await cache.set("key", {"complex": "object"})  # Auto-serialized
data = await cache.get("key")  # Auto-deserialized dict
```

### 5. **Async/Await Support**
All operations are async, matching your codebase pattern.

## Usage Examples

### Basic Operations

```python
from app.infrastructure.cache import CacheService

# Create a cache instance for your feature
cache = CacheService(namespace="myfeature", default_ttl=600)

# Store data
await cache.set("item_123", {"name": "Alice", "status": "active"})

# Retrieve data
item = await cache.get("item_123")
print(item["name"])  # "Alice"

# Check existence
if await cache.exists("item_123"):
    print("Item exists")

# Delete data
await cache.delete("item_123")
```

### With Secondary Indexes

```python
# Store with user index
await cache.set(
    "action_123",
    {"action": "create_issue", "project": "PROJ"},
    indexes={"user": "alice"}
)

await cache.set(
    "action_456",
    {"action": "update_file", "repo": "myrepo"},
    indexes={"user": "alice"}
)

# Retrieve all items for user
user_actions = await cache.get_by_index("user", "alice")
print(f"Alice has {len(user_actions)} pending actions")

# Delete with index cleanup
await cache.delete("action_123", indexes={"user": "alice"})
```

### Partial Updates

```python
# Update specific fields without retrieving entire object
await cache.update("action_123", {
    "status": "confirmed",
    "confirmed_at": datetime.utcnow().isoformat()
})
```

### TTL Management

```python
# Set custom TTL when storing
await cache.set("temp_token", "abc123", ttl=60)  # 1 minute

# Extend TTL of existing item
await cache.set_ttl("action_123", 1800)  # Extend to 30 minutes

# Check remaining TTL
ttl = await cache.get_ttl("action_123")
print(f"Expires in {ttl} seconds")
```

### Counters & Rate Limiting

```python
from app.infrastructure.cache import CacheService

rate_limit_cache = CacheService("ratelimit", default_ttl=60)

# Increment counter
count = await rate_limit_cache.increment(f"api:{user_id}")
if count > 100:
    raise RateLimitError("Too many requests")
```

## Predefined Cache Instances

For convenience, common cache instances are pre-configured:

```python
from app.infrastructure.cache.instances import (
    confirmation_cache,  # Namespace: 'confirmation', TTL: 300s (5 min)
    signup_cache,        # Namespace: 'signup', TTL: 1800s (30 min)
    session_cache,       # Namespace: 'session', TTL: 86400s (24 hrs)
    rate_limit_cache,    # Namespace: 'rate_limit', TTL: 3600s (1 hr)
    temp_cache          # Namespace: 'temp', TTL: 60s (1 min)
)

# Use directly
await confirmation_cache.set("action_123", data)
await signup_cache.set("session_456", data)
```

## Migration Guide

### From Old RedisCacheService (Deprecated)

If you were using the old `RedisCacheService` from `app.services.redis_cache_service`:

**Before:**
```python
from app.services.redis_cache_service import RedisCacheService

cache = RedisCacheService(namespace="myfeature", default_ttl=600)
```

**After:**
```python
from app.infrastructure.cache import CacheService

cache = CacheService(namespace="myfeature", default_ttl=600)
```

The API remains the same - only the import path changed!

### Replacing SignupSessionRepository

**Before:**
```python
class SignupSessionRepository:
    KEY_PREFIX = "signup"
    SESSION_TTL = 300
    
    async def create_session(self, session_id: str, data: dict):
        key = f"{self.KEY_PREFIX}:{session_id}"
        await self.redis.set(key, json.dumps(data), ex=self.SESSION_TTL)
    
    async def get_session(self, session_id: str):
        key = f"{self.KEY_PREFIX}:{session_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
```

**After:**
```python
from app.infrastructure.cache.instances import signup_cache

# Much simpler!
await signup_cache.set(session_id, data)
data = await signup_cache.get(session_id)
```

### Replacing PendingActionsStore

**Before:**
```python
class PendingActionsStore:
    def __init__(self):
        self._store = {}  # In-memory dict
        self._lock = threading.Lock()
        # Manual cleanup thread...
```

**After:**
```python
from app.infrastructure.cache.instances import confirmation_cache

# Redis-backed with automatic TTL
await confirmation_cache.set(
    action_id,
    action_data,
    indexes={"user": user_id}
)

# Get all actions for user
actions = await confirmation_cache.get_by_index("user", user_id)
```

## API Reference

### Constructor

```python
CacheService(namespace: str, default_ttl: int = 900, cache_type: Optional[CacheType] = None)
```

### Core Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `set(key, value, ttl=None, indexes=None)` | Store value with optional TTL and indexes | `bool` |
| `get(key, deserialize=True)` | Retrieve value | `Any | None` |
| `delete(key, indexes=None)` | Delete value and clean up indexes | `bool` |
| `exists(key)` | Check if key exists | `bool` |
| `update(key, updates, ttl=None)` | Update fields in stored dict | `bool` |

### Index Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `get_by_index(index_name, index_value)` | Get all items matching index | `List[Any]` |
| `get_keys_by_index(index_name, index_value)` | Get keys matching index | `Set[str]` |

### TTL Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `set_ttl(key, ttl)` | Update TTL | `bool` |
| `get_ttl(key)` | Get remaining TTL | `int | None` |

### Utility Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `increment(key, amount=1, ttl=None)` | Increment counter | `int | None` |
| `clear_namespace()` | Delete all keys in namespace | `int` |

## Benefits

### vs. In-Memory Storage
- **Persistent** across server restarts (until TTL)
- **Scalable** - works in multi-instance deployments
- **Automatic cleanup** via Redis TTL
- **No memory leaks** - Redis manages memory
- **Fallback support** - Can use InMemoryCacheProvider when Redis unavailable

### vs. Direct Redis Access
- **DRY** - reuse existing infrastructure
- **Consistent API** across features
- **Automatic serialization** - no manual JSON handling
- **Namespace isolation** - no key collisions
- **Built-in indexing** - easy secondary lookups
- **Provider flexibility** - Switch between Redis/Memory via factory

### vs. Custom Repositories
- **Less boilerplate** - no custom class needed
- **Standardized** - same API everywhere
- **Tested** - one well-tested implementation
- **Maintainable** - one place to add features
- **Factory pattern** - Easy to test and mock

## Testing

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.infrastructure.cache import CacheService
from app.infrastructure.cache import CacheType

@pytest.fixture
def mock_cache_provider():
    with patch('app.infrastructure.cache.CacheFactory.create_cache') as mock:
        cache_mock = AsyncMock()
        mock.return_value = cache_mock
        yield cache_mock

async def test_set_and_get(mock_cache_provider):
    cache = CacheService("test", default_ttl=60)
    
    mock_cache_provider.set = AsyncMock(return_value=True)
    mock_cache_provider.get = AsyncMock(return_value={"key": "value"})
    
    await cache.set("test_key", {"key": "value"})
    result = await cache.get("test_key")
    
    assert result == {"key": "value"}
    mock_cache_provider.set.assert_called_once()

async def test_with_in_memory_cache():
    """Test with in-memory provider for unit tests"""
    cache = CacheService("test", default_ttl=60, cache_type=CacheType.IN_MEMORY)
    
    await cache.set("test_key", {"key": "value"})
    result = await cache.get("test_key")
    
    assert result == {"key": "value"}
```

## Configuration

Cache providers are configured in `resources/application-cache.yaml`:

```yaml
cache:
  default_provider: redis  # or 'in_memory' for development
  
  redis:
    enabled: true
    namespace_prefix: "agenthub"
    default_ttl: 900
    serializer: "json"
  
  in_memory:
    enabled: true
    max_size: 1000
    cleanup_interval: 60
```

Redis connection itself is configured in `resources/application-db.yaml`:

```yaml
redis:
  host: "${REDIS_HOST:localhost}"
  port: "${REDIS_PORT:6379}"
  password: "${REDIS_PASSWORD}"
  database: "${REDIS_DB:0}"
  connection_pool_size: 10
  socket_timeout: 30
```

## Performance Considerations

1. **TTL Selection**: Balance between performance and freshness
   - Short TTL (< 5 min): Frequently updated data
   - Medium TTL (5-30 min): User sessions, confirmations
   - Long TTL (> 30 min): Rarely changing data

2. **Indexing**: Only index fields you'll query by
   - Each index adds overhead to writes
   - But makes reads much faster

3. **Provider Selection**: Choose the right provider for your use case
   - **Redis**: Production, distributed systems, persistence
   - **InMemory**: Development, testing, single-instance apps

4. **Batch Operations**: For multiple items, consider using pipelines
   - Future enhancement: `set_many()`, `get_many()`

## Architecture Benefits

The new infrastructure-based cache system provides:

1. **Factory Pattern**: Easy to swap providers (Redis ↔ InMemory)
2. **Registry Pattern**: Automatic provider discovery
3. **Dependency Injection**: Better testability
4. **Separation of Concerns**: Infrastructure layer isolated from business logic
5. **Extensibility**: Easy to add new cache providers (Memcached, etc.)

## Future Enhancements

- [ ] Redis pipeline support for batch operations
- [ ] Key expiration callbacks/webhooks
- [ ] Compression for large values
- [ ] Distributed locking support
- [ ] Redis pub/sub integration
- [ ] Metrics and monitoring hooks
- [ ] Additional providers (Memcached, DynamoDB, etc.)

## Related Files

### Infrastructure Layer
- Service Wrapper: `src/app/infrastructure/cache/cache_service.py`
- Factory: `src/app/infrastructure/cache/cache_factory.py`
- Registry: `src/app/infrastructure/cache/cache_registry.py`
- Base Provider: `src/app/infrastructure/cache/base/base_cache_provider.py`
- Redis Provider: `src/app/infrastructure/cache/implementations/redis_cache.py`
- InMemory Provider: `src/app/infrastructure/cache/implementations/in_memory_cache.py`
- Pre-configured Instances: `src/app/infrastructure/cache/instances.py`

### Tests
- Tests: `tests/unit/infrastructure/cache/` (recommended location)
- Connection: `src/app/connections/database/redis_connection_manager.py`
- Config: `resources/application-db.yaml`
- Tests: `tests/unit/services/test_redis_cache_service.py` (to be created)
