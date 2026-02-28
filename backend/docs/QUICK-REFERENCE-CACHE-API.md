# Quick Reference: Cache Management API

## Overview
Three-layer caching system for performance optimization. All caches are in-memory and cleared on application restart.

---

## Connection Manager Cache

### Get Connection Manager (Auto-Cached)
```python
from app.infrastructure.connections.factory.connection_factory import ConnectionFactory
from app.infrastructure.connections.connection_type import ConnectionType

# First call: Creates and caches
manager = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)

# Subsequent calls: Returns cached instance
manager = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)
```

### Clear Cache
```python
# Clear all connection managers
ConnectionFactory.clear_cache()

# Clear specific type
ConnectionFactory.clear_cache(ConnectionType.MONGODB)
ConnectionFactory.clear_cache(ConnectionType.REDIS)
ConnectionFactory.clear_cache(ConnectionType.JIRA)
```

**When to Clear:**
- After config changes
- During testing (between test cases)
- When troubleshooting connection issues

---

## Tool Registry Cache

### Get Tools (Auto-Cached)
```python
from app.agent.tools.base.registry import ToolRegistry

# First call: Loads and caches all tools
tools = ToolRegistry.get_instantiated_tools()

# Subsequent calls: Returns from cache
tools = ToolRegistry.get_instantiated_tools()

# Force fresh load (bypass cache)
tools = ToolRegistry.get_instantiated_tools(use_cache=False)

# Get specific category (cached separately)
jira_tools = ToolRegistry.get_instantiated_tools(category='jira')
github_tools = ToolRegistry.get_instantiated_tools(category='github')
```

### Clear Cache
```python
# Clear all tool caches
ToolRegistry.clear_tool_cache()

# Clear specific category
ToolRegistry.clear_tool_cache('jira')
ToolRegistry.clear_tool_cache('github')
```

### Enable/Disable Caching
```python
# Disable caching (useful for testing)
ToolRegistry.set_cache_enabled(False)

# Re-enable caching
ToolRegistry.set_cache_enabled(True)
```

### Get Statistics
```python
stats = ToolRegistry.get_cache_stats()
print(stats)
# {
#     'cache_enabled': True,
#     'cached_categories': ['category:all', 'category:jira'],
#     'total_cached_tools': 92,
#     'cache_size_bytes': 245760
# }
```

**When to Clear:**
- After tool configuration changes
- During development (testing new tools)
- When troubleshooting tool issues

---

## GitHub Repository Cache

### Discover Repositories (Auto-Cached, 10-min TTL)
```python
from app.agent.tools.github.connection_manager import GitHubConnectionManager

# Create manager instance
manager = GitHubConnectionManager()

# First call: GitHub API discovery (16-19s)
repos = manager.discover_accessible_repositories()

# Subsequent calls within 10 minutes: From cache (<100ms)
repos = manager.discover_accessible_repositories()

# After 10 minutes: Cache expires, re-fetches from GitHub
```

### Clear Cache
```python
# Clear all installations
GitHubConnectionManager.clear_repo_cache()

# Clear specific installation
GitHubConnectionManager.clear_repo_cache('101772652')
```

### Get Statistics
```python
stats = GitHubConnectionManager.get_cache_stats()
print(stats)
# {
#     'cached_installations': 1,
#     'cache_ttl_seconds': 600,
#     'entries': [
#         {
#             'installation_id': '101772652',
#             'repo_count': 22,
#             'cached_at': '2026-02-25T19:22:26',
#             'age_seconds': 142.5,
#             'expired': False
#         }
#     ]
# }
```

**When to Clear:**
- After installing/uninstalling GitHub App
- After adding/removing repository access
- When troubleshooting repository discovery issues

---

## Testing Utilities

### Disable All Caching for Tests
```python
import pytest
from app.agent.tools.base.registry import ToolRegistry
from app.infrastructure.connections.factory.connection_factory import ConnectionFactory
from app.agent.tools.github.connection_manager import GitHubConnectionManager

@pytest.fixture(autouse=True)
def clear_all_caches():
    """Clear all caches before each test."""
    # Disable tool caching
    ToolRegistry.set_cache_enabled(False)

    # Clear existing caches
    ConnectionFactory.clear_cache()
    ToolRegistry.clear_tool_cache()
    GitHubConnectionManager.clear_repo_cache()

    yield

    # Re-enable caching after test
    ToolRegistry.set_cache_enabled(True)
```

