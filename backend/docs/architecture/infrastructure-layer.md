# Infrastructure Layer Architecture

## Overview

The **Infrastructure Layer** is a comprehensive abstraction layer that manages all external dependencies and low-level system interactions. It follows the **Factory + Registry Pattern** consistently across all components, providing a unified interface for connections, caching, and LLM providers.

## Design Philosophy

The infrastructure layer adheres to these core principles:

1. **Separation of Concerns**: Business logic is decoupled from infrastructure details
2. **Factory Pattern**: Centralized creation of infrastructure components
3. **Registry Pattern**: Automatic discovery and registration of implementations
4. **Dependency Injection**: Components receive dependencies rather than creating them
5. **Settings-Driven Configuration**: All configuration comes from YAML files and environment variables
6. **Testability**: Easy to mock and test infrastructure components

## Layer Structure

```
infrastructure/
├── cache/              # Cache providers (Redis, InMemory)
│   ├── base/           # Base classes and interfaces
│   ├── implementations/ # Concrete providers
│   ├── factory/        # CacheFactory
│   ├── cache_service.py # Convenience wrapper
│   └── instances.py    # Pre-configured instances
│
├── connections/        # Database and external service connections
│   ├── base/           # Base connection managers
│   ├── database/       # MongoDB, PostgreSQL, Redis
│   ├── external/       # Confluence, Jira, S3
│   ├── vector/         # Qdrant, ChromaDB, PgVector
│   └── factory/        # ConnectionFactory
│
└── llm/                # LLM provider abstraction
    ├── base/           # BaseLLMProvider, LLMRegistry
    ├── providers/      # OpenAI, Groq, Anthropic, etc.
    ├── factory/        # LLMFactory
    ├── config/         # LLM configuration utilities
    └── context/        # Context window management
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│   (Services, APIs, Agent Logic - Business Rules)                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                            │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Cache System   │  │  Connections    │  │  LLM Providers │  │
│  │                 │  │                 │  │                │  │
│  │  CacheFactory   │  │ConnectionFactory│  │  LLMFactory    │  │
│  │  CacheRegistry  │  │ConnectionRegistry│  │  LLMRegistry   │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬───────┘  │
│           │                    │                     │          │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼───────┐  │
│  │ Redis Provider  │  │ DB Managers     │  │ Provider Impls │  │
│  │ InMemory Provider│  │ Vector Stores   │  │ (OpenAI, etc.) │  │
│  └─────────────────┘  │ External APIs   │  └────────────────┘  │
│                       └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               External Systems & Dependencies                    │
│  (Redis, PostgreSQL, MongoDB, OpenAI API, Qdrant, etc.)         │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Cache Infrastructure

**Location**: `app/infrastructure/cache/`

**Purpose**: Provides unified caching interface with support for multiple backends (Redis, In-Memory).

**Key Components**:
- `CacheFactory`: Creates cache provider instances
- `CacheRegistry`: Registers cache implementations
- `BaseCacheProvider`: Abstract base for all providers
- `RedisCacheProvider`: Redis-backed caching
- `InMemoryCacheProvider`: In-memory caching for dev/testing
- `CacheService`: Convenience wrapper for dependency injection
- Pre-configured instances: `confirmation_cache`, `signup_cache`, etc.

**Usage**:
```python
from app.infrastructure.cache import CacheService
from app.infrastructure.cache.instances import confirmation_cache

# Create custom instance
cache = CacheService(namespace="myfeature", default_ttl=600)
await cache.set("key", value)

# Use pre-configured instance
await confirmation_cache.set("action_123", data)
```

### 2. Connection Infrastructure

**Location**: `app/infrastructure/connections/`

**Purpose**: Manages all external connections with automatic configuration, health checking, and resilience.

**Key Components**:
- `ConnectionFactory`: Creates connection manager instances
- `ConnectionRegistry`: Registers connection implementations
- `BaseConnectionManager`: Base class for sync connections
- `AsyncBaseConnectionManager`: Base class for async connections
- Database managers: PostgreSQL, MongoDB, Redis
- Vector store managers: Qdrant, ChromaDB, PgVector
- External service managers: Confluence, Jira, S3

**Connection Types**:
```python
class ConnectionType(str, Enum):
    # Databases
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    REDIS = "redis"
    
    # Vector Stores
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"
    CHROMADB = "chromadb"
    
    # External Services
    CONFLUENCE = "confluence"
    JIRA = "jira"
    S3 = "s3"
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get connection manager
postgres_mgr = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)

# Connect and use
await postgres_mgr.connect()
result = await postgres_mgr.execute_query("SELECT * FROM users")

# Health check
if postgres_mgr.is_healthy():
    print("Connection is healthy!")
