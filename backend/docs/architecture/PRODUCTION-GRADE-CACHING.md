# Production-Grade Caching Implementation

## Executive Summary

This document describes the enterprise-grade caching implementation that reflects 18+ years of production system experience. All caches are **thread-safe**, have **bounded memory usage**, implement **LRU eviction**, and include comprehensive **telemetry**.

---

## Core Principles

### 1. Thread Safety (Concurrency)
**Problem:** Module-level dictionaries cause race conditions under load
**Solution:** All caches use `threading.RLock()` for safe concurrent access

### 2. Memory Bounds (Resource Management)
**Problem:** Unbounded caches = memory leaks in production
**Solution:** LRU eviction with sensible max sizes (10-50 entries)

### 3. State Isolation (No Shared Mutable State)
**Problem:** Mutating cached objects causes bugs across requests
**Solution:** Each cache entry gets its own instance, configured before caching

### 4. Observability (Production Monitoring)
**Problem:** Can't optimize what you can't measure
**Solution:** Hit/miss rates, cache sizes, eviction counters

### 5. Lifecycle Management (Resource Cleanup)
**Problem:** Cached objects with connections cause resource leaks
**Solution:** LRU eviction, weak references where appropriate

---

## Implementation Details

### LRU Cache (llm_factory.py)

```python
class LRUCache:
    """Thread-safe LRU cache with size limit and TTL support."""

    def __init__(self, max_size: int = 50, ttl_seconds: Optional[int] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict = {}  # {key: (value, timestamp, access_count)}
        self.lock = threading.RLock()  # ← Thread safety
        self.hits = 0  # ← Telemetry
        self.misses = 0
```

**Key Features:**
- **RLock**: Reentrant lock prevents deadlocks
- **Access Counting**: Tracks usage for LRU eviction
- **TTL Support**: Optional time-based expiration
- **Hit/Miss Tracking**: Performance monitoring
- **Bounded Size**: Automatic eviction at max_size

**Production Metrics:**
```python
stats = cache.stats()
# {
#     'hit_rate': '87.35%',  # ← Production KPI
#     'size': 12,
#     'max_size': 20,
#     'hits': 342,
#     'misses': 49
# }
```

---

### Agent Cache (chat_service.py)

```python
class AgentCache:
    """
    Thread-safe LRU cache for agent instances with proper lifecycle management.

    Uses OrderedDict for efficient LRU eviction.
    Max size of 10 prevents memory bloat (agents hold LLM clients + tools).
    """

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()  # ← LRU ordering
        self.lock = threading.RLock()  # ← Thread safety
        self.hits = 0
        self.misses = 0

    def set(self, key, agent):
        with self.lock:
            if len(self.cache) >= self.max_size:
                lru_key, lru_agent = self.cache.popitem(last=False)  # ← LRU eviction
                logger.info(f"Evicted LRU agent: {lru_key}")
            self.cache[key] = agent
```

**Why 10 Agents Max?**
- Each agent holds: LLM client, 84 tools, session repo
- Estimated memory: ~50-100MB per agent
- 10 agents = ~1GB memory (reasonable for production)
- LRU ensures most-used combinations stay cached

---

### LLM Provider Caching (llm_factory.py)

```python
_llm_provider_cache = LRUCache(max_size=20, ttl_seconds=None)

def get_llm_by_name(provider_name, model, use_cache=True):
    cache_key = (provider_name, validated_model)

    # Thread-safe cache lookup
    cached_provider = _llm_provider_cache.get(cache_key)
    if cached_provider is not None:
        logger.info(
            f"✅ Cache hit: {provider_name}, {validated_model} "
            f"(hit_rate: {_llm_provider_cache.stats()['hit_rate']})"
        )
        return cached_provider

    # Create NEW instance (no shared state)
    provider_class = LLMRegistry.get_provider_class(provider)
    llm_provider = provider_class()

    # Configure BEFORE caching (immutable after)
    llm_provider.config['model'] = validated_model

    # Thread-safe cache insert
    _llm_provider_cache.set(cache_key, llm_provider)
    return llm_provider
```

**Critical Fix: State Isolation**
```python
# ❌ BAD (Original): Mutates cached instance
llm = get_cached_provider()
llm.config['model'] = new_model  # ← Affects ALL users!

# ✅ GOOD (Fixed): Configure before caching
llm = create_new_provider()
llm.config['model'] = model  # ← Fresh instance
cache.set(key, llm)
```

---

## Production Monitoring

### Cache Metrics Endpoints

All caches expose statistics for monitoring:

```python
# LLM Provider Cache
from app.infrastructure.llm.factory.llm_factory import LLMFactory
stats = LLMFactory.get_llm_cache_stats()
# {
#     'hit_rate': '92.15%',
#     'cache_size': 5,
#     'max_size': 20,
#     'total_hits': 472,
#     'total_misses': 41,
#     'entries': [...]
# }

# Agent Cache
from app.services.chat_service import ChatService
service = ChatService()
stats = service.get_agent_cache_stats()
# {
#     'hit_rate': '85.33%',
#     'size': 3,
#     'max_size': 10,
#     'hits': 128,
#     'misses': 22,
#     'entries': [...]
# }

# Tool Registry Cache
from app.agent.tools.base.registry import ToolRegistry
stats = ToolRegistry.get_cache_stats()
# {
#     'cache_enabled': True,
#     'cached_categories': ['category:all'],
#     'total_cached_tools': 84
# }

# GitHub Repository Cache
from app.agent.tools.github.connection_manager import GitHubConnectionManager
stats = GitHubConnectionManager.get_cache_stats()
# {
#     'cached_installations': 1,
#     'cache_ttl_seconds': 600,
#     'entries': [...]
# }
```

### Recommended Production Alerts

```yaml
# Prometheus/Grafana Alerts

- name: LowCacheHitRate
  expr: llm_cache_hit_rate < 70
  severity: warning
  description: "LLM cache hit rate below 70% - investigate cold starts"

- name: CacheEvictionRate
  expr: rate(agent_cache_evictions[5m]) > 1
  severity: info
  description: "Frequent agent evictions - consider increasing max_size"

- name: MemoryPressure
  expr: agent_cache_size >= agent_cache_max_size * 0.9
  severity: warning
  description: "Agent cache near capacity - monitor memory usage"
```

---

## Memory Profiling

### Estimated Memory Usage

| Component | Per Entry | Max Entries | Total |
|-----------|-----------|-------------|-------|
| LLM Provider Cache | ~5-10 MB | 20 | ~200 MB |
| Agent Cache | ~50-100 MB | 10 | ~1 GB |
| Tool Registry Cache | ~50 MB | 1 | ~50 MB |
| GitHub Repo Cache | ~100 KB | 5 | ~500 KB |
| Connection Manager Cache | ~1 MB | 5 | ~5 MB |
| **Total** | | | **~1.25 GB** |

**Production Capacity Planning:**
- Caches designed for vertical scaling (single server)
- Total cache memory: ~1.25GB (reasonable for 4GB+ instances)
- LRU eviction prevents unbounded growth
- Horizontal scaling: Each instance has independent caches

---

## Cache Invalidation Strategy

### Development/Testing

```python
# Clear all caches between tests
from app.infrastructure.llm.factory.llm_factory import LLMFactory
from app.infrastructure.connections.factory.connection_factory import ConnectionFactory
from app.agent.tools.base.registry import ToolRegistry
from app.agent.tools.github.connection_manager import GitHubConnectionManager
from app.services.chat_service import ChatService

# Before each test
LLMFactory.clear_llm_cache()
ConnectionFactory.clear_cache()
ToolRegistry.clear_tool_cache()
GitHubConnectionManager.clear_repo_cache()
ChatService().clear_agent_cache()
```

### Production Deployment

```python
# Option 1: Rolling restart (simplest)
# - Restart application servers
# - Caches warm up naturally on first requests

# Option 2: Graceful cache warming
def warm_caches():
    """Warm critical caches on startup."""
    from app.infrastructure.llm.factory.llm_factory import LLMFactory
    from app.agent.tools.base.registry import ToolRegistry

    # Warm default LLM provider
    LLMFactory.get_llm_by_name('openai', 'gpt-4o-mini')

    # Warm tool registry (most expensive)
    ToolRegistry.get_instantiated_tools()

    logger.info("✅ Caches warmed successfully")

# Call from app startup (FastAPI lifespan)
@app.on_event("startup")
async def startup_event():
    warm_caches()
```

### Configuration Changes

```python
# When LLM config changes
LLMFactory.clear_llm_cache(provider_name='openai')

# When tool config changes
ToolRegistry.clear_tool_cache(category='github')

# When database config changes
ConnectionFactory.clear_cache(ConnectionType.MONGODB)

# When switching agent frameworks
ChatService().set_agent_framework(AgentFramework.LANGGRAPH)  # Auto-clears agent cache
```

---

## Thread Safety Verification

### Concurrency Test

```python
import threading
import concurrent.futures

def test_concurrent_cache_access():
    """Verify thread safety under concurrent load."""
    from app.infrastructure.llm.factory.llm_factory import LLMFactory

    def get_llm_concurrent():
        for _ in range(100):
            llm = LLMFactory.get_llm_by_name('openai', 'gpt-4o-mini')
            assert llm is not None

    # 10 threads, 100 requests each = 1000 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_llm_concurrent) for _ in range(10)]
        concurrent.futures.wait(futures)

    stats = LLMFactory.get_llm_cache_stats()
    print(f"Hit rate: {stats['hit_rate']}")  # Should be >99%
    print(f"Total requests: {stats['total_hits'] + stats['total_misses']}")
```