### Force Fresh Initialization
```python
# Force fresh tools (bypass cache)
tools = ToolRegistry.get_instantiated_tools(use_cache=False)

# Connection managers always use cache (no bypass option)
# To force fresh, clear cache first:
ConnectionFactory.clear_cache(ConnectionType.MONGODB)
manager = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)
```

---

## Cache Warming (Optional)

Pre-populate caches on application startup:

```python
# In app startup/initialization code
from app.infrastructure.connections.factory.connection_factory import ConnectionFactory
from app.infrastructure.connections.connection_type import ConnectionType
from app.agent.tools.base.registry import ToolRegistry
import logging

logger = logging.getLogger(__name__)

def warm_caches():
    """Warm up caches on application startup."""
    logger.info("Warming up caches...")

    # Warm connection managers
    ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)
    ConnectionFactory.get_connection_manager(ConnectionType.REDIS)

    # Warm tool registry (most expensive)
    ToolRegistry.get_instantiated_tools()

    logger.info("✅ Caches warmed successfully")
```

---

## Performance Monitoring

### Log Messages to Watch

**Cache Hits (Good):**
```
✅ Reusing cached connection manager: ConnectionType.MONGODB
✅ Loaded 84 tools from cache (saved ~20-30s initialization time)
✅ Loaded 22 repositories from cache (age: 45.2s, saved ~16-19s GitHub API time)
```

**Cache Misses (Expected on first request):**
```
Created and cached connection manager: ConnectionType.MONGODB
Cache miss - loading tools from scratch for 'category:all'
Discovering accessible repositories from GitHub API...
```

**Cache Expiry:**
```
Cache expired (age: 612.3s > 600s), refreshing GitHub repositories...
```

### Metrics to Track

- **Cache hit rate:** Should be >95% after warmup
- **Tool loading time:** <500ms from cache vs 20-30s cold
- **GitHub API calls:** <1 per 10 minutes per installation
- **Request duration:** <5s with warm cache vs 50-75s without

---

## Troubleshooting

### "Stale data in cache"
```python
# Clear specific cache
ToolRegistry.clear_tool_cache('github')
GitHubConnectionManager.clear_repo_cache('101772652')
```

### "Cache not working"
```python
# Check if caching is enabled
stats = ToolRegistry.get_cache_stats()
if not stats['cache_enabled']:
    ToolRegistry.set_cache_enabled(True)

# Check cache stats
print(ToolRegistry.get_cache_stats())
print(GitHubConnectionManager.get_cache_stats())
```

### "Connection issues"
```python
# Clear and recreate connection managers
ConnectionFactory.clear_cache()
manager = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)
```

### "Need fresh data for debugging"
```python
# Bypass all caches
ToolRegistry.set_cache_enabled(False)
ConnectionFactory.clear_cache()
GitHubConnectionManager.clear_repo_cache()

# Get fresh instances
tools = ToolRegistry.get_instantiated_tools(use_cache=False)
manager = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)

# Re-enable caching
ToolRegistry.set_cache_enabled(True)
```

---

## Production Considerations

### Cache Persistence

**Current:** In-memory (cleared on restart)
**Upgrade Path:** Use Redis for persistence across restarts

```python
# Future: Redis-backed cache
from app.infrastructure.cache.redis_cache_provider import RedisCacheProvider
tool_cache = RedisCacheProvider(namespace="tools", ttl_seconds=3600)
```

### Distributed Systems

If running multiple application instances:
- Each instance has separate in-memory cache
- First request per instance warms cache
- Consider Redis for shared cache across instances

### Cache Invalidation Strategy

**Development:** Manual clearing via API
**Production:**
- GitHub repos: 10-minute TTL (automatic)
- Tools: Manual clearing on deployment
- Connections: Persist until restart

---

## Related Documentation

- [Optimization Overview](./architecture/OPTIMIZATION-2026-02-25.md)
- [Cache Service Design](./architecture/cache-service-design-comparison.md)
- [Redis Cache Service Guide](./guides/redis-cache-service.md)

---

**Last Updated:** February 25, 2026
**Status:** Production Ready
