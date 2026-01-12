# Configuration System ⭐

> **Flexible YAML-based configuration** with `settings.profile_name` dictionary access pattern

## Table of Contents
- [Quick Start](#quick-start)
- [Overview](#overview)
- [The Magic: settings.profile_name](#the-magic-settingsprofile_name)
- [Architecture](#architecture)
- [Configuration Files](#configuration-files)
- [Type Safety](#type-safety)
- [Profile Management](#profile-management)
- [Environment Variables](#environment-variables)
- [Dynamic Loading](#dynamic-loading)
- [Validation](#validation)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Quick Start

**Access any configuration profile as a dictionary:**

```python
from app.core.config import Settings

settings = Settings.instance()

# Get entire profiles as dictionaries
llm_config = settings.llm          # All LLM settings
db_config = settings.db            # All database settings  
vector_config = settings.vector    # All vector store settings

# Access nested values
provider = llm_config['default_provider']
api_key = llm_config['providers']['openai']['api_key']
temperature = llm_config['temperature']
```

**For detailed resources/ directory guide, see: [Resources Directory Guide](../guides/configuration/resources-directory.md)**

---

## Overview

AgentHub's configuration system is a **star feature** that makes the application:
- **Flexible**: Change settings without code changes
- **Type-Safe**: Pydantic models ensure correctness
- **Environment-Aware**: Different configs for dev/test/prod
- **Modular**: Split configuration by concern
- **Validated**: Comprehensive validation before startup

### Key Benefits

| Feature | Benefit | Example |
|---------|---------|---------|
| **YAML-Based** | Human-readable, easy to edit | See configs in `resources/` |
| **Type-Safe** | Catch errors at load time | Pydantic models |
| **Profile System** | Environment-specific settings | Dev vs prod |
| **Hot Reload** | Update without restart | Dynamic loading |
| **Validation** | Fail fast on invalid config | Startup checks |
| **Secret Management** | Secure credential handling | Environment variables |

---

## The Magic: `settings.profile_name`

### How It Works

Every YAML file in `resources/` becomes **automatically accessible** as a dictionary attribute on the settings object:

```python
resources/application-llm.yaml      →  settings.llm       (dict)
resources/application-db.yaml       →  settings.db        (dict)
resources/application-vector.yaml   →  settings.vector    (dict)
resources/application-prompt.yaml   →  settings.prompt    (dict)
```

### The Pattern

```
Filename Pattern:          application-{profile-name}.yaml
Python Access Pattern:     settings.{profile_name}
Return Type:               Dictionary (dict)

Note: Hyphens (-) in filenames become underscores (_) in Python
```

### Example: Complete Flow

**1. Create YAML File**: `resources/application-llm.yaml`
```yaml
llm:
  default_provider: "openai"
  temperature: 0.1
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4"
```

**2. Access in Python**:
```python
from app.core.config import Settings

settings = Settings.instance()

# Get entire profile as dictionary
llm_config = settings.llm
print(type(llm_config))  # <class 'dict'>

# Access any key
provider = llm_config['default_provider']        # 'openai'
temperature = llm_config['temperature']          # 0.1
openai = llm_config['providers']['openai']
api_key = openai['api_key']                      # Reads from env var
model = openai['model']                          # 'gpt-4'
```

### Why This is Powerful

| Feature | Benefit | Example |
|---------|---------|---------|
| **Flexible** | Access entire config as dict | `settings.llm` returns everything |
| **No Boilerplate** | No need to define Python classes | Just add YAML file |
| **Dynamic** | Add new profiles without code changes | Create `application-custom.yaml` |
| **Type-Agnostic** | Works with any YAML structure | Nested dicts, lists, values |
| **Environment Aware** | Override with env vars | `${VAR:default}` syntax |

### Real Usage Example

```python
from app.core.config import Settings
from app.llm.factory.llm_factory import LLMFactory

settings = Settings.instance()

# Method 1: Dictionary access
llm_config = settings.llm
provider_name = llm_config['default_provider']
provider_settings = llm_config['providers'][provider_name]

# Method 2: Dot notation (also works!)
provider_name = settings.llm.default_provider
provider_settings = settings.llm.providers[provider_name]

# All ${ENV_VAR} patterns are automatically resolved!
# No need to manually check environment variables
temperature = provider_settings['temperature']  # Already has actual value
api_key = provider_settings['api_key']          # Already resolved from env

# Use configuration to initialize
llm = LLMFactory.get_llm(provider_name)
response = await llm.generate(
    messages=["Hello"],
    temperature=temperature,
    max_tokens=provider_settings.get('max_tokens', 1000)
)
```

### Key Features

**Flexible Access**: Use `settings.llm` (dict) OR `settings.llm.temperature` (dot notation)  
**Auto Environment Variables**: `${VAR_NAME}` automatically resolved from environment  
**Default Values**: `${VAR_NAME:default}` provides fallback if not set  
**No Boilerplate**: Just add YAML file, access immediately  
**Type Safe**: Values validated at load time  

**Complete Guide**: See [Resources Directory Guide](../guides/configuration/resources-directory.md) for 40+ examples

---

## Architecture

### Configuration Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  Uses: get_settings() → type-safe access to all configs │
└───────────────────────────────┬─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────┐
│                   Settings Models                        │
│  Pydantic models: AppSettings, LLMSettings, DBSettings  │
└───────────────────────────────┬─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────┐
│                  Configuration Loader                    │
│  Loads YAML files, merges profiles, validates schemas   │
└───────────────────────────────┬─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────┐
│                    YAML Files                           │
│  application-*.yaml files in resources/ directory       │
└───────────────────────────────┬─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────┐
│                 Environment Variables                    │
│  Overrides from .env file and system environment        │
└─────────────────────────────────────────────────────────┘
```

### Loading Priority (Highest to Lowest)

1. **Environment Variables**: `OPENAI_API_KEY=xxx`
2. **Profile-Specific Config**: `profiles.prod.llm.model`
3. **Base Config**: `llm.default_model`
4. **Default Values**: Defined in Pydantic models

---

## Configuration Files

### File Organization

```
resources/
├── application-app.yaml           # Application metadata
├── application-context.yaml       # Context window management
├── application-data-sources.yaml  # Database connections
├── application-db.yaml            # Database settings
├── application-embeddings.yaml    # Embedding configuration
├── application-external.yaml      # External services
├── application-llm.yaml           # LLM providers
├── application-prompt.yaml        # Prompt templates
└── application-vector.yaml        # Vector store settings
```

### 1. Application Config (`application-app.yaml`)

```yaml
app:
  name: "agenthub"
  version: "1.0.0"
  environment: "${APP_ENV:dev}"  # dev, test, prod
  debug: ${DEBUG:false}
  
  # Server settings
  server:
    host: "0.0.0.0"
    port: 8000
    reload: ${RELOAD:false}
    workers: ${WORKERS:1}
  
  # Logging configuration
  logging:
    level: "${LOG_LEVEL:INFO}"
    format: "json"  # json or text
    output: "stdout"  # stdout or file
    file_path: "logs/app.log"
  
  # CORS settings
  cors:
    enabled: true
    allowed_origins:
      - "http://localhost:3000"
      - "https://yourdomain.com"
    allowed_methods:
      - "GET"
      - "POST"
      - "PUT"
      - "DELETE"
    allowed_headers:
      - "*"
  
  # Profiles for different environments
  profiles:
    dev:
      debug: true
      server:
        reload: true
        workers: 1
      logging:
        level: "DEBUG"
    
    test:
      debug: false
      server:
        reload: false
        workers: 1
      logging:
        level: "INFO"
    
    prod:
      debug: false
      server:
        reload: false
        workers: 4
      logging:
        level: "WARNING"
      cors:
        allowed_origins:
          - "https://yourdomain.com"
```

### 2. LLM Config (`application-llm.yaml`)

```yaml
llm:
  # Default provider
  default_provider: "${LLM_PROVIDER:openai}"
  
  # OpenAI configuration
  openai:
    api_key: "${OPENAI_API_KEY}"
    organization: "${OPENAI_ORG:}"
    models:
      chat: "gpt-4-turbo-preview"
      embeddings: "text-embedding-3-small"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
  
  # Azure OpenAI configuration
  azure:
    api_key: "${AZURE_OPENAI_API_KEY}"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    api_version: "2024-02-15-preview"
    deployments:
      chat: "gpt-4"
      embeddings: "text-embedding-ada-002"
    temperature: 0.7
    max_tokens: 4000
  
  # Anthropic configuration
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-opus-20240229"
    max_tokens: 4000
    temperature: 0.7
  
  # Fallback configuration
  fallback:
    enabled: true
    providers:
      - openai
      - azure
      - anthropic
    retry_delay: 2.0
  
  # Rate limiting
  rate_limit:
    requests_per_minute: 60
    tokens_per_minute: 90000
  
  # Caching
  cache:
    enabled: true
    ttl: 3600
    backend: "redis"  # redis or memory
  
  # Profiles
  profiles:
    dev:
      openai:
        models:
          chat: "gpt-3.5-turbo"
      cache:
        backend: "memory"
    
    prod:
      fallback:
        enabled: true
      rate_limit:
        requests_per_minute: 1000
        tokens_per_minute: 1500000
```

### 3. Database Config (`application-db.yaml`)

```yaml
database:
  # PostgreSQL configuration
  postgres:
    url: "${DATABASE_URL}"
    pool_size: 20
    max_overflow: 10
    pool_timeout: 30
    pool_recycle: 3600
    echo: ${DB_ECHO:false}
  
  # MongoDB configuration
  mongodb:
    url: "${MONGODB_URL}"
    database: "${MONGODB_DB:agenthub}"
    collections:
      sessions: "sessions"
      conversations: "conversations"
      users: "users"
    pool_size: 100
    max_idle_time: 10000
  
  # Redis configuration
  redis:
    url: "${REDIS_URL:redis://localhost:6379}"
    db: 0
    max_connections: 50
    socket_timeout: 5
    socket_connect_timeout: 5
    decode_responses: true
  
  # Profiles
  profiles:
    dev:
      postgres:
        url: "postgresql://postgres:postgres@localhost:5432/agenthub_dev"
        echo: true
      mongodb:
        url: "mongodb://localhost:27017"
      redis:
        url: "redis://localhost:6379"
    
    test:
      postgres:
        url: "postgresql://postgres:postgres@localhost:5432/agenthub_test"
      mongodb:
        database: "agenthub_test"
      redis:
        db: 1
    
    prod:
      postgres:
        pool_size: 50
        max_overflow: 20
      mongodb:
        pool_size: 200
      redis:
        max_connections: 100
```

### 4. External Services Config (`application-external.yaml`)

```yaml
external:
  # Jira configuration
  jira:
    enabled: ${JIRA_ENABLED:false}
    url: "${JIRA_URL}"
    username: "${JIRA_USERNAME}"
    api_token: "${JIRA_API_TOKEN}"
    default_project: "${JIRA_PROJECT:}"
    timeout: 30
  
  # Confluence configuration
  confluence:
    enabled: ${CONFLUENCE_ENABLED:false}
    url: "${CONFLUENCE_URL}"
    username: "${CONFLUENCE_USERNAME}"
    api_token: "${CONFLUENCE_API_TOKEN}"
    default_space: "${CONFLUENCE_SPACE:}"
    timeout: 30
  
  # Datadog configuration
  datadog:
    enabled: ${DATADOG_ENABLED:false}
    api_key: "${DATADOG_API_KEY}"
    app_key: "${DATADOG_APP_KEY}"
    site: "${DATADOG_SITE:datadoghq.com}"
    timeout: 30
  
  # Slack configuration
  slack:
    enabled: ${SLACK_ENABLED:false}
    bot_token: "${SLACK_BOT_TOKEN}"
    app_token: "${SLACK_APP_TOKEN}"
    signing_secret: "${SLACK_SIGNING_SECRET}"
```

### 5. Vector Store Config (`application-vector.yaml`)

```yaml
vector:
  # Default vector store
  default_store: "${VECTOR_STORE:pinecone}"
  
  # Pinecone configuration
  pinecone:
    api_key: "${PINECONE_API_KEY}"
    environment: "${PINECONE_ENV:us-west1-gcp}"
    index_name: "${PINECONE_INDEX:agenthub}"
    dimension: 1536
    metric: "cosine"
    namespace: "default"
  
  # Weaviate configuration
  weaviate:
    url: "${WEAVIATE_URL:http://localhost:8080}"
    api_key: "${WEAVIATE_API_KEY:}"
    class_name: "Document"
    timeout: 30
  
  # Qdrant configuration
  qdrant:
    url: "${QDRANT_URL:http://localhost:6333}"
    api_key: "${QDRANT_API_KEY:}"
    collection_name: "documents"
    vector_size: 1536
    distance: "cosine"
```

### 6. Context Window Config (`application-context.yaml`)

```yaml
context:
  # Token limits per model
  limits:
    gpt-4-turbo-preview:
      max_tokens: 128000
      reserved_output: 4000
    gpt-4:
      max_tokens: 8192
      reserved_output: 2000
    gpt-3.5-turbo:
      max_tokens: 16385
      reserved_output: 2000
    claude-3-opus:
      max_tokens: 200000
      reserved_output: 4000
  
  # Truncation strategy
  truncation:
    strategy: "sliding_window"  # sliding_window, summarize, remove_oldest
    keep_system: true
    keep_recent: 5
  
  # Summarization (when strategy is 'summarize')
  summarization:
    enabled: true
    model: "gpt-3.5-turbo"
    prompt_template: "Summarize this conversation concisely:\n\n{conversation}"
    max_summary_tokens: 500
```

### 7. Prompt Templates (`application-prompt.yaml`)

```yaml
prompts:
  # System prompts
  system:
    default: |
      You are a helpful AI assistant powered by AgentHub.
      You have access to various tools to help users.
      Always be concise, accurate, and helpful.
    
    conversational: |
      You are a friendly AI assistant in a conversation.
      Ask clarifying questions when needed.
      Maintain context throughout the conversation.
  
  # Task-specific prompts
  tasks:
    jira_ticket:
      template: |
        Based on the user's description:
        "{user_input}"
        
        Generate a Jira ticket with:
        - Summary (concise title)
        - Description (detailed)
        - Issue Type (Bug/Task/Story)
        - Priority (High/Medium/Low)
        
        Return as JSON.
      
      output_schema:
        type: object
        properties:
          summary:
            type: string
          description:
            type: string
          issue_type:
            type: string
            enum: ["Bug", "Task", "Story"]
          priority:
            type: string
            enum: ["High", "Medium", "Low"]
    
    code_review:
      template: |
        Review the following code for:
        1. Best practices
        2. Potential bugs
        3. Performance issues
        4. Security concerns
        
        Code:
        ```{language}
        {code}
        ```
        
        Provide constructive feedback.
```

---

## Type Safety

### Pydantic Models

AgentHub uses **Pydantic** for type-safe configuration with automatic validation.

```python
# src/app/core/config/models.py

from pydantic import BaseSettings, Field, validator
from typing import List, Dict, Optional
from enum import Enum

class Environment(str, Enum):
    """Application environment."""
    DEV = "dev"
    TEST = "test"
    PROD = "prod"

class ServerSettings(BaseSettings):
    """Server configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, gt=0, lt=65536)
    reload: bool = Field(default=False)
    workers: int = Field(default=1, gt=0)
    
    @validator('port')
    def validate_port(cls, v):
        if v < 1024 and v != 8000:
            raise ValueError("Avoid using privileged ports")
        return v

class LoggingSettings(BaseSettings):
    """Logging configuration."""
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    output: str = Field(default="stdout")
    file_path: Optional[str] = None
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Level must be one of {valid_levels}")
        return v.upper()

class CORSSettings(BaseSettings):
    """CORS configuration."""
    enabled: bool = Field(default=True)
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    allowed_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"]
    )
    allowed_headers: List[str] = Field(default_factory=lambda: ["*"])

class AppSettings(BaseSettings):
    """Application configuration."""
    name: str = Field(default="agenthub")
    version: str = Field(default="1.0.0")
    environment: Environment = Field(default=Environment.DEV)
    debug: bool = Field(default=False)
    
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class LLMProviderSettings(BaseSettings):
    """LLM provider configuration."""
    api_key: str = Field(..., min_length=1)  # Required
    organization: Optional[str] = None
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, gt=0)
    timeout: int = Field(default=60, gt=0)
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or v == "":
            raise ValueError("API key is required")
        return v

class LLMSettings(BaseSettings):
    """LLM configuration."""
    default_provider: str = Field(default="openai")
    openai: Optional[LLMProviderSettings] = None
    azure: Optional[Dict] = None
    anthropic: Optional[Dict] = None
    
    @validator('default_provider')
    def validate_provider(cls, v, values):
        valid_providers = ["openai", "azure", "anthropic"]
        if v not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v

class DatabaseSettings(BaseSettings):
    """Database configuration."""
    postgres_url: str = Field(..., alias="DATABASE_URL")
    mongodb_url: str = Field(..., alias="MONGODB_URL")
    redis_url: str = Field(default="redis://localhost:6379")
    
    @validator('postgres_url')
    def validate_postgres_url(cls, v):
        if not v.startswith('postgresql://'):
            raise ValueError("Invalid PostgreSQL URL")
        return v
    
    @validator('mongodb_url')
    def validate_mongodb_url(cls, v):
        if not v.startswith('mongodb://'):
            raise ValueError("Invalid MongoDB URL")
        return v

class Settings(BaseSettings):
    """Root settings class."""
    app: AppSettings = Field(default_factory=AppSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Type-Safe Access

```python
from src.app.core.config import get_settings

# Get settings (singleton)
settings = get_settings()

# Type-safe access with autocomplete
api_key: str = settings.llm.openai.api_key
port: int = settings.app.server.port
debug: bool = settings.app.debug

# IDE knows the types and provides:
# - Autocomplete
# - Type hints
# - Error checking
```

---

## Profile Management

### Profile System

Profiles allow environment-specific configuration without code changes.

```yaml
# Base configuration
app:
  name: "agenthub"
  debug: false
  
  # Profile-specific overrides
  profiles:
    dev:
      debug: true
      logging:
        level: "DEBUG"
    
    test:
      debug: false
      logging:
        level: "INFO"
    
    prod:
      debug: false
      logging:
        level: "WARNING"
```

### Profile Loading

```python
# src/app/core/config/loader.py

import os
import yaml
from typing import Dict, Any

class ConfigLoader:
    """Load and merge configuration with profile support."""
    
    def __init__(self, config_dir: str = "resources"):
        self.config_dir = config_dir
        self.environment = os.getenv("APP_ENV", "dev")
    
    def load(self) -> Dict[str, Any]:
        """Load configuration with profile merging."""
        config = {}
        
        # Load all YAML files
        for file in os.listdir(self.config_dir):
            if file.endswith('.yaml'):
                file_path = os.path.join(self.config_dir, file)
                with open(file_path) as f:
                    data = yaml.safe_load(f)
                    config = self._deep_merge(config, data)
        
        # Apply profile overrides
        config = self._apply_profile(config, self.environment)
        
        # Replace environment variables
        config = self._substitute_env_vars(config)
        
        return config
    
    def _apply_profile(
        self,
        config: Dict[str, Any],
        environment: str
    ) -> Dict[str, Any]:
        """Apply profile-specific overrides."""
        result = config.copy()
        
        for key, value in config.items():
            if isinstance(value, dict) and 'profiles' in value:
                profiles = value.pop('profiles')
                
                if environment in profiles:
                    # Merge profile config
                    profile_config = profiles[environment]
                    result[key] = self._deep_merge(value, profile_config)
        
        return result
    
    def _deep_merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Replace ${VAR:default} with environment values."""
        if isinstance(config, dict):
            return {
                key: self._substitute_env_vars(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${'):
            # Extract variable name and default
            var_spec = config[2:-1]  # Remove ${ and }
            
            if ':' in var_spec:
                var_name, default = var_spec.split(':', 1)
            else:
                var_name, default = var_spec, None
            
            return os.getenv(var_name, default)
        
        return config
```

### Usage

```bash
# Development
export APP_ENV=dev
python -m src.app.main

# Testing
export APP_ENV=test
pytest

# Production
export APP_ENV=prod
python -m src.app.main
```

---

## Environment Variables

### `.env` File

```bash
# .env

# Application
APP_ENV=dev
DEBUG=true
LOG_LEVEL=DEBUG

# LLM Providers
OPENAI_API_KEY=sk-xxx
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com
ANTHROPIC_API_KEY=sk-ant-xxx

# Databases
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenthub
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# External Services
JIRA_ENABLED=true
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=user@example.com
JIRA_API_TOKEN=xxx

DATADOG_ENABLED=true
DATADOG_API_KEY=xxx
DATADOG_APP_KEY=xxx
```

### `.env.example` (Committed to Git)

```bash
# .env.example - Template for environment variables

# Application
APP_ENV=dev
DEBUG=false
LOG_LEVEL=INFO

# LLM Providers
OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com

# Databases
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# External Services (optional)
JIRA_ENABLED=false
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
```

### Security Best Practices

1. **Never commit `.env`**: Add to `.gitignore`
2. **Use `.env.example`**: Template for documentation
3. **Rotate secrets regularly**: Update API keys periodically
4. **Use secret managers**: AWS Secrets Manager, Azure Key Vault
5. **Validate at startup**: Fail fast on missing secrets

---

## Dynamic Loading

### Hot Reload Configuration

```python
# src/app/core/config/watcher.py

import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable

class ConfigWatcher(FileSystemEventHandler):
    """Watch configuration files for changes."""
    
    def __init__(
        self,
        config_dir: str,
        on_change: Callable[[str], None]
    ):
        self.config_dir = config_dir
        self.on_change = on_change
    
    def on_modified(self, event):
        """Handle file modification."""
        if event.src_path.endswith('.yaml'):
            print(f"Config changed: {event.src_path}")
            self.on_change(event.src_path)

async def watch_config(config_dir: str, reload_callback: Callable):
    """Watch configuration directory for changes."""
    event_handler = ConfigWatcher(config_dir, reload_callback)
    observer = Observer()
    observer.schedule(event_handler, config_dir, recursive=False)
    observer.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Usage in application
async def reload_config(file_path: str):
    """Reload configuration when file changes."""
    global settings
    settings = load_config()
    print("Configuration reloaded!")

# Start watcher
if settings.app.environment == "dev":
    asyncio.create_task(watch_config("resources", reload_config))
```

---

## Validation

### Startup Validation

```python
# src/app.core/config/validator.py

from typing import List, Tuple
from pydantic import ValidationError

class ConfigValidator:
    """Validate configuration at startup."""
    
    @staticmethod
    def validate_settings(settings: Settings) -> Tuple[bool, List[str]]:
        """
        Validate all settings.
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check required API keys
        if settings.llm.default_provider == "openai":
            if not settings.llm.openai or not settings.llm.openai.api_key:
                errors.append("OpenAI API key is required")
        
        # Check database connections
        if not settings.database.postgres_url:
            errors.append("PostgreSQL URL is required")
        
        if not settings.database.mongodb_url:
            errors.append("MongoDB URL is required")
        
        # Check external services
        if settings.external.jira.enabled:
            if not settings.external.jira.api_token:
                errors.append("Jira API token required when Jira is enabled")
        
        # Validate port ranges
        if settings.app.server.port < 1024 and settings.app.server.port != 8000:
            errors.append("Avoid using privileged ports")
        
        return (len(errors) == 0, errors)

# In main.py
from src.app.core.config import get_settings, ConfigValidator

settings = get_settings()
is_valid, errors = ConfigValidator.validate_settings(settings)

if not is_valid:
    print("Configuration validation failed:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
```

---

## Best Practices

### 1. **Organize by Concern**

**Good**: Separate files for different domains
```
application-llm.yaml        # LLM configuration
application-db.yaml         # Database configuration
application-external.yaml   # External services
```

**Bad**: Everything in one file
```
application.yaml  # 1000+ lines
```

### 2. **Use Environment Variables for Secrets**

**Good**:
```yaml
llm:
  openai:
    api_key: "${OPENAI_API_KEY}"  # From environment
```

**Bad**:
```yaml
llm:
  openai:
    api_key: "sk-xxx"  # Hardcoded secret
```

### 3. **Provide Defaults**

**Good**:
```yaml
llm:
  temperature: ${LLM_TEMPERATURE:0.7}  # Default: 0.7
```

**Bad**:
```yaml
llm:
  temperature: ${LLM_TEMPERATURE}  # No default
```

### 4. **Document Configuration**

```yaml
llm:
  # Temperature controls randomness (0.0 = deterministic, 2.0 = very random)
  # Recommended: 0.7 for creative tasks, 0.3 for factual tasks
  temperature: 0.7
```

### 5. **Validate Early**

```python
# Validate at startup, not at runtime
settings = get_settings()
ConfigValidator.validate_settings(settings)  # Fail fast
```

### 6. **Use Type-Safe Models**

```python
# Type-safe access
settings.llm.openai.api_key  # IDE autocomplete

# Avoid dictionary access
settings["llm"]["openai"]["api_key"]  # No type safety
```

---

## Examples

### Example 1: Get Configuration

```python
from src.app.core.config import get_settings

settings = get_settings()

# Access app settings
print(f"App: {settings.app.name} v{settings.app.version}")
print(f"Environment: {settings.app.environment}")
print(f"Debug: {settings.app.debug}")

# Access LLM settings
print(f"LLM Provider: {settings.llm.default_provider}")
print(f"Model: {settings.llm.openai.model}")

# Access database settings
print(f"PostgreSQL: {settings.database.postgres_url}")
print(f"MongoDB: {settings.database.mongodb_url}")
```

### Example 2: Runtime Provider Selection

```python
from src.app.llm.factory import LLMFactory
from src.app.core.config import get_settings

settings = get_settings()

# Create LLM based on configuration
llm = LLMFactory.create_llm(
    provider=settings.llm.default_provider,
    **settings.llm.get_provider_config()
)

# Use the LLM
response = await llm.generate("Hello!")
```

### Example 3: Environment-Specific Behavior

```python
from src.app.core.config import get_settings

settings = get_settings()

if settings.app.environment == "dev":
    # Development behavior
    print("Debug logs enabled")
    app = create_app(reload=True)
elif settings.app.environment == "prod":
    # Production behavior
    print("Production mode")
    app = create_app(workers=settings.app.server.workers)
```

### Example 4: Update Configuration at Runtime

```python
from src.app.core.config import get_settings, set_settings

# Get current settings
settings = get_settings()

# Modify settings
settings.llm.temperature = 0.9
settings.llm.max_tokens = 2000

# Apply changes (in dev mode only)
if settings.app.environment == "dev":
    set_settings(settings)
```

---

## Related Documentation

- **[Architecture Overview](./overview.md)**: System architecture
- **[Design Patterns](./design-patterns.md)**: Configuration patterns
- **[Deployment Guide](../deployment/overview.md)**: Production configuration
- **[Quick Start](../getting-started/quick-start.md)**: Configuration in practice

---

## Troubleshooting

### Common Issues

**1. Missing Environment Variables**

```
Error: Field required [type=missing, input_value={}, input_type=dict]
```

**Solution**: Check `.env` file and ensure all required variables are set.

**2. Invalid Configuration Value**

```
ValidationError: temperature must be between 0.0 and 2.0
```

**Solution**: Fix the value in YAML file or environment variable.

**3. Configuration Not Loading**

```
FileNotFoundError: resources/application-llm.yaml
```

**Solution**: Ensure YAML files exist in `resources/` directory.

---

**Last Updated**: January 8, 2026  
**Maintainer**: AgentHub Team  
**Status**: Production configuration system
