# Quick Reference: Using Object Cache

## Overview
The object cache stores Python object references (LLM providers, agents) that cannot be serialized to Redis.

## Import
```python
from app.infrastructure.cache.instances import agent_cache, llm_provider_cache
```

## Basic Usage

### Store Object
```python
# Store an agent
cache_key = f"{provider}:{model}"
await agent_cache.set(cache_key, agent_instance)

# Store an LLM provider
cache_key = f"{provider.value}"
await llm_provider_cache.set(cache_key, llm_instance)
```

### Retrieve Object
```python
# Get an agent
cache_key = f"{provider}:{model}"
agent = await agent_cache.get(cache_key)

if agent is not None:
    # Cache hit - use cached instance
    logger.info("Using cached agent")
else:
    # Cache miss - create new instance
    agent = await create_new_agent()
    await agent_cache.set(cache_key, agent)
```

### Delete Entry
```python
cache_key = f"{provider}:{model}"
await agent_cache.delete(cache_key)
```

### Clear Entire Cache
```python
await agent_cache.clear()
```

### Check Existence
```python
cache_key = f"{provider}:{model}"
exists = await agent_cache.exists(cache_key)
```

### Get Statistics
```python
stats = agent_cache.get_stats()
# Returns:
{
    'size': 8,              # Current number of entries
    'max_size': 50,         # Maximum capacity
    'hits': 156,            # Number of cache hits
    'misses': 8,            # Number of cache misses
    'hit_rate': '95.12%',   # Hit rate percentage
    'evictions': 2          # Number of LRU evictions
}
```

## Cache Key Patterns

### Agent Cache
```python
# Format: "{provider}:{model}"
cache_key = f"{provider or 'default'}:{model or 'default'}"

# Examples:
"openai:gpt-4"
"anthropic:claude-3-opus"
"default:default"
```

### LLM Provider Cache
```python
# Format: "{provider_value}"
cache_key = f"{provider.value}"

# Examples:
"openai"
"anthropic"
"groq"
```

## Complete Example

```python
from app.infrastructure.cache.instances import agent_cache
from app.infrastructure.llm.factory.llm_factory import LLMFactory
from app.agent import AgentFactory

async def get_or_create_agent(provider: str, model: str):
    """Get cached agent or create new one."""

    # Build cache key
    cache_key = f"{provider}:{model}"

    # Try cache first
    agent = await agent_cache.get(cache_key)

    if agent is not None:
        # Cache hit
        stats = agent_cache.get_stats()
        logger.info(
            f"✅ Cache hit for {cache_key} "
            f"(hit_rate: {stats.get('hit_rate', 'N/A')})"
        )
        return agent

    # Cache miss - create new agent
    logger.info(f"Cache miss for {cache_key}, creating new agent")

    # Get LLM instance (also cached)
    llm = await LLMFactory.get_llm_by_name(provider, model)

    # Create agent
    agent = await AgentFactory.create_agent(
        agent_type=AgentType.REACT,
        framework=AgentFramework.LANGCHAIN,
        llm_provider=llm,
        session_repository=session_repo,
        verbose=False
    )

    # Cache the agent
    await agent_cache.set(cache_key, agent)
    logger.info(f"Cached new agent for {cache_key}")

    return agent
```

## LLM Factory Integration

```python
from app.infrastructure.llm.factory.llm_factory import LLMFactory
from app.core.constants import LLMProvider

# Get LLM provider (automatically cached)
llm = await LLMFactory.get_llm(LLMProvider.OPENAI)

# Or by name
llm = await LLMFactory.get_llm_by_name("openai", "gpt-4")

# Get default LLM
llm = await LLMFactory.get_default_llm()
```

## Chat Service Integration

```python
from app.services.chat_service import ChatService

chat_service = ChatService()

# Chat with caching (automatic)
response = await chat_service.chat(
    message="Hello",
    user_id="user123",
    session_id="session456",
    provider="openai",
    model="gpt-4"
)

# Clear agent cache
await chat_service.clear_agent_cache()

# Clear specific provider
await chat_service.clear_agent_cache(provider="openai")

# Get cache statistics
stats = await chat_service.get_agent_cache_stats()
print(f"Hit rate: {stats['hit_rate']}")
```

## Configuration

### Create Custom Object Cache

```python
from app.infrastructure.cache import CacheFactory
from app.core.core_enums import CacheType

# Create custom object cache
my_cache = CacheFactory.create_cache(
    cache_type=CacheType.OBJECT,
    namespace="my_objects",
    default_ttl=None,  # No expiration
    max_size=100       # Store up to 100 objects
)

# Use it
await my_cache.set("key1", my_object)
obj = await my_cache.get("key1")
```

