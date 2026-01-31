# Redis Cache Service

## Overview

The `RedisCacheService` is a **generic, reusable service** for storing temporary/cached data in Redis across the entire application. It provides a consistent, high-level API for common caching patterns while leveraging your existing Redis connection infrastructure.

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
│                    ┌───────▼────────┐                        │
│                    │ RedisCacheService│                      │
│                    │   (Generic)      │                      │
│                    └───────┬──────────┘                      │
│                            │                                 │
│                    ┌───────▼──────────┐                      │
│                    │RedisConnectionMgr│                      │
│                    └───────┬──────────┘                      │
└────────────────────────────┼──────────────────────────────────┘
                             │
                      ┌──────▼───────┐
                      │ Redis Server │
                      └──────────────┘
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
from app.services.redis_cache_service import RedisCacheService

# Create a cache instance for your feature
cache = RedisCacheService(namespace="myfeature", default_ttl=600)

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
rate_limit_cache = RedisCacheService("ratelimit", default_ttl=60)

# Increment counter
count = await rate_limit_cache.increment(f"api:{user_id}")
if count > 100:
    raise RateLimitError("Too many requests")
```

## Predefined Cache Instances

For convenience, common cache instances are pre-configured:

```python
from app.services.redis_cache_service import (
    confirmation_cache,  # 15-minute TTL
    signup_cache,        # 5-minute TTL  
    session_cache,       # 30-minute TTL
    rate_limit_cache     # 1-minute TTL
)

# Use directly
await confirmation_cache.set("action_123", data)
await signup_cache.set("session_456", data)
```

## Migration Guide

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
from app.services.redis_cache_service import signup_cache

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
from app.services.redis_cache_service import confirmation_cache

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
RedisCacheService(namespace: str, default_ttl: int = 900)
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

### vs. Direct Redis Access
- **DRY** - reuse existing ConnectionManager
- **Consistent API** across features
- **Automatic serialization** - no manual JSON handling
- **Namespace isolation** - no key collisions
- **Built-in indexing** - easy secondary lookups

### vs. Custom Repositories
- **Less boilerplate** - no custom class needed
- **Standardized** - same API everywhere
- **Tested** - one well-tested implementation
- **Maintainable** - one place to add features

## Testing

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.redis_cache_service import RedisCacheService

@pytest.fixture
def mock_redis():
    with patch('app.services.redis_cache_service.ConnectionFactory') as mock:
        redis_mock = AsyncMock()
        mock.get_connection_manager.return_value = redis_mock
        yield redis_mock

async def test_set_and_get(mock_redis):
    cache = RedisCacheService("test", default_ttl=60)
    
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value='{"key": "value"}')
    
    await cache.set("test_key", {"key": "value"})
    result = await cache.get("test_key")
    
    assert result == {"key": "value"}
    mock_redis.set.assert_called_once()
```

## Configuration

Redis connection is configured in `resources/application-db.yaml`:

```yaml
redis:
  host: "${REDIS_HOST:localhost}"
  port: "${REDIS_PORT:6379}"
  password: "${REDIS_PASSWORD}"
  database: "${REDIS_DB:0}"
  max_connections: 10
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

3. **Batch Operations**: For multiple items, consider using pipelines
   - Future enhancement: `set_many()`, `get_many()`

## Future Enhancements

- [ ] Redis pipeline support for batch operations
- [ ] Key expiration callbacks/webhooks
- [ ] Compression for large values
- [ ] Distributed locking support
- [ ] Redis pub/sub integration
- [ ] Metrics and monitoring hooks

## Related Files

- Service: `src/app/services/redis_cache_service.py`
- Connection: `src/app/connections/database/redis_connection_manager.py`
- Config: `resources/application-db.yaml`
- Tests: `tests/unit/services/test_redis_cache_service.py` (to be created)
