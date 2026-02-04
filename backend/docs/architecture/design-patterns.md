# Design Patterns in AgentHub

## Table of Contents
- [Overview](#overview)
- [Registry Pattern](#registry-pattern)
- [Factory Pattern](#factory-pattern)
- [Singleton Pattern](#singleton-pattern)
- [Strategy Pattern](#strategy-pattern)
- [Decorator Pattern](#decorator-pattern)
- [Template Method Pattern](#template-method-pattern)
- [Observer Pattern](#observer-pattern)
- [Dependency Injection](#dependency-injection)
- [Pattern Combinations](#pattern-combinations)

---

## Overview

AgentHub implements **8 core design patterns** to achieve:
- **Flexibility**: Easy to extend and modify
- **Maintainability**: Clear, predictable code structure
- **Testability**: Components can be tested in isolation
- **Scalability**: Patterns that support growth

Each pattern is implemented with **real production code** - these aren't theoretical examples!

---

## Registry Pattern

### Purpose
**Dynamically register and discover components at runtime** without modifying core code.

### Use Cases in AgentHub
1. **Tool Registration**: Register agent tools dynamically
2. **Provider Registration**: Register LLM providers
3. **Middleware Registration**: Add request/response middleware

### Implementation

```python
# src/app/agent/tools/registry.py

from typing import Dict, Callable, Any
from functools import wraps

class ToolRegistry:
    """
    Registry for dynamically registering agent tools.
    
    Benefits:
    - No code changes to add new tools
    - Tools discovered automatically
    - Type-safe registration
    """
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self,
        name: str,
        description: str = None,
        category: str = "general"
    ):
        """
        Decorator to register a tool.
        
        Example:
            @tool_registry.register("jira_create_issue")
            async def create_issue(summary: str, description: str):
                # Implementation
                pass
        """
        def decorator(func: Callable):
            self._tools[name] = func
            self._metadata[name] = {
                "description": description or func.__doc__,
                "category": category,
                "parameters": self._extract_params(func)
            }
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_tool(self, name: str) -> Callable:
        """Retrieve a registered tool."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name]
    
    def list_tools(self, category: str = None) -> Dict[str, Dict]:
        """List all registered tools, optionally filtered by category."""
        if category:
            return {
                name: meta
                for name, meta in self._metadata.items()
                if meta["category"] == category
            }
        return self._metadata.copy()
    
    @staticmethod
    def _extract_params(func: Callable) -> Dict:
        """Extract parameter information from function signature."""
        import inspect
        sig = inspect.signature(func)
        return {
            name: {
                "type": param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "Any",
                "default": param.default if param.default != inspect.Parameter.empty else None
            }
            for name, param in sig.parameters.items()
        }

# Global registry instance
tool_registry = ToolRegistry()
```

### Usage Example

```python
# Register a Jira tool
from src.app.agent.tools.registry import tool_registry

@tool_registry.register(
    name="jira_create_issue",
    description="Create a new Jira issue",
    category="jira"
)
async def create_jira_issue(
    project: str,
    summary: str,
    description: str,
    issue_type: str = "Task"
) -> dict:
    """Create a Jira issue and return the issue key."""
    # Implementation using Jira service
    from src.app.services.jira_service import JiraService
    
    service = JiraService()
    issue = await service.create_issue(
        project=project,
        summary=summary,
        description=description,
        issue_type=issue_type
    )
    return {"issue_key": issue.key, "url": issue.permalink()}

# Discover and use tools
all_tools = tool_registry.list_tools()
jira_tools = tool_registry.list_tools(category="jira")

# Execute a tool
tool = tool_registry.get_tool("jira_create_issue")
result = await tool(
    project="PROJ",
    summary="Bug fix",
    description="Fix login issue"
)
```

### Benefits
- **Extensibility**: Add tools without modifying core code
- **Discovery**: Tools automatically available to agents
- **Metadata**: Rich information for LLM tool selection
- **Type Safety**: Validates parameters at registration

---

## Factory Pattern

### Purpose
**Create objects without specifying exact classes**, enabling runtime provider selection.

### Use Cases in AgentHub
1. **LLM Factory**: Create LLM instances for different providers
2. **Session Factory**: Create session managers for different backends
3. **Embedding Factory**: Create embedding models

### Implementation

```python
# src/app/llm/factory.py

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    """Abstract base class for all LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        """Generate structured output matching schema."""
        pass

class OpenAILLM(BaseLLM):
    """OpenAI implementation."""
    
    def __init__(
        self,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        **kwargs
    ):
        import openai
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            **kwargs
        )
        return response.choices[0].message.content
    
    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_schema", "json_schema": schema}
        )
        import json
        return json.loads(response.choices[0].message.content)

class AzureOpenAILLM(BaseLLM):
    """Azure OpenAI implementation."""
    
    def __init__(
        self,
        deployment: str,
        api_key: str,
        endpoint: str,
        api_version: str = "2024-02-15-preview",
        **kwargs
    ):
        import openai
        self.client = openai.AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        self.deployment = deployment
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content
    
    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        # Similar to OpenAI implementation
        pass

class AnthropicLLM(BaseLLM):
    """Anthropic Claude implementation."""
    
    def __init__(self, model: str, api_key: str, **kwargs):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text
    
    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        # Implementation with tool use for structured output
        pass

class LLMFactory:
    """
    Factory for creating LLM instances.
    
    Benefits:
    - Switch providers without code changes
    - Centralized configuration
    - Easy to add new providers
    """
    
    _providers: Dict[str, type] = {
        "openai": OpenAILLM,
        "azure": AzureOpenAILLM,
        "anthropic": AnthropicLLM,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register a custom LLM provider."""
        cls._providers[name] = provider_class
    
    @classmethod
    def create_llm(
        cls,
        provider: str,
        **kwargs
    ) -> BaseLLM:
        """
        Create an LLM instance for the specified provider.
        
        Args:
            provider: Provider name (openai, azure, anthropic)
            **kwargs: Provider-specific configuration
            
        Returns:
            Configured LLM instance
            
        Raises:
            ValueError: If provider not supported
            
        Example:
            llm = LLMFactory.create_llm(
                provider="openai",
                model="gpt-4",
                api_key="sk-xxx"
            )
        """
        if provider not in cls._providers:
            raise ValueError(
                f"Provider '{provider}' not supported. "
                f"Available: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider]
        return provider_class(**kwargs)
    
    @classmethod
    def create_from_config(cls, config: dict) -> BaseLLM:
        """Create LLM from configuration dictionary."""
        provider = config.pop("provider")
        return cls.create_llm(provider=provider, **config)
```

### Usage Example

```python
from src.app.llm.factory import LLMFactory

# Create OpenAI instance
openai_llm = LLMFactory.create_llm(
    provider="openai",
    model="gpt-4",
    api_key="sk-xxx",
    temperature=0.7
)

# Create Azure instance
azure_llm = LLMFactory.create_llm(
    provider="azure",
    deployment="gpt-4",
    api_key="xxx",
    endpoint="https://your-resource.openai.azure.com"
)

# Switch providers at runtime based on config
from src.app.core.config import get_settings

settings = get_settings()
llm = LLMFactory.create_llm(
    provider=settings.llm.default_provider,
    **settings.llm.get_provider_config()
)

# Use the LLM (same interface regardless of provider)
response = await llm.generate("Explain RAG in simple terms")
print(response)

# Register custom provider
class CustomLLM(BaseLLM):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Custom implementation
        pass

LLMFactory.register_provider("custom", CustomLLM)
```

### Benefits
- **Provider Agnostic**: Same code works with any LLM
- **Configuration-Driven**: Change providers via config
- **Extensible**: Easy to add new providers
- **Testable**: Mock providers in tests

---

## Singleton Pattern

### Purpose
**Ensure only one instance exists** for shared resources like configuration and connections.

### Use Cases in AgentHub
1. **Settings Management**: Single source of truth for configuration
2. **Connection Pools**: Reuse database connections
3. **Logger Instance**: Centralized logging

### Implementation

```python
# src/app/core/config.py

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class LLMSettings(BaseSettings):
    """LLM configuration settings."""
    default_provider: str = Field(default="openai")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    azure_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    postgres_url: str = Field(alias="DATABASE_URL")
    mongodb_url: str = Field(alias="MONGODB_URL")
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    
    class Config:
        env_file = ".env"

class AppSettings(BaseSettings):
    """Main application settings."""
    app_name: str = "AgentHub"
    environment: str = Field(default="dev", alias="APP_ENV")
    debug: bool = Field(default=False)
    
    # Nested settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> AppSettings:
    """
    Get application settings singleton.
    
    Uses @lru_cache to ensure only one instance is created.
    The instance is cached and reused for all subsequent calls.
    
    Benefits:
    - Single source of truth
    - Lazy initialization
    - Thread-safe (in CPython)
    - Memory efficient
    
    Returns:
        AppSettings instance
    """
    return AppSettings()

# Alternative: Traditional Singleton implementation
class SingletonMeta(type):
    """
    Metaclass for Singleton pattern.
    Thread-safe singleton implementation.
    """
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class ConnectionPool(metaclass=SingletonMeta):
    """
    Database connection pool singleton.
    
    Ensures all parts of the application use the same connection pool.
    """
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._pool = None
        self._settings = get_settings()
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self._pool is not None:
            return
        
        import asyncpg
        self._pool = await asyncpg.create_pool(
            self._settings.database.postgres_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def acquire(self):
        """Get a connection from the pool."""
        if self._pool is None:
            await self.initialize()
        return await self._pool.acquire()
    
    async def close(self):
        """Close all connections in the pool."""
        if self._pool:
            await self._pool.close()
```

### Usage Example

```python
# Settings singleton
from src.app.core.config import get_settings

# First call creates instance
settings1 = get_settings()
print(settings1.llm.openai_api_key)

# Subsequent calls return same instance
settings2 = get_settings()
assert settings1 is settings2  # True - same object

# Connection pool singleton
from src.app.db.pool import ConnectionPool

# Multiple instantiations return same instance
pool1 = ConnectionPool()
pool2 = ConnectionPool()
assert pool1 is pool2  # True

# Use the pool
async with pool1.acquire() as conn:
    result = await conn.fetch("SELECT * FROM users")
```

### Benefits
- **Single Instance**: Prevents multiple configuration loads
- **Thread-Safe**: Safe in concurrent environments
- **Memory Efficient**: Reuses resources
- **Lazy Initialization**: Created only when needed

---

## Strategy Pattern

### Purpose
**Define a family of algorithms** and make them interchangeable at runtime.

### Use Cases in AgentHub
1. **Chunking Strategies**: Different ways to split documents
2. **Embedding Strategies**: Different embedding models
3. **Retry Strategies**: Different retry behaviors

### Implementation

```python
# src/app/core/chunking/strategies.py

from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class Chunk:
    """Represents a document chunk."""
    text: str
    start_idx: int
    end_idx: int
    metadata: dict

class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""
    
    @abstractmethod
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        """Split text into chunks."""
        pass

class FixedSizeChunkingStrategy(ChunkingStrategy):
    """
    Split text into fixed-size chunks with optional overlap.
    
    Best for: Consistent chunk sizes, simple documents
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            
            chunks.append(Chunk(
                text=chunk_text,
                start_idx=start,
                end_idx=end,
                metadata={"strategy": "fixed_size", "size": len(chunk_text)}
            ))
            
            start = end - self.overlap if end < len(text) else end
        
        return chunks

class SemanticChunkingStrategy(ChunkingStrategy):
    """
    Split text based on semantic boundaries (paragraphs, sentences).
    
    Best for: Maintaining context, natural language
    """
    
    def __init__(self, max_chunk_size: int = 1000):
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        import re
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        start_idx = 0
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(Chunk(
                        text=current_chunk.strip(),
                        start_idx=start_idx,
                        end_idx=start_idx + len(current_chunk),
                        metadata={"strategy": "semantic"}
                    ))
                    start_idx += len(current_chunk)
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(Chunk(
                text=current_chunk.strip(),
                start_idx=start_idx,
                end_idx=start_idx + len(current_chunk),
                metadata={"strategy": "semantic"}
            ))
        
        return chunks

class RecursiveChunkingStrategy(ChunkingStrategy):
    """
    Recursively split text by different separators.
    
    Best for: Code, structured documents
    """
    
    def __init__(
        self,
        separators: List[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200
    ):
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        return self._split_text(text, self.separators)
    
    def _split_text(
        self,
        text: str,
        separators: List[str]
    ) -> List[Chunk]:
        if not separators:
            return [Chunk(
                text=text,
                start_idx=0,
                end_idx=len(text),
                metadata={"strategy": "recursive"}
            )]
        
        separator = separators[0]
        splits = text.split(separator)
        
        chunks = []
        current_chunk = ""
        start_idx = 0
        
        for split in splits:
            if len(current_chunk) + len(split) <= self.chunk_size:
                current_chunk += split + separator
            else:
                if current_chunk:
                    chunks.append(Chunk(
                        text=current_chunk,
                        start_idx=start_idx,
                        end_idx=start_idx + len(current_chunk),
                        metadata={"strategy": "recursive", "separator": separator}
                    ))
                    start_idx += len(current_chunk)
                
                # If split is still too large, use next separator
                if len(split) > self.chunk_size:
                    chunks.extend(
                        self._split_text(split, separators[1:])
                    )
                else:
                    current_chunk = split + separator
        
        if current_chunk:
            chunks.append(Chunk(
                text=current_chunk,
                start_idx=start_idx,
                end_idx=start_idx + len(current_chunk),
                metadata={"strategy": "recursive", "separator": separator}
            ))
        
        return chunks

class ChunkingContext:
    """
    Context class for using chunking strategies.
    
    Allows runtime strategy selection.
    """
    
    def __init__(self, strategy: ChunkingStrategy):
        self._strategy = strategy
    
    @property
    def strategy(self) -> ChunkingStrategy:
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: ChunkingStrategy):
        """Change strategy at runtime."""
        self._strategy = strategy
    
    def chunk_text(self, text: str, **kwargs) -> List[Chunk]:
        """Execute chunking with current strategy."""
        return self._strategy.chunk(text, **kwargs)
```

### Usage Example

```python
from src.app.core.chunking.strategies import (
    ChunkingContext,
    FixedSizeChunkingStrategy,
    SemanticChunkingStrategy,
    RecursiveChunkingStrategy
)

# Document to chunk
document = "Long document text here..."

# Strategy 1: Fixed size
fixed_strategy = FixedSizeChunkingStrategy(chunk_size=500, overlap=50)
context = ChunkingContext(fixed_strategy)
chunks = context.chunk_text(document)
print(f"Fixed size: {len(chunks)} chunks")

# Strategy 2: Semantic (runtime change)
context.strategy = SemanticChunkingStrategy(max_chunk_size=1000)
chunks = context.chunk_text(document)
print(f"Semantic: {len(chunks)} chunks")

# Strategy 3: Recursive (best for code)
recursive_strategy = RecursiveChunkingStrategy(
    separators=["\n\n", "\n", ". "],
    chunk_size=500
)
context.strategy = recursive_strategy
chunks = context.chunk_text(document)
print(f"Recursive: {len(chunks)} chunks")

# Configuration-driven strategy selection
from src.app.core.config import get_settings

settings = get_settings()
strategy_map = {
    "fixed": FixedSizeChunkingStrategy,
    "semantic": SemanticChunkingStrategy,
    "recursive": RecursiveChunkingStrategy
}

strategy_class = strategy_map[settings.chunking.strategy]
strategy = strategy_class(**settings.chunking.params)
context = ChunkingContext(strategy)
```

### Real-World Example: Embedding Configuration Strategy

**Updated Feb 2026** - The embedding system uses Strategy Pattern for configuration management.

```python
# src/app/db/vector/providers/embedding_provider.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.core.constants import EmbeddingType

class EmbeddingConfigProvider(ABC):
    """
    Strategy interface for embedding configuration providers.
    
    Allows different sources for embedding configurations:
    - Settings (production)
    - Dictionary (testing)
    - Database (runtime)
    - API (remote config)
    """
    
    @abstractmethod
    def get_config(self, embedding_type: EmbeddingType) -> Dict[str, Any]:
        """Retrieve configuration for a specific embedding type."""
        pass

class SettingsConfigProvider(EmbeddingConfigProvider):
    """Production strategy: Load from settings.embeddings."""
    
    def get_config(self, embedding_type: EmbeddingType) -> Dict[str, Any]:
        from app.core.config.framework.settings import settings
        from app.core.config.utils.config_converter import dynamic_config_to_dict
        
        config_key = embedding_type.value.lower()  # 'openai', 'huggingface', etc.
        embedding_config = getattr(settings.embeddings, config_key)
        return dynamic_config_to_dict(embedding_config)

class DictConfigProvider(EmbeddingConfigProvider):
    """Test strategy: Load from in-memory dictionary."""
    
    def __init__(self, configs: Dict[EmbeddingType, Dict[str, Any]]):
        self._configs = configs
    
    def get_config(self, embedding_type: EmbeddingType) -> Dict[str, Any]:
        if embedding_type not in self._configs:
            raise ValueError(f"Config for {embedding_type} not found")
        return self._configs[embedding_type]

class EmbeddingFactory:
    """Factory with pluggable configuration strategy."""
    
    _config_provider: EmbeddingConfigProvider = SettingsConfigProvider()  # Default
    
    @classmethod
    def set_config_provider(cls, provider: EmbeddingConfigProvider) -> None:
        """Swap configuration strategy at runtime."""
        cls._config_provider = provider
    
    @classmethod
    def get_embedding_model(cls, embedding_type: EmbeddingType):
        """Create embedding model using current config strategy."""
        config = cls._config_provider.get_config(embedding_type)
        return cls._registry[embedding_type](config)
```

**Usage - Production:**
```python
from app.db.vector.providers import EmbeddingFactory
from app.core.constants import EmbeddingType

# Uses default SettingsConfigProvider
# Gets config from settings.embeddings.openai
embedding = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI)
```

**Usage - Testing:**
```python
from app.db.vector.providers import EmbeddingFactory, DictConfigProvider

# Swap to test strategy
test_provider = DictConfigProvider({
    EmbeddingType.OPENAI: {
        'api_key': 'test-key',
        'model': 'test-model'
    }
})
EmbeddingFactory.set_config_provider(test_provider)

# Now uses test config
embedding = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI)
```

**Benefits:**
- ✅ **Testable**: Inject test configs without touching settings
- ✅ **Flexible**: Swap config sources at runtime
- ✅ **Extensible**: Add database/API providers easily
- ✅ **Clean**: Factory only creates, strategies handle config

### Benefits
- **Flexible**: Change algorithms at runtime
- **Testable**: Test each strategy independently
- **Extensible**: Add new strategies easily
- **Configuration-Driven**: Select via config

---

## Decorator Pattern

### Purpose
**Add functionality to objects dynamically** without modifying their code.

### Use Cases in AgentHub
1. **LLM Caching**: Cache LLM responses
2. **Retry Logic**: Add automatic retry behavior
3. **Monitoring**: Track metrics and logs
4. **Rate Limiting**: Enforce API limits

### Implementation

```python
# src/app/llm/decorators.py

from functools import wraps
import time
from typing import Callable, Any
import hashlib
import json

class LLMDecorator:
    """Base decorator for LLM enhancements."""
    
    def __init__(self, llm):
        self._llm = llm
    
    async def generate(self, prompt: str, **kwargs) -> str:
        return await self._llm.generate(prompt, **kwargs)

class CachedLLM(LLMDecorator):
    """
    Add caching to LLM responses.
    
    Caches based on prompt + parameters hash.
    """
    
    def __init__(self, llm, cache_backend=None, ttl: int = 3600):
        super().__init__(llm)
        self._cache = cache_backend or {}
        self._ttl = ttl
    
    def _cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and params."""
        content = json.dumps({"prompt": prompt, **kwargs}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    async def generate(self, prompt: str, **kwargs) -> str:
        cache_key = self._cache_key(prompt, **kwargs)
        
        # Check cache
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data["timestamp"] < self._ttl:
                print(f"Cache hit for prompt: {prompt[:50]}...")
                return cached_data["response"]
        
        # Generate and cache
        response = await self._llm.generate(prompt, **kwargs)
        self._cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        return response

class RetryLLM(LLMDecorator):
    """
    Add retry logic to LLM calls.
    
    Retries on transient errors with exponential backoff.
    """
    
    def __init__(
        self,
        llm,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        super().__init__(llm)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def generate(self, prompt: str, **kwargs) -> str:
        import asyncio
        from openai import APIError, RateLimitError
        
        for attempt in range(self.max_retries):
            try:
                return await self._llm.generate(prompt, **kwargs)
            except (APIError, RateLimitError) as e:
                if attempt == self.max_retries - 1:
                    raise
                
                # Exponential backoff
                delay = min(
                    self.base_delay * (2 ** attempt),
                    self.max_delay
                )
                print(f"Retry {attempt + 1}/{self.max_retries} after {delay}s")
                await asyncio.sleep(delay)
        
        raise Exception("Max retries exceeded")

class MonitoredLLM(LLMDecorator):
    """
    Add monitoring and metrics to LLM calls.
    
    Tracks: latency, token usage, errors
    """
    
    def __init__(self, llm, metrics_collector=None):
        super().__init__(llm)
        self._metrics = metrics_collector
    
    async def generate(self, prompt: str, **kwargs) -> str:
        start_time = time.time()
        
        try:
            response = await self._llm.generate(prompt, **kwargs)
            
            # Record success metrics
            duration = time.time() - start_time
            if self._metrics:
                self._metrics.record_llm_call(
                    provider=self._llm.__class__.__name__,
                    model=getattr(self._llm, 'model', 'unknown'),
                    duration=duration,
                    prompt_tokens=len(prompt.split()),
                    status="success"
                )
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            if self._metrics:
                self._metrics.record_llm_call(
                    provider=self._llm.__class__.__name__,
                    model=getattr(self._llm, 'model', 'unknown'),
                    duration=duration,
                    status="error",
                    error=str(e)
                )
            raise

class RateLimitedLLM(LLMDecorator):
    """
    Add rate limiting to LLM calls.
    
    Implements token bucket algorithm.
    """
    
    def __init__(
        self,
        llm,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 90000
    ):
        super().__init__(llm)
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self._request_tokens = requests_per_minute
        self._token_bucket = tokens_per_minute
        self._last_refill = time.time()
    
    async def _refill_buckets(self):
        """Refill token buckets based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        
        # Refill at rate per second
        request_refill = (self.requests_per_minute / 60) * elapsed
        token_refill = (self.tokens_per_minute / 60) * elapsed
        
        self._request_tokens = min(
            self.requests_per_minute,
            self._request_tokens + request_refill
        )
        self._token_bucket = min(
            self.tokens_per_minute,
            self._token_bucket + token_refill
        )
        self._last_refill = now
    
    async def generate(self, prompt: str, **kwargs) -> str:
        import asyncio
        
        estimated_tokens = len(prompt.split()) * 1.3  # Rough estimate
        
        # Wait until we have capacity
        while True:
            await self._refill_buckets()
            
            if (self._request_tokens >= 1 and 
                self._token_bucket >= estimated_tokens):
                self._request_tokens -= 1
                self._token_bucket -= estimated_tokens
                break
            
            await asyncio.sleep(0.1)
        
        return await self._llm.generate(prompt, **kwargs)

# Function decorator for retry logic
def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator to add retry logic to any async function.
    
    Example:
        @with_retry(max_retries=3, base_delay=2.0)
        async def fetch_data(url: str):
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import asyncio
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                    await asyncio.sleep(delay)
        
        return wrapper
    return decorator
```

### Usage Example

```python
from src.app.llm.factory import LLMFactory
from src.app.llm.decorators import (
    CachedLLM,
    RetryLLM,
    MonitoredLLM,
    RateLimitedLLM
)

# Base LLM
base_llm = LLMFactory.create_llm(provider="openai", model="gpt-4")

# Add caching
cached_llm = CachedLLM(base_llm, ttl=3600)

# Add retry logic
retry_llm = RetryLLM(cached_llm, max_retries=3)

# Add monitoring
monitored_llm = MonitoredLLM(retry_llm)

# Add rate limiting
production_llm = RateLimitedLLM(
    monitored_llm,
    requests_per_minute=60,
    tokens_per_minute=90000
)

# Use the fully decorated LLM
response = await production_llm.generate("Explain quantum computing")

# The call goes through all decorators:
# 1. Rate limiting checks capacity
# 2. Monitoring records start time
# 3. Retry handles transient failures
# 4. Caching checks for cached response
# 5. Base LLM generates if not cached

# Function decorator example
from src.app.llm.decorators import with_retry

@with_retry(max_retries=5, base_delay=2.0)
async def fetch_external_api(url: str):
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### Benefits
- **Composable**: Stack multiple decorators
- **Non-Invasive**: No changes to original code
- **Reusable**: Apply to any LLM or function
- **Separation of Concerns**: Each decorator has single responsibility

---

## Template Method Pattern

### Purpose
**Define skeleton of an algorithm**, letting subclasses override specific steps.

### Use Cases in AgentHub
1. **Agent Execution Flow**: Common flow, custom steps
2. **Data Pipeline**: ETL with customizable transforms
3. **Report Generation**: Standard format, custom content

### Implementation

```python
# src/app/agent/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentContext:
    """Context passed through agent execution."""
    user_input: str
    session_id: str
    history: List[Dict[str, str]]
    metadata: Dict[str, Any]

@dataclass
class AgentResponse:
    """Response from agent execution."""
    output: str
    tool_calls: List[Dict[str, Any]]
    tokens_used: int
    metadata: Dict[str, Any]

class BaseAgent(ABC):
    """
    Template for agent execution flow.
    
    Defines the standard steps all agents follow:
    1. Prepare context
    2. Plan actions
    3. Execute tools
    4. Generate response
    5. Post-process
    
    Subclasses override specific steps.
    """
    
    def __init__(self, llm, tools: List = None):
        self.llm = llm
        self.tools = tools or []
    
    async def run(self, context: AgentContext) -> AgentResponse:
        """
        Template method defining the execution flow.
        
        This is the skeleton - subclasses don't override this.
        """
        # Step 1: Prepare
        prepared_context = await self.prepare_context(context)
        
        # Step 2: Plan
        plan = await self.create_plan(prepared_context)
        
        # Step 3: Execute tools (if needed)
        tool_results = []
        if plan.requires_tools:
            tool_results = await self.execute_tools(plan.tool_calls)
        
        # Step 4: Generate response
        response = await self.generate_response(
            prepared_context,
            tool_results
        )
        
        # Step 5: Post-process
        final_response = await self.post_process(response)
        
        return final_response
    
    # Template methods - subclasses override these
    
    async def prepare_context(self, context: AgentContext) -> AgentContext:
        """
        Prepare context for processing.
        
        Default implementation - subclasses can override.
        """
        return context
    
    @abstractmethod
    async def create_plan(self, context: AgentContext) -> 'ExecutionPlan':
        """
        Create execution plan (abstract - must override).
        
        Subclasses implement their planning strategy.
        """
        pass
    
    async def execute_tools(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute tool calls.
        
        Default implementation - can be overridden for custom logic.
        """
        results = []
        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call["arguments"]
            
            # Find and execute tool
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if tool:
                result = await tool.execute(**tool_args)
                results.append({
                    "tool": tool_name,
                    "result": result
                })
        
        return results
    
    @abstractmethod
    async def generate_response(
        self,
        context: AgentContext,
        tool_results: List[Dict[str, Any]]
    ) -> AgentResponse:
        """
        Generate final response (abstract - must override).
        
        Subclasses implement their response generation.
        """
        pass
    
    async def post_process(self, response: AgentResponse) -> AgentResponse:
        """
        Post-process response.
        
        Default implementation - can be overridden.
        """
        return response

@dataclass
class ExecutionPlan:
    """Plan created by agent."""
    requires_tools: bool
    tool_calls: List[Dict[str, Any]]
    reasoning: str

# Concrete implementation: ReAct Agent
class ReActAgent(BaseAgent):
    """
    ReAct (Reasoning + Acting) agent implementation.
    
    Overrides: create_plan, generate_response
    """
    
    async def create_plan(self, context: AgentContext) -> ExecutionPlan:
        """Create plan using ReAct reasoning."""
        # Build prompt with reasoning template
        prompt = f"""
        User: {context.user_input}
        
        Think step by step:
        1. What information do I need?
        2. What tools can help?
        3. What's my reasoning?
        
        Available tools: {[t.name for t in self.tools]}
        """
        
        # Get LLM to reason
        reasoning = await self.llm.generate(prompt)
        
        # Extract tool calls from reasoning
        tool_calls = self._parse_tool_calls(reasoning)
        
        return ExecutionPlan(
            requires_tools=len(tool_calls) > 0,
            tool_calls=tool_calls,
            reasoning=reasoning
        )
    
    async def generate_response(
        self,
        context: AgentContext,
        tool_results: List[Dict[str, Any]]
    ) -> AgentResponse:
        """Generate response incorporating tool results."""
        # Build final prompt
        prompt = f"""
        User question: {context.user_input}
        
        Tool results:
        {json.dumps(tool_results, indent=2)}
        
        Provide a comprehensive answer:
        """
        
        output = await self.llm.generate(prompt)
        
        return AgentResponse(
            output=output,
            tool_calls=tool_results,
            tokens_used=len(prompt.split()) + len(output.split()),
            metadata={"agent_type": "react"}
        )
    
    def _parse_tool_calls(self, reasoning: str) -> List[Dict[str, Any]]:
        """Parse tool calls from reasoning text."""
        # Implementation to extract tool calls
        pass

# Concrete implementation: Chain-of-Thought Agent
class ChainOfThoughtAgent(BaseAgent):
    """
    Chain-of-Thought agent implementation.
    
    Overrides: prepare_context, create_plan, generate_response
    """
    
    async def prepare_context(self, context: AgentContext) -> AgentContext:
        """Add CoT examples to context."""
        cot_examples = [
            {
                "question": "What is 25 * 4?",
                "reasoning": "Let's think: 25 * 4 = 25 * (2 * 2) = (25 * 2) * 2 = 50 * 2 = 100",
                "answer": "100"
            }
        ]
        
        context.metadata["cot_examples"] = cot_examples
        return context
    
    async def create_plan(self, context: AgentContext) -> ExecutionPlan:
        """Create plan with explicit reasoning steps."""
        prompt = f"""
        Question: {context.user_input}
        
        Let's think step by step:
        """
        
        reasoning = await self.llm.generate(prompt)
        
        return ExecutionPlan(
            requires_tools=False,  # CoT doesn't use tools
            tool_calls=[],
            reasoning=reasoning
        )
    
    async def generate_response(
        self,
        context: AgentContext,
        tool_results: List[Dict[str, Any]]
    ) -> AgentResponse:
        """Generate response with explicit reasoning."""
        plan = await self.create_plan(context)
        
        return AgentResponse(
            output=plan.reasoning,
            tool_calls=[],
            tokens_used=len(plan.reasoning.split()),
            metadata={"agent_type": "cot"}
        )
```

### Usage Example

```python
from src.app.agent.base import ReActAgent, ChainOfThoughtAgent, AgentContext
from src.app.llm.factory import LLMFactory

# Create LLM
llm = LLMFactory.create_llm(provider="openai", model="gpt-4")

# Create tools
tools = [jira_tool, datadog_tool, search_tool]

# Use ReAct agent
react_agent = ReActAgent(llm=llm, tools=tools)

context = AgentContext(
    user_input="Create a Jira ticket for the login bug",
    session_id="session-123",
    history=[],
    metadata={}
)

response = await react_agent.run(context)
print(response.output)

# Use Chain-of-Thought agent (same interface!)
cot_agent = ChainOfThoughtAgent(llm=llm, tools=[])
response = await cot_agent.run(context)
print(response.output)

# The execution flow is the same for both:
# 1. Prepare context (CoT adds examples)
# 2. Create plan (ReAct: tool-based, CoT: reasoning)
# 3. Execute tools (ReAct: yes, CoT: no)
# 4. Generate response (different strategies)
# 5. Post-process (same for both)
```

### Benefits
- **Consistent Flow**: All agents follow same steps
- **Flexible**: Override only what's needed
- **Maintainable**: Changes to flow affect all agents
- **Testable**: Test flow and steps independently

---

## Observer Pattern

### Purpose
**Define one-to-many dependency** where changes notify all dependents automatically.

### Use Cases in AgentHub
1. **Event System**: Notify listeners of agent events
2. **Metrics Collection**: Track system events
3. **Audit Logging**: Log all important actions

### Implementation

```python
# src/app/core/events.py

from typing import List, Callable, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum
import asyncio

class EventType(Enum):
    """Types of events in the system."""
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    TOOL_EXECUTED = "tool_executed"
    LLM_CALLED = "llm_called"
    ERROR_OCCURRED = "error_occurred"
    SESSION_CREATED = "session_created"

class Event:
    """Represents a system event."""
    
    def __init__(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ):
        self.event_type = event_type
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = time.time()

class EventListener(ABC):
    """Abstract base class for event listeners."""
    
    @abstractmethod
    async def handle_event(self, event: Event):
        """Handle an event."""
        pass

class LoggingListener(EventListener):
    """Listener that logs all events."""
    
    def __init__(self, logger):
        self.logger = logger
    
    async def handle_event(self, event: Event):
        self.logger.info(
            f"Event: {event.event_type.value}",
            extra={
                "event_data": event.data,
                "event_metadata": event.metadata,
                "timestamp": event.timestamp
            }
        )

class MetricsListener(EventListener):
    """Listener that collects metrics."""
    
    def __init__(self, metrics_client):
        self.metrics = metrics_client
    
    async def handle_event(self, event: Event):
        # Record event metric
        self.metrics.increment(
            f"events.{event.event_type.value}",
            tags={
                **event.metadata,
                "timestamp": event.timestamp
            }
        )
        
        # Record specific metrics based on event type
        if event.event_type == EventType.LLM_CALLED:
            self.metrics.histogram(
                "llm.latency",
                event.data.get("duration", 0)
            )
            self.metrics.increment(
                "llm.tokens",
                event.data.get("tokens_used", 0)
            )

class AuditListener(EventListener):
    """Listener that maintains audit trail."""
    
    def __init__(self, audit_db):
        self.audit_db = audit_db
    
    async def handle_event(self, event: Event):
        # Save to audit database
        await self.audit_db.insert({
            "event_type": event.event_type.value,
            "data": event.data,
            "metadata": event.metadata,
            "timestamp": event.timestamp
        })

class EventBus:
    """
    Central event bus for pub/sub messaging.
    
    Implements Observer pattern for system-wide events.
    """
    
    def __init__(self):
        self._listeners: Dict[EventType, List[EventListener]] = {}
        self._global_listeners: List[EventListener] = []
    
    def subscribe(
        self,
        event_type: EventType,
        listener: EventListener
    ):
        """Subscribe to specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
    
    def subscribe_all(self, listener: EventListener):
        """Subscribe to all events."""
        self._global_listeners.append(listener)
    
    def unsubscribe(
        self,
        event_type: EventType,
        listener: EventListener
    ):
        """Unsubscribe from event type."""
        if event_type in self._listeners:
            self._listeners[event_type].remove(listener)
    
    async def publish(self, event: Event):
        """
        Publish event to all subscribers.
        
        Notifies:
        1. Listeners subscribed to this event type
        2. Global listeners
        """
        listeners = []
        
        # Get specific listeners
        if event.event_type in self._listeners:
            listeners.extend(self._listeners[event.event_type])
        
        # Add global listeners
        listeners.extend(self._global_listeners)
        
        # Notify all listeners concurrently
        await asyncio.gather(
            *[listener.handle_event(event) for listener in listeners],
            return_exceptions=True
        )

# Global event bus instance
event_bus = EventBus()
```

### Usage Example

```python
from src.app.core.events import (
    event_bus,
    Event,
    EventType,
    LoggingListener,
    MetricsListener,
    AuditListener
)

# Setup listeners
import logging
logger = logging.getLogger(__name__)

# Subscribe listeners
event_bus.subscribe_all(LoggingListener(logger))
event_bus.subscribe(EventType.LLM_CALLED, MetricsListener(metrics_client))
event_bus.subscribe(EventType.TOOL_EXECUTED, AuditListener(audit_db))

# In agent code - publish events
class InstrumentedAgent:
    async def run(self, context):
        # Publish start event
        await event_bus.publish(Event(
            event_type=EventType.AGENT_STARTED,
            data={"session_id": context.session_id},
            metadata={"user_id": context.user_id}
        ))
        
        try:
            # Execute agent logic
            response = await self._execute(context)
            
            # Publish completion event
            await event_bus.publish(Event(
                event_type=EventType.AGENT_COMPLETED,
                data={
                    "session_id": context.session_id,
                    "tokens_used": response.tokens_used
                }
            ))
            
            return response
            
        except Exception as e:
            # Publish error event
            await event_bus.publish(Event(
                event_type=EventType.ERROR_OCCURRED,
                data={
                    "error": str(e),
                    "session_id": context.session_id
                }
            ))
            raise

# All subscribed listeners are automatically notified:
# - LoggingListener logs the event
# - MetricsListener records metrics
# - AuditListener saves to database
```

### Benefits
- **Decoupled**: Publishers don't know about subscribers
- **Extensible**: Add new listeners without changing publishers
- **Async**: Non-blocking event processing
- **Centralized**: Single event bus for entire system

---

## Dependency Injection

### Purpose
**Invert control of dependencies**, making code more flexible and testable.

### Use Cases in AgentHub
1. **Service Dependencies**: Inject services into controllers
2. **Configuration Injection**: Pass settings to components
3. **Test Mocking**: Replace real services with mocks

### Implementation

```python
# src/app/core/di.py

from typing import TypeVar, Type, Callable, Dict, Any
from functools import wraps

T = TypeVar('T')

class Container:
    """
    Dependency injection container.
    
    Manages service lifecycle and dependencies.
    """
    
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
    
    def register_singleton(self, interface: Type[T], instance: T):
        """Register a singleton instance."""
        self._singletons[interface] = instance
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]):
        """Register a factory function."""
        self._factories[interface] = factory
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency."""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Try factories
        if interface in self._factories:
            return self._factories[interface]()
        
        raise ValueError(f"No registration found for {interface}")
    
    def resolve_all(self, *interfaces: Type) -> tuple:
        """Resolve multiple dependencies."""
        return tuple(self.resolve(interface) for interface in interfaces)

# Global container
container = Container()

# Decorator for dependency injection
def inject(*dependencies: Type):
    """
    Decorator to inject dependencies into function.
    
    Example:
        @inject(DatabaseService, LLMService)
        async def process_request(db: DatabaseService, llm: LLMService):
            # Use injected services
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Resolve dependencies
            resolved = container.resolve_all(*dependencies)
            
            # Call with injected dependencies
            return await func(*args, *resolved, **kwargs)
        
        return wrapper
    return decorator
```

### Usage Example

```python
from src.app.core.di import container, inject
from src.app.services.jira_service import JiraService
from src.app.services.datadog_service import DatadogService
from src.app.llm.factory import LLMFactory

# Register services at startup
def setup_di():
    # Register singletons
    container.register_singleton(
        JiraService,
        JiraService(settings.jira)
    )
    
    container.register_singleton(
        DatadogService,
        DatadogService(settings.datadog)
    )
    
    # Register factories
    container.register_factory(
        LLMFactory,
        lambda: LLMFactory.create_llm(
            provider=settings.llm.default_provider,
            **settings.llm.get_provider_config()
        )
    )

# Use dependency injection
@inject(JiraService, LLMFactory)
async def create_ticket_with_ai(
    user_input: str,
    jira: JiraService,
    llm: LLMFactory
):
    """Function with injected dependencies."""
    # Use LLM to generate ticket details
    prompt = f"Generate Jira ticket for: {user_input}"
    ticket_details = await llm.generate(prompt)
    
    # Use Jira service to create ticket
    issue = await jira.create_issue(**ticket_details)
    return issue

# In FastAPI endpoint
from fastapi import Depends

def get_jira_service() -> JiraService:
    """FastAPI dependency."""
    return container.resolve(JiraService)

@app.post("/tickets")
async def create_ticket(
    request: TicketRequest,
    jira: JiraService = Depends(get_jira_service)
):
    """Endpoint with injected service."""
    issue = await jira.create_issue(
        project=request.project,
        summary=request.summary
    )
    return {"issue_key": issue.key}

# Testing with mocks
import pytest
from unittest.mock import AsyncMock

def test_create_ticket():
    # Replace real service with mock
    mock_jira = AsyncMock(spec=JiraService)
    mock_jira.create_issue.return_value = {"key": "TEST-123"}
    
    container.register_singleton(JiraService, mock_jira)
    
    # Test function with mocked dependency
    result = await create_ticket_with_ai("Fix bug")
    assert result["key"] == "TEST-123"
    mock_jira.create_issue.assert_called_once()
```

### Benefits
- **Testability**: Easy to mock dependencies
- **Flexibility**: Swap implementations
- **Decoupling**: Components don't create dependencies
- **Lifecycle Management**: Control singleton vs factory

---

## Pattern Combinations

### Real-World Example: Production LLM Service

Combining multiple patterns for a robust service:

```python
# Combines: Singleton + Factory + Decorator + Observer

from src.app.core.config import get_settings  # Singleton
from src.app.llm.factory import LLMFactory  # Factory
from src.app.llm.decorators import CachedLLM, RetryLLM, MonitoredLLM  # Decorator
from src.app.core.events import event_bus, Event, EventType  # Observer

class ProductionLLMService:
    """
    Production-ready LLM service combining patterns:
    - Singleton: Single service instance
    - Factory: Create appropriate LLM
    - Decorator: Add caching, retry, monitoring
    - Observer: Publish events
    """
    
    _instance = None  # Singleton
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        settings = get_settings()  # Singleton settings
        
        # Factory: Create base LLM
        base_llm = LLMFactory.create_llm(
            provider=settings.llm.default_provider,
            **settings.llm.get_provider_config()
        )
        
        # Decorator: Add layers
        cached = CachedLLM(base_llm, ttl=3600)
        retried = RetryLLM(cached, max_retries=3)
        self.llm = MonitoredLLM(retried)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate with full production stack."""
        # Observer: Publish start event
        await event_bus.publish(Event(
            event_type=EventType.LLM_CALLED,
            data={"prompt_length": len(prompt)}
        ))
        
        try:
            response = await self.llm.generate(prompt, **kwargs)
            
            # Observer: Publish success event
            await event_bus.publish(Event(
                event_type=EventType.LLM_COMPLETED,
                data={"response_length": len(response)}
            ))
            
            return response
            
        except Exception as e:
            # Observer: Publish error event
            await event_bus.publish(Event(
                event_type=EventType.ERROR_OCCURRED,
                data={"error": str(e)}
            ))
            raise

# Usage is simple despite complex internals
service = ProductionLLMService()  # Singleton
response = await service.generate("Explain RAG")
# Internally uses: Factory + Decorators + Observer
```

---

## Summary

| Pattern | Purpose | Use in AgentHub | Benefit |
|---------|---------|-----------------|---------|
| **Registry** | Dynamic registration | Tools, providers | Easy extension |
| **Factory** | Object creation | LLMs, sessions | Provider agnostic |
| **Singleton** | Single instance | Config, connections | Resource efficiency |
| **Strategy** | Interchangeable algorithms | Chunking, embeddings | Runtime flexibility |
| **Decorator** | Add functionality | Caching, retry, monitoring | Composable features |
| **Template Method** | Algorithm skeleton | Agent execution | Consistent flow |
| **Observer** | Event notification | Metrics, logging, audit | Decoupled monitoring |
| **Dependency Injection** | Inversion of control | Service dependencies | Testability |

---

## Related Documentation

- **[Architecture Overview](./overview.md)**: System architecture
- **[Configuration System](./configuration-system.md)**: Settings management
- **[Core Concepts](../core-concepts/llm-basics.md)**: LLM fundamentals
- **[RAG Pipeline](../core-concepts/rag-pipeline.md)**: More working implementations

---

**Last Updated**: January 8, 2026  
**Maintainer**: AgentHub Team  
**Status**: Production patterns