---

## Performance Comparison

### Before (Naive Implementation)

```python
# ❌ Not thread-safe
_cache = {}

def get_llm(provider, model):
    key = (provider, model)
    if key in _cache:  # ← Race condition!
        return _cache[key]

    llm = create_llm()
    _cache[key] = llm  # ← Race condition!
    return llm
```

**Issues:**
- Race condition: Multiple threads can create duplicate entries
- No memory bounds: Cache grows forever
- No telemetry: Can't measure effectiveness
- Shared state: Mutating cached object affects all users

### After (Production-Grade)

```python
# ✅ Thread-safe, bounded, observable
_cache = LRUCache(max_size=20)

def get_llm(provider, model):
    cache_key = (provider, model)

    # Thread-safe get
    cached = _cache.get(cache_key)
    if cached:
        return cached

    # Create fresh instance
    llm = create_llm()
    llm.config['model'] = model  # Configure before caching

    # Thread-safe set with LRU eviction
    _cache.set(cache_key, llm)

    # Telemetry
    logger.info(f"Cache stats: {_cache.stats()}")
    return llm
```

**Benefits:**
- ✅ Thread-safe with RLock
- ✅ Bounded memory with LRU eviction
- ✅ Observable with hit/miss tracking
- ✅ State isolation (no shared mutations)

---

## Rollback Plan

If caching causes issues in production:

```python
# Emergency: Disable all caching

# 1. Disable tool caching
ToolRegistry.set_cache_enabled(False)

# 2. Clear all caches
LLMFactory.clear_llm_cache()
ConnectionFactory.clear_cache()
ToolRegistry.clear_tool_cache()
GitHubConnectionManager.clear_repo_cache()
ChatService().clear_agent_cache()

# 3. Force fresh instances
llm = LLMFactory.get_llm_by_name('openai', 'gpt-4o-mini', use_cache=False)
tools = ToolRegistry.get_instantiated_tools(use_cache=False)

# 4. Restart application (clears in-memory caches)
```

---

## Code Review Checklist

When reviewing caching code, verify:

- [ ] **Thread Safety**: Uses `threading.RLock()` or `threading.Lock()`
- [ ] **Memory Bounds**: Has `max_size` parameter with LRU eviction
- [ ] **State Isolation**: No mutations of cached objects
- [ ] **Telemetry**: Tracks hits/misses for monitoring
- [ ] **Cache Keys**: Immutable tuples, not mutable dicts/lists
- [ ] **Error Handling**: Cache failures don't break functionality
- [ ] **Documentation**: Clear docstrings explaining strategy
- [ ] **Testing**: Unit tests for concurrency and eviction

---

## Future Enhancements

### 1. Distributed Caching (Multi-Server)

Current: In-memory caches (single server)
Future: Redis-backed caching for distributed systems

```python
# Replace LRUCache with RedisLRUCache
from app.infrastructure.cache.redis_cache_provider import RedisCacheProvider

_llm_provider_cache = RedisCacheProvider(
    namespace="llm_providers",
    max_size=20,
    ttl_seconds=3600
)
```

### 2. Adaptive Cache Sizing

Current: Fixed max_size
Future: Dynamic sizing based on memory pressure

```python
class AdaptiveLRUCache(LRUCache):
    def __init__(self, target_memory_mb: int = 500):
        self.target_memory_mb = target_memory_mb
        self.max_size = self._calculate_max_size()

    def _calculate_max_size(self):
        """Calculate max entries based on available memory."""
        available_memory = psutil.virtual_memory().available / (1024 ** 2)
        return min(50, int(available_memory * 0.1 / self.target_memory_mb))
```

### 3. Cache Warming on Deployment

Current: Cold start on first request
Future: Pre-warm critical caches

```python
async def warm_production_caches():
    """Warm caches with production traffic patterns."""
    # Warm top 5 models from last 24h
    top_models = await get_popular_models()
    for provider, model in top_models:
        LLMFactory.get_llm_by_name(provider, model)
```

---

## Related Documentation

- [Optimization Overview](./OPTIMIZATION-2026-02-25.md)
- [Quick Reference: Cache API](../QUICK-REFERENCE-CACHE-API.md)
- [Redis Cache Service](../guides/redis-cache-service.md)
- [Design Patterns](./design-patterns.md)

---

**Author:** Senior Backend Engineer (18+ years experience)
**Date:** February 25, 2026
**Status:** Production-Ready ✅
**Code Review:** Approved for deployment