```

### 3. LLM Infrastructure

**Location**: `app/infrastructure/llm/`

**Purpose**: Provides unified interface for multiple LLM providers with context management and streaming support.

**Key Components**:
- `LLMFactory`: Creates LLM provider instances
- `LLMRegistry`: Registers LLM implementations
- `BaseLLMProvider`: Abstract base for all providers
- Provider implementations: OpenAI, Azure OpenAI, Anthropic, Groq, Google, HuggingFace, Ollama
- `ContextWindowManager`: Manages conversation context and token limits
- Context strategies: Recent, Sliding Window, Summarization

**Supported Providers**:
```python
class LLMProvider(str, Enum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
```

**Usage**:
```python
from app.infrastructure.llm import LLMFactory
from app.core.constants import LLMProvider

# Get LLM provider
llm = LLMFactory.get_llm(LLMProvider.GROQ)
await llm.initialize()

# Generate response
response = await llm.generate("Explain quantum computing")
print(response.content)

# Stream response
async for chunk in llm.stream_generate("Write a story"):
    print(chunk, end="", flush=True)
```

## Factory + Registry Pattern

All infrastructure components follow the same pattern:

### 1. Define Enum for Types
```python
class InfrastructureType(str, Enum):
    TYPE_A = "type_a"
    TYPE_B = "type_b"
```

### 2. Create Base Abstract Class
```python
class BaseInfrastructure(ABC):
    @abstractmethod
    def operation(self):
        pass
```

### 3. Implement Registry
```python
class InfrastructureRegistry:
    _registry: Dict[InfrastructureType, Type[BaseInfrastructure]] = {}
    
    @classmethod
    def register(cls, infra_type: InfrastructureType):
        def decorator(infra_class):
            cls._registry[infra_type] = infra_class
            return infra_class
        return decorator
```

### 4. Create Implementations with Decorator
```python
@InfrastructureRegistry.register(InfrastructureType.TYPE_A)
class TypeAInfrastructure(BaseInfrastructure):
    def operation(self):
        # Implementation
        pass
```

### 5. Build Factory
```python
class InfrastructureFactory:
    @staticmethod
    def create(infra_type: InfrastructureType) -> BaseInfrastructure:
        infra_class = InfrastructureRegistry.get_class(infra_type)
        return infra_class()
```

## Configuration Management

All infrastructure components are configured via YAML files in `resources/`:

- `application-db.yaml`: Database connections (PostgreSQL, MongoDB, Redis)
- `application-cache.yaml`: Cache configuration
- `application-llm.yaml`: LLM provider settings
- `application-vector.yaml`: Vector store configuration
- `application-external.yaml`: External service credentials

Configuration uses environment variable substitution:
```yaml
redis:
  host: "${REDIS_HOST:localhost}"
  port: "${REDIS_PORT:6379}"
  password: "${REDIS_PASSWORD}"
```

## Testing Infrastructure Components

### Unit Testing with Mocks

```python
from unittest.mock import AsyncMock, patch

# Test with mocked provider
@patch('app.infrastructure.cache.CacheFactory.create_cache')
async def test_cache_service(mock_factory):
    mock_provider = AsyncMock()
    mock_factory.return_value = mock_provider
    
    cache = CacheService("test")
    await cache.set("key", "value")
    
    mock_provider.set.assert_called_once()
```

### Integration Testing

```python
# Test with in-memory provider
from app.infrastructure.cache import CacheService, CacheType

async def test_cache_integration():
    cache = CacheService("test", cache_type=CacheType.IN_MEMORY)
    
    await cache.set("key", "value")
    result = await cache.get("key")
    
    assert result == "value"
```

## Benefits of Infrastructure Layer

### 1. **Consistency**
- Same patterns across all infrastructure components
- Predictable API surface
- Easy to learn and use

### 2. **Flexibility**
- Easy to swap implementations (Redis ↔ InMemory)
- Add new providers without changing business logic
- Configure via YAML without code changes

### 3. **Testability**
- Mock at factory level for unit tests
- Use in-memory providers for integration tests
- No need to mock external systems

### 4. **Maintainability**
- Single place to add features (base classes)
- Centralized error handling
- Consistent logging and monitoring

### 5. **Separation of Concerns**
- Business logic doesn't know about Redis, OpenAI, etc.
- Infrastructure concerns isolated
- Easy to refactor without breaking business logic

## Migration Guide

### From Direct Dependencies

**Before** (Direct Redis usage):
```python
import redis.asyncio as redis

redis_client = await redis.from_url("redis://localhost")
await redis_client.set("key", json.dumps(value))
data = await redis_client.get("key")
value = json.loads(data)
```

**After** (Infrastructure layer):
```python
from app.infrastructure.cache import CacheService

cache = CacheService("myfeature")
await cache.set("key", value)  # Auto-serialization
value = await cache.get("key")  # Auto-deserialization
```

### From Old Service Layer

**Before** (Old RedisCacheService):
```python
from app.services.redis_cache_service import RedisCacheService

cache = RedisCacheService("myfeature", default_ttl=600)
```

**After** (New infrastructure):
```python
from app.infrastructure.cache import CacheService

cache = CacheService("myfeature", default_ttl=600)
```

The API remains the same - only the import path changed!

## Best Practices

1. **Use Pre-configured Instances**: For common use cases, use the pre-configured cache instances
2. **Favor Context Managers**: Use async context managers for automatic cleanup
3. **Configuration Over Code**: Store settings in YAML files, not hardcoded
4. **Test with In-Memory Providers**: Use in-memory implementations for faster tests
5. **Check Health**: Always verify connection health before critical operations
6. **Handle Failures Gracefully**: Infrastructure operations can fail - always have fallbacks

## Future Enhancements

- [ ] Additional cache providers (Memcached, DynamoDB)
- [ ] More vector stores (Weaviate, Milvus, Pinecone)
- [ ] Additional LLM providers (Cohere, AI21, Replicate)
- [ ] Connection pooling improvements
- [ ] Advanced resilience patterns (bulkhead, rate limiting)
- [ ] Distributed tracing integration
- [ ] Metrics and observability hooks

## See Also

- [Cache Service Guide](../guides/redis-cache-service.md)
- [Connection Management](../guides/connections/README.md)
- [LLM Providers](../guides/llm-providers/README.md)
- [Cache Design Comparison](cache-service-design-comparison.md)
- [Configuration System](configuration-system.md)
