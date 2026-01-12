# Configuration System Guide

> **Comprehensive guide** to AgentHub's flexible, YAML-based configuration system with automatic discovery and multiple access patterns

## Table of Contents

### Overview
- [What is the Configuration System?](#what-is-the-configuration-system)
- [Key Features](#key-features)
- [Quick Start](#quick-start)

### Architecture
- [System Architecture](#system-architecture)
  - [Framework Layer](#framework-layer)
  - [Providers Layer](#providers-layer)
  - [Application Layer](#application-layer)
  - [Utils Layer](#utils-layer)
- [Configuration Flow](#configuration-flow)

### Configuration Files
- [All Configuration Files](#all-configuration-files)
  - [Application Configurations](#application-configurations)
  - [Provider Configurations](#provider-configurations)

### Usage Patterns
- [Access Patterns](#access-patterns)
  - [Pattern 1: Centralized Settings](#pattern-1-centralized-settings-recommended)
  - [Pattern 2: Domain-Specific Configs](#pattern-2-domain-specific-configs)
- [Choosing Your Pattern](#choosing-your-pattern)

### Advanced Topics
- [Automatic YAML Discovery](#automatic-yaml-discovery)
- [Environment Variables](#environment-variables)
- [Profile Control](#profile-control)
- [Configuration Registry](#configuration-registry)

### Best Practices
- [Configuration Best Practices](#configuration-best-practices)
- [Testing Configuration](#testing-configuration)
- [Production Deployment](#production-deployment)

### Reference
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## What is the Configuration System?

AgentHub's configuration system is a **layered, modular architecture** that provides:

1. **Automatic YAML Discovery** - Files matching `application-*.yaml` are automatically loaded
2. **Multiple Access Patterns** - Use centralized settings, domain configs, or direct access
3. **Type Safety** - Pydantic validation with dot notation support
4. **Environment Override** - Any setting can be overridden with environment variables
5. **Extensibility** - Add new configurations without code changes

### Key Features

| Feature | Description |
|---------|-------------|
| **Automatic Loading** | Drop a YAML file, access it immediately via `settings.profile_name` |
| **Layered Architecture** | Framework → Providers → Application → Utils |
| **Flexible Access** | Dictionary access, dot notation, or typed config classes |
| **Registry Pattern** | Automatic connection routing to appropriate config sources |
| **Singleton Pattern** | Single source of truth throughout application |
| **Profile Control** | Load all configs or only specific ones for performance |
| **Nested Support** | Organize configs in subdirectories (e.g., `workflows/`) |

---

## Quick Start

### 1. Access Configuration (Simplest)

```python
from app.core.config import Settings

settings = Settings.instance()

# Access any configuration
llm_config = settings.llm
db_config = settings.db
api_key = settings.external.atlassian.api_key

# Use in your code
provider = llm_config['default']['provider']
db_host = db_config['postgres']['host']
```

### 2. Use Domain-Specific Configs (Type-Safe)

```python
from app.core.config import database_config, llm_config, vector_config

# Get typed configurations
postgres = database_config.postgres_config
openai = llm_config.openai_config
qdrant = vector_config.qdrant_config

# Use with IDE autocompletion
connection_string = postgres['connection_string']
api_key = openai['api_key']
url = qdrant['url']
```

### 3. Add New Configuration (Zero Code!)

```bash
# Create new YAML file
cat > resources/application-monitoring.yaml << EOF
monitoring:
  enabled: true
  interval: 60
  endpoints:
    prometheus: "http://localhost:9090"
EOF
```

```python
# Access immediately (no code changes needed!)
settings = Settings.instance()
monitoring = settings.monitoring
print(monitoring['enabled'])  # True
```

---

## System Architecture

AgentHub's configuration system follows a **layered architecture** for separation of concerns:

```
src/app/core/config/
├── framework/           # Core configuration framework
│   ├── settings.py      # Main Settings singleton (automatic discovery)
│   ├── yaml_loader.py   # YAML file loading and parsing
│   ├── dynamic_config.py # Dot notation access wrapper
│   └── registry.py      # Config source registration
│
├── providers/           # Infrastructure provider configurations
│   ├── database.py      # PostgreSQL, Redis, MongoDB configs
│   ├── vector.py        # Qdrant, PgVector, ChromaDB configs
│   └── external.py      # Confluence, Jira, GitHub, S3 configs
│
├── application/         # Application-specific configurations
│   ├── app.py           # Core app settings (security, API, logging)
│   └── llm.py           # LLM provider configurations
│
└── utils/               # Configuration utilities
    └── config_converter.py # Type conversion helpers
```

### Framework Layer

The foundation of the configuration system.

#### `Settings` Class (settings.py)

**Purpose**: Singleton that automatically discovers and loads all `application-*.yaml` files

**Key Responsibilities**:
- Scan `resources/` directory for YAML files
- Extract profile names from filenames
- Load YAML content and resolve environment variables
- Create dynamic attributes for each profile
- Cache configurations for fast access

**Example**:
```python
from app.core.config import Settings

settings = Settings.instance()

# All profiles automatically loaded
print(settings.llm)      # LLM configuration
print(settings.db)       # Database configuration
print(settings.vector)   # Vector store configuration
```

#### `YamlLoader` Class (yaml_loader.py)

**Purpose**: Load and parse YAML files with error handling

**Key Features**:
- Safe YAML loading
- Environment variable placeholder resolution
- Validation and error reporting
- Nested structure support

#### `DynamicConfig` Class (dynamic_config.py)

**Purpose**: Provide dot notation access to dictionary data

**Example**:
```python
# Converts this:
config = {'database': {'host': 'localhost', 'port': 5432}}

# To this:
config.database.host  # 'localhost'
config.database.port  # 5432
```

#### `ConfigSourceRegistry` Class (registry.py)

**Purpose**: Map connection types to their configuration sources

**Pattern**: Decorator-based registration

**Example**:
```python
@register_config(['postgres', 'redis', 'mongodb'])
class DatabaseConfig(BaseConfigSource):
    def get_connection_config(self, connection_name: str) -> dict:
        # Return appropriate config based on connection_name
        pass
```

### Providers Layer

Infrastructure provider configurations (databases, vector stores, external services).

#### `DatabaseConfig` Class (providers/database.py)

**Manages**: PostgreSQL, Redis, MongoDB configurations

**Registered Connections**: `['postgres', 'redis', 'mongodb']`

**Configuration Properties**:
- `postgres_config` - PostgreSQL connection details
- `redis_config` - Redis connection details
- `mongodb_config` - MongoDB connection details (supports Atlas)

**Example**:
```python
from app.core.config import database_config

# Get PostgreSQL configuration
postgres = database_config.postgres_config
connection_string = postgres['connection_string']

# Get Redis configuration
redis = database_config.redis_config
redis_url = redis['url']
```

#### `VectorConfig` Class (providers/vector.py)

**Manages**: Qdrant, PgVector, ChromaDB, Pinecone, Weaviate, Milvus, OpenSearch

**Registered Connections**: `['qdrant', 'pgvector', 'chromadb', 'pinecone', 'weaviate', 'milvus', 'opensearch']`

**Configuration Properties**:
- `qdrant_config` - Qdrant vector database
- `pgvector_config` - PostgreSQL with pgvector extension
- `chromadb_config` - ChromaDB vector store
- `pinecone_config` - Pinecone vector database
- `weaviate_config` - Weaviate vector search
- `milvus_config` - Milvus vector database
- `opensearch_config` - OpenSearch vector search

**Example**:
```python
from app.core.config import vector_config

# Get Qdrant configuration
qdrant = vector_config.qdrant_config
url = qdrant['url']
collection = qdrant['collection_name']

# Get PgVector configuration
pgvector = vector_config.pgvector_config
dimension = pgvector['embedding_dimension']
```

#### `ExternalServicesConfig` Class (providers/external.py)

**Manages**: Confluence, Jira, GitHub, Bitbucket, S3, SharePoint, Datadog

**Registered Connections**: `['confluence', 'jira', 's3', 'sharepoint', 'github', 'bitbucket']`

**Configuration Properties**:
- `atlassian_config` - Confluence and Jira (shared credentials)
- `github_config` - GitHub API
- `bitbucket_config` - Bitbucket API
- `s3_config` - AWS S3
- `sharepoint_config` - Microsoft SharePoint

**Example**:
```python
from app.core.config import external_services_config

# Get Atlassian configuration (Confluence + Jira)
atlassian = external_services_config.atlassian_config
api_key = atlassian['api_key']
confluence_url = atlassian['confluence_base_url']

# Get GitHub configuration
github = external_services_config.github_config
github_token = github['api_key']
```

### Application Layer

Application-specific configurations (not tied to infrastructure).

#### `AppConfig` Class (application/app.py)

**Manages**: Core application settings, security, API, logging

**Configuration Properties**:
- `app_env` - Environment (dev/staging/prod)
- `debug` - Debug mode flag
- `app_name` - Application name
- `app_version` - Application version
- `jwt_secret_key` - JWT secret for authentication
- `jwt_algorithm` - JWT algorithm (e.g., HS256)
- `access_token_expire_minutes` - Token expiration
- `api_host` - API server host
- `api_port` - API server port
- `log_level` - Logging level
- `ingestion_config` - Data ingestion configuration

**Example**:
```python
from app.core.config import AppConfig

app_config = AppConfig()

# Access app settings
env = app_config.app_env
debug = app_config.debug
jwt_secret = app_config.jwt_secret_key

# Use in FastAPI
app = FastAPI(
    title=app_config.app_name,
    version=app_config.app_version,
    debug=app_config.debug
)
```

#### `LLMConfig` Class (application/llm.py)

**Manages**: LLM provider configurations (OpenAI, Anthropic, Groq, Ollama, etc.)

**Configuration Properties**:
- `llm_config` - Complete LLM configuration dictionary
- `openai_config` - OpenAI configuration
- `anthropic_config` - Anthropic Claude configuration
- `groq_config` - Groq configuration
- `ollama_config` - Ollama (local) configuration
- `huggingface_config` - HuggingFace configuration
- `google_config` - Google (Gemini) configuration
- `azure_openai_config` - Azure OpenAI configuration

**Example**:
```python
from app.core.config import llm_config

# Get complete LLM config
full_config = llm_config.llm_config
default_provider = full_config['default_provider']

# Get provider-specific config
openai = llm_config.openai_config
api_key = openai['api_key']
model = openai['default_model']
```

### Utils Layer

Configuration utilities and helpers.

#### `config_converter.py`

**Purpose**: Type conversion utilities for configuration values

**Functions**:
- Convert strings to appropriate types
- Handle environment variable defaults
- Validate configuration values

---

## Configuration Flow

Understanding how configuration flows through the system:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Startup                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Settings.instance() Called                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│        Discover YAML Files (application-*.yaml)              │
│                 in resources/ directory                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│    Load Each YAML File (YamlLoader.load_file)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│   Resolve Environment Variables (${VAR:default})            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│     Wrap in DynamicConfig (dot notation support)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│      Register as settings.profile_name attribute             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Cache for Fast Access                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┬───────────────────┐
           ▼                       ▼                   ▼
    ┌─────────────┐        ┌─────────────┐     ┌─────────────┐
    │  Pattern 1  │        │  Pattern 2  │     │  Registry   │
    │  Settings   │        │   Domain    │     │   Lookup    │
    │   Direct    │        │   Configs   │     │             │
    └─────────────┘        └─────────────┘     └─────────────┘
           │                       │                   │
           └───────────┬───────────┴───────────────────┘
                       ▼
            ┌─────────────────────┐
            │  Application Code   │
            └─────────────────────┘
```

**Step-by-Step Flow**:

1. **Startup**: Application starts, `Settings.instance()` called
2. **Discovery**: Settings scans `resources/` for `application-*.yaml` files
3. **Loading**: YamlLoader loads each YAML file
4. **Resolution**: PropertyResolver replaces `${VAR:default}` with actual values
5. **Wrapping**: DynamicConfig wraps each profile for dot notation
6. **Registration**: Each profile registered as `settings.profile_name`
7. **Caching**: All configurations cached in memory
8. **Access**: Application code accesses via chosen pattern

---

## All Configuration Files

### Application Configurations

Configuration files for application-level settings.

#### `application-app.yaml` → `settings.app`

**Purpose**: Core application settings, security, API configuration

**Location**: `resources/application-app.yaml`

**Key Settings**:
- Application name, version, environment
- Security (JWT secret, algorithm, token expiration)
- API configuration (host, port)
- Logging configuration

**Access**:
```python
settings = Settings.instance()
app_name = settings.app.name
jwt_secret = settings.app.security.jwt_secret_key
api_port = settings.app.api.port
```

**Domain Config**:
```python
from app.core.config import AppConfig

app_config = AppConfig()
env = app_config.app_env
debug = app_config.debug
```

---

#### `application-llm.yaml` → `settings.llm`

**Purpose**: LLM provider configurations (OpenAI, Anthropic, Groq, etc.)

**Location**: `resources/application-llm.yaml`

**Key Settings**:
- Default provider selection
- Provider-specific API keys and models
- Temperature, max tokens, timeout settings
- Base URLs for each provider

**Access**:
```python
settings = Settings.instance()
default_provider = settings.llm.default.provider
openai_key = settings.llm.openai.api_key
```

**Domain Config**:
```python
from app.core.config import llm_config

openai = llm_config.openai_config
api_key = openai['api_key']
model = openai['default_model']
```

**See Also**: [LLM Providers Guide](../llm-providers/README.md)

---

#### `application-prompt.yaml` → `settings.prompt`

**Purpose**: Agent prompts, system instructions, tool selection guidance

**Location**: `resources/application-prompt.yaml`

**Key Settings**:
- System prompts
- Tool selection guidelines
- Prompt templates
- Context formatting instructions

**Access**:
```python
settings = Settings.instance()
system_prompt = settings.prompt.system.base
tool_guidance = settings.prompt.system.tool_selection
```

---

#### `application-context.yaml` → `settings.context`

**Purpose**: Context window management settings

**Location**: `resources/application-context.yaml`

**Key Settings**:
- Maximum token limits
- Buffer tokens for safety
- Truncation strategies
- Summarization settings

**Access**:
```python
settings = Settings.instance()
max_tokens = settings.context.max_tokens
strategy = settings.context.truncation_strategy
```

---

### Provider Configurations

Configuration files for infrastructure providers.

#### `application-db.yaml` → `settings.db`

**Purpose**: Database configurations (PostgreSQL, Redis, MongoDB)

**Location**: `resources/application-db.yaml`

**Key Settings**:
- PostgreSQL connection details
- Redis connection and database selection
- MongoDB connection (local or Atlas)
- Connection pooling settings

**Access**:
```python
settings = Settings.instance()
pg_host = settings.db.postgres.host
redis_host = settings.db.redis.host
```

**Domain Config**:
```python
from app.core.config import database_config

postgres = database_config.postgres_config
conn_str = postgres['connection_string']

redis = database_config.redis_config
redis_url = redis['url']
```

---

#### `application-vector.yaml` → `settings.vector`

**Purpose**: Vector database configurations (Qdrant, PgVector, ChromaDB, etc.)

**Location**: `resources/application-vector.yaml`

**Key Settings**:
- Default vector provider
- Provider-specific endpoints and credentials
- Collection names and dimensions
- Distance metrics and strategies

**Access**:
```python
settings = Settings.instance()
qdrant_url = settings.vector.qdrant.url
pgvector_collection = settings.vector.pgvector.collection_name
```

**Domain Config**:
```python
from app.core.config import vector_config

qdrant = vector_config.qdrant_config
url = qdrant['url']
collection = qdrant['collection_name']
```

**See Also**: [Vector Store Tools Guide](../tools/vector-store-tools.md)

---

#### `application-embeddings.yaml` → `settings.embeddings`

**Purpose**: Embedding model configurations

**Location**: `resources/application-embeddings.yaml`

**Key Settings**:
- Default embedding provider
- Provider-specific models
- Embedding dimensions
- API credentials

**Access**:
```python
settings = Settings.instance()
embedding_provider = settings.embeddings.default_provider
openai_model = settings.embeddings.openai.model
```

---

#### `application-external.yaml` → `settings.external`

**Purpose**: External service configurations (Confluence, Jira, GitHub, S3, etc.)

**Location**: `resources/application-external.yaml`

**Key Settings**:
- Atlassian (Confluence + Jira) credentials
- GitHub, Bitbucket API tokens
- AWS S3 credentials and bucket
- Datadog API keys
- SharePoint configuration

**Access**:
```python
settings = Settings.instance()
confluence_url = settings.external.atlassian.confluence_base_url
github_token = settings.external.github.api_key
```

**Domain Config**:
```python
from app.core.config import external_services_config

atlassian = external_services_config.atlassian_config
api_key = atlassian['api_key']

github = external_services_config.github_config
token = github['api_key']
```

**See Also**:
- [Confluence Tools Guide](../tools/confluence-tools.md)
- [Jira Tools Guide](../tools/jira-tools.md)
- [Datadog Tools Guide](../tools/datadog-tools.md)

---

#### `application-data-sources.yaml` → `settings.data_sources`

**Purpose**: Data ingestion source configurations

**Location**: `resources/application-data-sources.yaml`

**Key Settings**:
- List of data sources to ingest
- Source-specific configurations
- Enable/disable flags
- Scheduling settings

**Access**:
```python
settings = Settings.instance()
for source in settings.data_sources:
    print(source['type'], source['name'])
```

---

#### `application-tools.yaml` → `settings.tools`

**Purpose**: Tool enable/disable and rate limiting configuration

**Location**: `resources/application-tools.yaml`

**Key Settings**:
- Tool enable/disable flags
- Rate limiting per tool
- Tool-specific settings

**Access**:
```python
settings = Settings.instance()
confluence_enabled = settings.tools.confluence.enabled
jira_rate_limit = settings.tools.jira.rate_limit
```

---

## Access Patterns

AgentHub provides two primary patterns for accessing configuration.

### Pattern 1: Centralized Settings (Recommended)

**Use Case**: Small to medium projects, rapid development, consistent access

**Advantages**:
- Simple and consistent
- One import everywhere
- Automatic discovery
- Zero boilerplate

**Disadvantages**:
- Global state
- Less explicit dependencies
- Runtime type checking only

**Example**:

```python
from app.core.config import Settings

settings = Settings.instance()

# Access any configuration
llm_provider = settings.llm.default.provider
db_host = settings.db.postgres.host
confluence_url = settings.external.atlassian.confluence_base_url

# Use in functions
def create_llm():
    provider = settings.llm.default.provider
    return LLMFactory.create_llm(provider)

def connect_database():
    host = settings.db.postgres.host
    port = settings.db.postgres.port
    return connect(host, port)
```

---

### Pattern 2: Domain-Specific Configs

**Use Case**: Large projects, strong typing, explicit dependencies

**Advantages**:
- Strong typing
- IDE autocompletion
- Explicit dependencies
- Easier testing (inject configs)
- Domain-specific methods

**Disadvantages**:
- More boilerplate
- Need to update config classes
- Two layers (Settings → Config classes)

**Example**:

```python
from app.core.config import database_config, llm_config, vector_config

# Type-safe access
postgres = database_config.postgres_config
connection_string = postgres['connection_string']

openai = llm_config.openai_config
api_key = openai['api_key']
model = openai['default_model']

qdrant = vector_config.qdrant_config
url = qdrant['url']

# Dependency injection
class UserService:
    def __init__(self, db_config: DatabaseConfig, llm_config: LLMConfig):
        self.db = db_config
        self.llm = llm_config
    
    def create_user(self, user_data: dict):
        conn_str = self.db.postgres_config['connection_string']
        # Database operations...
```

---

## Choosing Your Pattern

### Decision Matrix

| Criteria | Pattern 1 (Settings) | Pattern 2 (Domain Configs) |
|----------|---------------------|---------------------------|
| **Project Size** | Small-Medium | Large |
| **Team Size** | 1-5 developers | 5+ developers |
| **Type Safety** | Runtime | Compile-time properties |
| **Boilerplate** | None | Medium |
| **Testing** | Mock Settings | Inject configs |
| **IDE Support** | Limited | Full autocompletion |
| **Extensibility** | Automatic | Manual updates |
| **Learning Curve** | Easy | Medium |

### Recommendations

**Start with Pattern 1 (Centralized Settings) if:**
- Your team is small (1-5 developers)
- You want rapid development
- Your codebase is under 10,000 lines
- You prefer simplicity over type safety

**Upgrade to Pattern 2 (Domain Configs) when:**
- Your team grows beyond 5 developers
- Your codebase exceeds 10,000 lines
- You need strict type checking
- You're building reusable modules
- You want better testability

### Hybrid Approach

You can mix patterns in the same project:

```python
# Use Settings for simple access
from app.core.config import Settings
settings = Settings.instance()
app_name = settings.app.name

# Use domain configs for complex operations
from app.core.config import database_config, llm_config

class DataService:
    def __init__(self):
        self.db = database_config
        self.llm = llm_config
    
    def process_data(self):
        # Type-safe access
        postgres = self.db.postgres_config
        openai = self.llm.openai_config
        # ...
```

---

## Automatic YAML Discovery

The Settings class automatically discovers and loads YAML files using a simple pattern.

### How It Works

**1. File Pattern Recognition**

```
File: resources/application-{profile_name}.yaml
Access: settings.{profile_name}
```

**2. Automatic Loading Process**

When `Settings.instance()` is called:

1. Scan `resources/` for `application-*.yaml` files
2. Extract profile name from filename (after `application-` prefix)
3. Load YAML content with safe parsing
4. Resolve `${ENV_VAR:default}` placeholders
5. Wrap in DynamicConfig for dot notation support
6. Register as `settings.profile_name` attribute
7. Cache for future fast access

**3. Naming Rules**

| Filename | Profile Name | Access Via |
|----------|--------------|------------|
| `application-llm.yaml` | `llm` | `settings.llm` |
| `application-db.yaml` | `db` | `settings.db` |
| `application-my-service.yaml` | `my-service` | `settings.my_service` |
| `application-api_v2.yaml` | `api_v2` | `settings.api_v2` |

### Adding New Configurations

**Zero code changes required!**

**Step 1**: Create YAML file

```bash
# Create: resources/application-cache.yaml
cat > resources/application-cache.yaml << EOF
cache:
  enabled: true
  ttl_seconds: 3600
  max_size: 1000
  strategy: "LRU"
EOF
```

**Step 2**: Restart application

```python
settings = Settings.instance()
# Automatically discovered and loaded!
```

**Step 3**: Access immediately

```python
cache_config = settings.cache
enabled = cache_config.enabled
ttl = cache_config.ttl_seconds
```

### Nested Configuration

Organize related configs in subdirectories:

```
resources/
├── application-app.yaml
├── application-db.yaml
└── workflows/
    ├── application-approval.yaml
    └── application-signup.yaml
```

```python
# Access nested configs
approval = settings.workflows.approval
signup = settings.workflows.signup
```

**See Also**: [Resources Directory Guide](./resources-directory.md) for detailed information on automatic loading

---

## Environment Variables

Override any configuration value with environment variables.

### Syntax

```yaml
key: "${ENV_VAR_NAME:default_value}"
```

**Examples**:

```yaml
# With default
api_key: "${OPENAI_API_KEY:sk-test-key}"

# Without default (will error if not set)
api_key: "${OPENAI_API_KEY}"

# Nested values
database:
  host: "${DB_HOST:localhost}"
  port: "${DB_PORT:5432}"
```

### Environment File (.env)

Create `.env` file in project root:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agenthub
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret

# External Services
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
JIRA_BASE_URL=https://your-domain.atlassian.net
ATLASSIAN_API_KEY=your-api-key
ATLASSIAN_EMAIL=your-email@company.com
```

### Priority Order

Configuration values are resolved in this order (highest to lowest priority):

1. **Environment variables** (highest priority)
2. **YAML file values**
3. **Default values** (in `${VAR:default}` syntax)

---

## Profile Control

Control which configurations to load for performance optimization.

### Load All Profiles (Default)

```python
# In src/app/core/config/framework/settings.py
PROFILES = ['*']  # Load all available profiles
```

### Load Specific Profiles

```python
# In src/app/core/config/framework/settings.py
PROFILES = ['db', 'llm', 'app']  # Load only these profiles
```

**Use Case**: Microservices that only need specific configs

```python
# API service only needs app and llm configs
PROFILES = ['app', 'llm']

# Worker service only needs db and external configs
PROFILES = ['db', 'external']
```

### Runtime Profile Control

```python
from app.core.config import Settings

# Change profiles at runtime
Settings.set_profiles_setting(['vector', 'embeddings'])

# Reload with new profile selection
settings = Settings.instance()
settings.reload_profiles()
```

---

## Configuration Registry

The registry pattern automatically routes connection requests to appropriate config sources.

### How It Works

**1. Registration**

Config classes register which connection types they handle:

```python
@register_config(['postgres', 'redis', 'mongodb'])
class DatabaseConfig(BaseConfigSource):
    def get_connection_config(self, connection_name: str) -> dict:
        if connection_name == 'postgres':
            return self.postgres_config
        # ... handle other connections
```

**2. Lookup**

```python
from app.core.config.framework.registry import ConfigSourceRegistry

# Get config source for a connection
config_source = ConfigSourceRegistry.get_config_source('postgres')

# Get configuration
postgres_config = config_source.get_connection_config('postgres')
```

### Registered Connections

| Connection Type | Config Source | Module |
|----------------|---------------|---------|
| `postgres`, `redis`, `mongodb` | `DatabaseConfig` | `providers/database.py` |
| `qdrant`, `pgvector`, `chromadb`, `pinecone`, `weaviate`, `milvus`, `opensearch` | `VectorConfig` | `providers/vector.py` |
| `confluence`, `jira`, `s3`, `sharepoint`, `github`, `bitbucket` | `ExternalServicesConfig` | `providers/external.py` |

---

## Configuration Best Practices

### 1. Use Environment Variables for Secrets

```yaml
# GOOD
database:
  password: "${POSTGRES_PASSWORD}"
  api_key: "${API_KEY}"

# BAD
database:
  password: "hardcoded-password"
```

### 2. Provide Sensible Defaults

```yaml
# GOOD
app:
  port: "${API_PORT:8000}"
  timeout: "${TIMEOUT:30}"

# BAD (will fail if env var not set)
app:
  port: "${API_PORT}"
```

### 3. Group Related Settings

```yaml
# GOOD
llm:
  default:
    provider: "openai"
    temperature: 0.1
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"

# BAD (flat structure)
llm_provider: "openai"
llm_temperature: 0.1
openai_api_key: "${OPENAI_API_KEY}"
```

### 4. Document Configuration

```yaml
# GOOD - Add comments
llm:
  # Default LLM provider (openai, anthropic, groq, ollama)
  default_provider: "openai"
  
  # Temperature controls randomness (0.0 = deterministic, 2.0 = very random)
  temperature: 0.1
```

### 5. Validate at Startup

```python
from app.core.config import Settings

settings = Settings.instance()

# Validate required configs exist
assert hasattr(settings, 'llm'), "Missing LLM configuration"
assert hasattr(settings, 'db'), "Missing database configuration"
```

---

## Testing Configuration

### Mock Settings in Tests

```python
import pytest
from unittest.mock import Mock, patch
from app.core.config import Settings

@pytest.fixture
def mock_settings():
    """Mock Settings for testing."""
    settings = Mock(spec=Settings)
    settings.llm.default.provider = "openai"
    settings.llm.openai.api_key = "test-key"
    settings.db.postgres.host = "localhost"
    return settings

def test_create_llm(mock_settings):
    with patch('app.core.config.Settings.instance', return_value=mock_settings):
        # Test code that uses Settings
        pass
```

### Reset Settings Between Tests

```python
import pytest
from app.core.config import Settings

@pytest.fixture(autouse=True)
def reset_settings():
    """Reset Settings singleton between tests."""
    yield
    Settings.reset()
```

---

## Production Deployment

### Environment-Specific Configs

Use environment variables to switch configurations:

```bash
# Development
export APP_ENV=development
export DEBUG=true
export LLM_PROVIDER=ollama

# Production
export APP_ENV=production
export DEBUG=false
export LLM_PROVIDER=azure_openai
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Copy configuration files
COPY resources/ /app/resources/

# Environment variables injected at runtime
ENV APP_ENV=production
ENV DEBUG=false

CMD ["python", "main.py"]
```

### Health Checks

```python
from fastapi import FastAPI, HTTPException
from app.core.config import Settings

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check with configuration validation."""
    try:
        settings = Settings.instance()
        
        # Validate critical configs
        assert hasattr(settings, 'app'), "Missing app config"
        assert hasattr(settings, 'db'), "Missing database config"
        
        return {
            "status": "healthy",
            "environment": settings.app.environment,
            "version": settings.app.version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config error: {str(e)}")
```

---

## API Reference

### Settings Class

```python
from app.core.config import Settings

# Get singleton instance
settings = Settings.instance()

# Reset instance (testing)
Settings.reset()

# Set profile selection
Settings.set_profiles_setting(['db', 'llm'])

# Reload profiles
settings.reload_profiles()

# Access profiles
llm_config = settings.llm
db_config = settings.db
```

### Domain Config Classes

```python
# Database configuration
from app.core.config import database_config
postgres = database_config.postgres_config
redis = database_config.redis_config

# Vector configuration
from app.core.config import vector_config
qdrant = vector_config.qdrant_config
pgvector = vector_config.pgvector_config

# LLM configuration
from app.core.config import llm_config
openai = llm_config.openai_config
anthropic = llm_config.anthropic_config

# External services
from app.core.config import external_services_config
atlassian = external_services_config.atlassian_config

# App configuration
from app.core.config import AppConfig
app_config = AppConfig()
env = app_config.app_env
```

---

## Troubleshooting

### Issue 1: Profile Not Found

**Error**: `AttributeError: 'Settings' object has no attribute 'my_config'`

**Solution**: Ensure YAML file exists and follows naming pattern

```bash
# Check file exists
ls resources/application-my-config.yaml

# Restart application to reload configs
```

### Issue 2: Environment Variable Not Resolved

**Error**: Environment variable appears literally in config

**Solution**: Check syntax and ensure variable is set

```yaml
# Correct syntax
api_key: "${OPENAI_API_KEY}"

# Incorrect
api_key: "$OPENAI_API_KEY"  # Missing braces
```

```bash
# Verify environment variable is set
echo $OPENAI_API_KEY

# Set if missing
export OPENAI_API_KEY="your-key"
```

### Issue 3: Circular Import

**Error**: `ImportError: cannot import name 'settings'`

**Solution**: Import Settings locally in functions

```python
# BAD (module level)
from app.core.config.framework.settings import settings

# GOOD (local import)
class MyClass:
    def __init__(self):
        from app.core.config.framework.settings import settings
        self.config = settings.my_config
```

---

## Next Steps

- **[Resources Directory Guide](./resources-directory.md)** - Detailed guide on YAML file structure and automatic loading
- **[LLM Providers Guide](../llm-providers/README.md)** - Configure and use different LLM providers
- **[Tools Documentation](../tools/README.md)** - Configure and use tools (Confluence, Jira, Vector Store, Datadog)

---

**Last Updated**: January 10, 2026  
**Version**: 1.0  
**Related**: Settings, YAML Configuration, Environment Variables