## Thread Safety

ObjectCacheProvider is thread-safe:
- Uses `threading.RLock` for all operations
- Safe for concurrent access from multiple threads
- No need for external locking

```python
# Safe to call from multiple threads/coroutines
await asyncio.gather(
    agent_cache.get("key1"),
    agent_cache.get("key2"),
    agent_cache.set("key3", agent3)
)
```

## Memory Management

### LRU Eviction
When cache reaches `max_size`, least recently used entry is evicted:

```python
# Cache with max_size=3
await cache.set("a", obj_a)  # Cache: [a]
await cache.set("b", obj_b)  # Cache: [a, b]
await cache.set("c", obj_c)  # Cache: [a, b, c]
await cache.get("a")         # Cache: [b, c, a] (a moved to end)
await cache.set("d", obj_d)  # Cache: [c, a, d] (b evicted - LRU)
```

### Check Evictions
```python
stats = cache.get_stats()
if stats['evictions'] > 0:
    logger.warning(f"Cache evicted {stats['evictions']} entries - consider increasing max_size")
```

## Best Practices

### 1. Use Descriptive Cache Keys
```python
# Good
cache_key = f"agent:{provider}:{model}:{framework}"

# Bad
cache_key = f"{p}:{m}"
```

### 2. Log Cache Hits/Misses
```python
if cached_object is not None:
    logger.info(f"✅ Cache hit: {cache_key}")
else:
    logger.info(f"❌ Cache miss: {cache_key}")
```

### 3. Monitor Hit Rates
```python
stats = agent_cache.get_stats()
hit_rate = float(stats['hit_rate'].rstrip('%'))

if hit_rate < 80:
    logger.warning(f"Low cache hit rate: {hit_rate}%")
```

### 4. Clear Cache When Needed
```python
# Clear on configuration change
@app.on_event("startup")
async def on_config_change():
    await agent_cache.clear()
    await llm_provider_cache.clear()
```

### 5. Handle Cache Errors Gracefully
```python
try:
    cached_obj = await cache.get(cache_key)
except Exception as e:
    logger.error(f"Cache error: {e}")
    cached_obj = None  # Fall back to creating new instance
```

## Troubleshooting

### Cache Not Working
1. Check if cache is initialized:
   ```python
   from app.infrastructure.cache.instances import agent_cache
   print(agent_cache)  # Should show ObjectCacheProvider instance
   ```

2. Check cache stats:
   ```python
   stats = agent_cache.get_stats()
   print(stats)  # Check hits/misses
   ```

### Low Hit Rate
1. Check cache key consistency:
   ```python
   # Ensure same key format used everywhere
   cache_key = f"{provider}:{model}"
   ```

2. Check if cache is being cleared prematurely:
   ```python
   # Avoid clearing cache too frequently
   ```

3. Increase max_size if evictions are high:
   ```python
   stats = agent_cache.get_stats()
   if stats['evictions'] > stats['size']:
       # Cache is too small - increase max_size
   ```

### Memory Issues
1. Check cache size:
   ```python
   stats = agent_cache.get_stats()
   print(f"Cache size: {stats['size']}/{stats['max_size']}")
   ```

2. Reduce max_size if needed:
   ```python
   # Recreate cache with smaller max_size
   agent_cache = CacheFactory.create_cache(
       cache_type=CacheType.OBJECT,
       namespace="agents",
       max_size=10  # Reduced from 50
   )
   ```

## Performance Tips

1. **Warm up cache on startup:**
   ```python
   @app.on_event("startup")
   async def warmup_cache():
       # Pre-create common LLM providers
       await LLMFactory.get_llm(LLMProvider.OPENAI)
       await LLMFactory.get_llm(LLMProvider.ANTHROPIC)
   ```

2. **Use cache stats for monitoring:**
   ```python
   # Add to metrics endpoint
   @app.get("/metrics/cache")
   async def cache_metrics():
       return {
           "agent_cache": agent_cache.get_stats(),
           "llm_cache": llm_provider_cache.get_stats()
       }
   ```

3. **Adjust max_size based on usage:**
   ```python
   # Monitor evictions and adjust
   stats = agent_cache.get_stats()
   if stats['evictions'] > 10:
       # Increase max_size in configuration
       pass
   ```

## See Also
- [Cache Architecture](./CACHE-ARCHITECTURE-TWO-LAYER-DESIGN.md)
- [Production-Grade Caching](./PRODUCTION-GRADE-CACHING.md)
- [Cache Integration Complete](./CACHE-INTEGRATION-COMPLETE.md)
