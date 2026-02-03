# Resources Directory: Flexible Configuration Management

> **YAML-based configuration system** that provides flexible, environment-specific settings accessible via `settings.profile_name`

## Table of Contents
- [What is the Resources Directory?](#what-is-the-resources-directory)
- [How It Works](#how-it-works)
  - [Automatic Discovery and Loading](#automatic-discovery-and-loading)
  - [Extensibility and Performance](#extensibility-and-performance)
  - [The Magic of `settings.profile_name`](#the-magic-of-settingsprofile_name)
  - [Flow Diagram](#flow-diagram)
- [File Structure](#file-structure)
- [Accessing Configuration](#accessing-configuration)
- [Available Profiles](#available-profiles)
- [Configuration Files](#configuration-files)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Configuration Approaches: Choosing Your Strategy](#configuration-approaches-choosing-your-strategy)
  - [Approach 1: Centralized Settings Object](#approach-1-centralized-settings-object-recommended)
  - [Approach 2: Domain-Specific Config Classes](#approach-2-domain-specific-config-classes)
  - [Comparison Table](#comparison-table)
- [Troubleshooting](#troubleshooting)

---

## What is the Resources Directory?

The `resources/` directory contains **YAML configuration files** that define all application settings. This provides:

- **Centralized Configuration** - All settings in one place
- **Environment Profiles** - Different configs for dev/staging/prod
- **Type Safety** - Validated configuration with Pydantic
- **Flexible Access** - Get entire profiles as dictionaries
- **Easy Override** - Environment variables can override any setting
- **Version Control** - Track configuration changes in git

---

## How It Works

### Automatic Discovery and Loading

The configuration system **automatically discovers and loads** all YAML files in the `resources/` directory using a simple naming pattern:

```
File Pattern: application-{profile_name}.yaml
Access Pattern: settings.{profile_name}
```

When the application starts, the `Settings` class:

1. **Scans** the `resources/` directory for files matching `application-*.yaml`
2. **Extracts** the profile name from the filename (everything after `application-`)
3. **Loads** the YAML content and resolves environment variables
4. **Creates** a dynamic attribute on the settings object with the profile name
5. **Makes it accessible** as a dictionary via `settings.profile_name`

**This is completely automatic** - no code changes needed! Just add a new YAML file and it becomes available.

#### Example: Adding a New Configuration

Let's say you want to add custom monitoring configuration:

**Step 1:** Create the YAML file
```bash
# Create: resources/application-monitoring.yaml
```

**Step 2:** Add your configuration
```yaml
# resources/application-monitoring.yaml
enabled: true
interval_seconds: 60
metrics:
  - cpu_usage
  - memory_usage
  - disk_io
endpoints:
  prometheus: "http://localhost:9090"
  grafana: "http://localhost:3000"
```

**Step 3:** Access it immediately (no code changes!)
```python
from app.core.config import Settings

settings = Settings.instance()

# Automatically available!
monitoring = settings.monitoring
print(monitoring['enabled'])  # True
print(monitoring['interval_seconds'])  # 60

# Or use dot notation
print(settings.monitoring.enabled)  # True
```

#### How File Names Map to Attributes

The system converts filenames to attribute names using these rules:

| Filename | Profile Name | Access Via |
|----------|--------------|------------|
| `application-llm.yaml` | `llm` | `settings.llm` |
| `application-db.yaml` | `db` | `settings.db` |
| `application-external.yaml` | `external` | `settings.external` |
| `application-custom-api.yaml` | `custom-api` | `settings.custom_api` |
| `application-my_service.yaml` | `my_service` | `settings.my_service` |

**Note:** Hyphens in filenames are preserved in the profile name but work with both hyphen and underscore access (Python converts automatically).

#### Nested Configuration Support

You can also organize configurations in subdirectories:

```
resources/
├── application-app.yaml          # Flat: settings.app
├── application-db.yaml           # Flat: settings.db
└── workflows/                    # Nested namespace
    ├── application-approval.yaml # Nested: settings.workflows.approval
    └── application-signup.yaml   # Nested: settings.workflows.signup
```

```python
# Access nested configurations
approval_config = settings.workflows.approval
signup_config = settings.workflows.signup
```

#### Extensibility and Performance

The configuration system is designed to be both extensible and performant:

**Dynamic Loading**
- The `Settings` class uses Python's `__getattr__` magic method to provide dynamic attribute access
- Configuration is loaded once at startup and cached in memory
- New profiles are automatically discovered without code changes

**Profile Control**
You can control which profiles to load for performance optimization:

```python
# In src/app/core/config/framework/settings.py

# Option 1: Load all profiles (default)
PROFILES = ['*']

# Option 2: Load only specific profiles
PROFILES = ['db', 'llm', 'app']

# Option 3: Change at runtime
Settings.set_profiles_setting(['vector', 'embeddings'])
settings = Settings.instance()
settings.reload_profiles()  # Apply new profile selection
```

**Internal Architecture**

The configuration system consists of three main components:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Settings** | Singleton manager that discovers and loads profiles | `src/app/core/config/framework/settings.py` |
| **YamlLoader** | Loads YAML files and handles parsing | `src/app/core/config/framework/yaml_loader.py` |
| **DynamicConfig** | Provides dot notation access to dictionaries | `src/app/core/config/framework/dynamic_config.py` |

**How It Works Internally:**

1. **Discovery Phase**: Settings scans `resources/` for `application-*.yaml` files
2. **Extraction Phase**: Profile names are extracted from filenames
3. **Loading Phase**: YamlLoader loads each file and resolves environment variables
4. **Resolution Phase**: PropertyResolver replaces `${VAR:default}` placeholders
5. **Creation Phase**: DynamicConfig wraps each profile for dot notation access
6. **Caching Phase**: All profiles are cached in memory for fast access

```python
# Example of what happens internally:
# 1. File discovered: resources/application-llm.yaml
# 2. Profile name extracted: "llm"
# 3. YAML content loaded: {'default_provider': 'openai', ...}
# 4. Env vars resolved: ${OPENAI_API_KEY} → actual key
# 5. DynamicConfig created: settings.llm
# 6. Cached for future access
```

### The Magic of `settings.profile_name`

Every YAML file in `resources/` becomes accessible as a **dictionary** through the settings object:

```python
from app.core.config import Settings

settings = Settings.instance()

# Access any profile by name
llm_config = settings.llm        # Returns entire LLM configuration as dict
db_config = settings.db          # Returns entire database configuration as dict
vector_config = settings.vector  # Returns entire vector store configuration as dict
```

### Flow Diagram

```
resources/
├── application-llm.yaml      → settings.llm       (dict)
├── application-db.yaml       → settings.db        (dict)
├── application-vector.yaml   → settings.vector    (dict)
├── application-embeddings.yaml → settings.embeddings (dict)
└── ...

Access Pattern:
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  YAML File       │  →   │  Settings        │  →   │  Dictionary      │
│  *.yaml          │      │  .profile_name   │      │  {key: value}    │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## File Structure

### Current Resources Directory

```
resources/
├── application-llm.yaml          # LLM provider configurations
├── application-db.yaml           # Database configurations
├── application-vector.yaml       # Vector store configurations
├── application-embeddings.yaml   # Embedding configurations
├── application-prompt.yaml       # Prompt configurations
├── application-context.yaml      # Context window configurations
├── application-data-sources.yaml # Data source configurations
├── application-external.yaml     # External service configurations
├── application-app.yaml          # Application-level settings
├── test-application-defaults.yaml # Test environment defaults
└── workflows/                    # Workflow-specific configs
    ├── application-approval.yaml
    └── application-signup.yaml
```

### Naming Convention

```
application-{profile-name}.yaml  →  settings.{profile_name}

Examples:
application-llm.yaml      →  settings.llm
application-db.yaml       →  settings.db
application-vector.yaml   →  settings.vector
```

**Note**: Hyphens in filenames become underscores in Python attribute names.

---

## Accessing Configuration

AgentHub provides **two flexible ways** to access configuration:

### Method 1: Dictionary Access (Most Common)

```python
from app.core.config import Settings

settings = Settings.instance()

# Get entire profile as dictionary
llm_config = settings.llm
print(llm_config)
# Output:
# {
#     'default_provider': 'openai',
#     'temperature': 0.1,
#     'max_tokens': 1000,
#     'providers': {
#         'openai': {'api_key': '...', 'model': 'gpt-4'},
#         'anthropic': {'api_key': '...', 'model': 'claude-2'},
#         ...
#     }
# }

# Access nested values
provider = llm_config['default_provider']  # 'openai'
openai_config = llm_config['providers']['openai']
temperature = llm_config['temperature']  # 0.1

# Safe get with default
timeout = llm_config.get('timeout', 30)
```

### Method 2: Dot Notation (Also Supported!)

**You can also use dot operators** to access configuration values:

```python
from app.core.config import Settings

settings = Settings.instance()

# Access with dot notation 
provider = settings.llm.default_provider       # 'openai'
temperature = settings.llm.temperature         # 0.1
api_key = settings.llm.providers.openai.api_key

# Database config with dots
db_host = settings.db.postgres.host            # 'localhost'
db_port = settings.db.postgres.port            # 5432

# Vector config with dots
collection = settings.vector.pgvector.collection_name
dimension = settings.vector.pgvector.embedding_dimension
```

**Both methods work!** Choose based on your preference:

| Method | When to Use | Example |
|--------|-------------|---------|
| **Dictionary** `['key']` | Dynamic keys, safe defaults | `config.get('timeout', 30)` |
| **Dot notation** `.key` | Static keys, cleaner code | `settings.llm.temperature` |

### Method 3: Mixed Access

You can even **mix both styles**:

```python
# Start with dictionary, then use dots
llm_config = settings.llm
provider = llm_config.default_provider    # Dot notation on dict

# Or start with dots, then use dictionary
openai_config = settings.llm.providers['openai']  # Mixed!
```

---

## Available Profiles

### 1. LLM Configuration (`settings.llm`)

**File**: `resources/application-llm.yaml`

```yaml
llm:
  default_provider: "openai"
  temperature: 0.1
  max_tokens: 1000
  
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "${OPENAI_MODEL:gpt-4}"
      temperature: "${OPENAI_TEMPERATURE:0.1}"
      max_tokens: "${OPENAI_MAX_TOKENS:1000}"
    
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "${ANTHROPIC_MODEL:claude-2}"
      temperature: "${ANTHROPIC_TEMPERATURE:0.1}"
```

**Usage**:
```python
llm_config = settings.llm

# Get default provider
provider = llm_config['default_provider']  # 'openai'

# Get provider-specific config
openai = llm_config['providers']['openai']
api_key = openai['api_key']
model = openai['model']

# Use in your code
from app.infrastructure.llm import LLMFactory
llm = LLMFactory.get_llm(provider)
```

### 2. Database Configuration (`settings.db`)

**File**: `resources/application-db.yaml`

```yaml
db:
  postgres:
    host: "${POSTGRES_HOST:localhost}"
    port: "${POSTGRES_PORT:5432}"
    database: "${POSTGRES_DB:agenthub}"
    user: "${POSTGRES_USER:postgres}"
    password: "${POSTGRES_PASSWORD:postgres}"
    pool_size: 10
    max_overflow: 20
  
  mongodb:
    host: "${MONGODB_HOST:localhost}"
    port: "${MONGODB_PORT:27017}"
    database: "${MONGODB_DB:agenthub}"
  
  redis:
    host: "${REDIS_HOST:localhost}"
    port: "${REDIS_PORT:6379}"
    db: 0
```

**Usage**:
```python
db_config = settings.db

# Get PostgreSQL config
pg = db_config['postgres']
connection_string = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"

# Get MongoDB config
mongo = db_config['mongodb']
mongo_uri = f"mongodb://{mongo['host']}:{mongo['port']}/{mongo['database']}"

# Get Redis config
redis = db_config['redis']
redis_url = f"redis://{redis['host']}:{redis['port']}/{redis['db']}"
```

### 3. Vector Store Configuration (`settings.vector`)

**File**: `resources/application-vector.yaml`

```yaml
vector:
  default_provider: "pgvector"
  
  pgvector:
    collection_name: "documents"
    embedding_dimension: 1536
    distance_strategy: "cosine"
    connection_string: "${PGVECTOR_CONNECTION_STRING}"
    pre_delete_collection: false
```

**Usage**:
```python
vector_config = settings.vector

# Get default provider
provider = vector_config['default_provider']  # 'pgvector'

# Get provider-specific config
pgvector = vector_config['pgvector']
collection = pgvector['collection_name']
dimension = pgvector['embedding_dimension']

# Use in your code
from app.db.vector.pgvector import PgVectorDB
vector_db = PgVectorDB()
await vector_db.save_and_embed(docs=documents)
```

### 4. Embeddings Configuration (`settings.embeddings`)

**File**: `resources/application-embeddings.yaml`

```yaml
embeddings:
  default_type: "openai"
  
  openai:
    model: "text-embedding-ada-002"
    dimensions: 1536
  
  huggingface:
    model: "sentence-transformers/all-MiniLM-L6-v2"
    dimensions: 384
```

**Usage**:
```python
embeddings_config = settings.embeddings

# Get default embedding type
default_type = embeddings_config['default_type']  # 'openai'

# Get model config
openai_embedding = embeddings_config['openai']
model = openai_embedding['model']
dimensions = openai_embedding['dimensions']

# Use in your code
from app.db.vector.embeddings.embedding import EmbeddingFactory
embedding_model = EmbeddingFactory.get_embedding_model(default_type)
```

### 5. Prompt Configuration (`settings.prompt`)

**File**: `resources/application-prompt.yaml`

```yaml
prompt:
  temperature: 0.7
  max_tokens: 2000
  
  templates:
    system: "You are a helpful AI assistant."
    rag_query: "Based on the following context, answer the question..."
    chat: "Continue the conversation naturally..."
```

**Usage**:
```python
prompt_config = settings.prompt

# Get prompt settings
temperature = prompt_config['temperature']
max_tokens = prompt_config['max_tokens']

# Get templates
templates = prompt_config['templates']
system_prompt = templates['system']
rag_template = templates['rag_query']
```

### 6. Context Window Configuration (`settings.context`)

**File**: `resources/application-context.yaml`

```yaml
context:
  max_context_tokens: 8000
  reserve_for_response: 2000
  truncation_strategy: "smart"
```

**Usage**:
```python
context_config = settings.context

max_tokens = context_config['max_context_tokens']
reserve = context_config['reserve_for_response']
strategy = context_config['truncation_strategy']
```

### 7. Application Settings (`settings.app`)

**File**: `resources/application-app.yaml`

```yaml
app:
  name: "AgentHub"
  version: "1.0.0"
  environment: "${APP_ENV:development}"
  debug: "${DEBUG:false}"
  log_level: "${LOG_LEVEL:INFO}"
  
  api:
    host: "0.0.0.0"
    port: 8000
    reload: true
```

**Usage**:
```python
app_config = settings.app

app_name = app_config['name']
version = app_config['version']
environment = app_config['environment']

# API settings
api = app_config['api']
host = api['host']
port = api['port']
```

---

## Configuration Files

### Automatic Environment Variable Detection 

**AgentHub automatically detects and resolves environment variables** anywhere in your YAML configuration files using the `${VARIABLE_NAME}` syntax!

#### The Magic Syntax

```yaml
# Simple pattern: ${VARIABLE_NAME}
api_key: "${OPENAI_API_KEY}"

# With default value: ${VARIABLE_NAME:default}
host: "${POSTGRES_HOST:localhost}"
port: "${POSTGRES_PORT:5432}"
temperature: "${TEMPERATURE:0.7}"
```

#### How It Works

```
Step 1: You write YAML
┌────────────────────────────────┐
│ api_key: "${OPENAI_API_KEY}"  │
└────────────────────────────────┘
              ↓
Step 2: AgentHub checks environment
┌────────────────────────────────┐
│ Is OPENAI_API_KEY set?        │
│ - Yes: Use its value          │
│ - No:  Use default OR error   │
└────────────────────────────────┘
              ↓
Step 3: Value automatically injected
┌────────────────────────────────┐
│ api_key: "sk-abc123..."       │
└────────────────────────────────┘
```

#### Features

**Works Everywhere**: Use in any YAML file, any key, any nesting level  
**Automatic Detection**: No special code needed  
**Type Preservation**: Strings stay strings, numbers stay numbers  
**Default Values**: Optional fallback with `:default` syntax  
**Error Handling**: Clear error if required variable missing  

#### Syntax Options

```yaml
# Option 1: Required variable (error if not set)
api_key: "${OPENAI_API_KEY}"

# Option 2: With default value
host: "${POSTGRES_HOST:localhost}"
port: "${POSTGRES_PORT:5432}"

# Option 3: Nested in objects
database:
  connection:
    host: "${DB_HOST:localhost}"
    port: "${DB_PORT:5432}"
    
# Option 4: Multiple variables in same file
llm:
  api_key: "${OPENAI_API_KEY}"
  model: "${OPENAI_MODEL:gpt-4}"
  temperature: "${OPENAI_TEMPERATURE:0.7}"
  max_tokens: "${OPENAI_MAX_TOKENS:1000}"
```

#### When Accessed in Python

```python
settings = Settings.instance()

# All environment variables are ALREADY RESOLVED!
llm_config = settings.llm

print(llm_config['api_key'])
# Output: "sk-abc123..."  (not "${OPENAI_API_KEY}")

print(llm_config['temperature'])
# Output: 0.7  (actual value, not "${OPENAI_TEMPERATURE:0.7}")
```

**Key Point**: By the time you access `settings.profile_name`, all `${VARIABLE_NAME}` patterns have been automatically replaced with actual values from your environment!

---

### Environment Variable Interpolation Details

**Full Syntax**: `${ENV_VAR_NAME:default_value}`

| Part | Purpose | Required | Example |
|------|---------|----------|---------|
| `${` | Start marker | Yes | `${` |
| `ENV_VAR_NAME` | Variable name | Yes | `OPENAI_API_KEY` |
| `:` | Separator | No (only with default) | `:` |
| `default_value` | Fallback value | No | `localhost`, `5432`, `0.7` |
| `}` | End marker | Yes | `}` |

**Resolution Priority**:
1. **Environment Variable**: Check system environment
2. **Default Value**: Use if variable not set (if provided)
3. **Error**: Raise exception if no variable and no default

### Example: application-llm.yaml

```yaml
llm:
  # Global defaults
  default_provider: "openai"
  temperature: 0.1
  max_tokens: 1000
  timeout: 30
  
  # Provider-specific configurations
  providers:
    openai:
      # Required: Will error if OPENAI_API_KEY not set
      api_key: "${OPENAI_API_KEY}"
      
      # Optional: Falls back to gpt-4 if not set
      model: "${OPENAI_MODEL:gpt-4}"
      temperature: "${OPENAI_TEMPERATURE:0.1}"
      max_tokens: "${OPENAI_MAX_TOKENS:1000}"
      timeout: "${OPENAI_TIMEOUT:30}"
    
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "${ANTHROPIC_MODEL:claude-2}"
      temperature: "${ANTHROPIC_TEMPERATURE:0.1}"
      max_tokens: "${ANTHROPIC_MAX_TOKENS:1000}"
    
    groq:
      api_key: "${GROQ_API_KEY}"
      model: "${GROQ_MODEL:mixtral-8x7b-32768}"
      temperature: "${GROQ_TEMPERATURE:0.7}"
    
    google:
      api_key: "${GOOGLE_API_KEY}"
      model: "${GOOGLE_MODEL:gemini-pro}"
      temperature: "${GOOGLE_TEMPERATURE:0.7}"
    
    azure_openai:
      api_key: "${AZURE_OPENAI_API_KEY}"
      endpoint: "${AZURE_OPENAI_ENDPOINT}"
      deployment: "${AZURE_OPENAI_DEPLOYMENT:gpt-4}"
      api_version: "${AZURE_OPENAI_API_VERSION:2023-05-15}"
      temperature: "${AZURE_OPENAI_TEMPERATURE:0.1}"
```

**Accessing with Dictionary Notation**:
```python
settings = Settings.instance()
llm_config = settings.llm

# All ${...} variables are automatically resolved!
api_key = llm_config['providers']['openai']['api_key']
# Result: "sk-abc123..." (actual value from OPENAI_API_KEY env var)

temperature = llm_config['temperature']
# Result: 0.1 (or value from OPENAI_TEMPERATURE env var)
```

**Accessing with Dot Notation**:
```python
settings = Settings.instance()

# Clean dot notation access
provider = settings.llm.default_provider           # 'openai'
temperature = settings.llm.temperature             # 0.1
api_key = settings.llm.providers.openai.api_key   # Actual API key value
model = settings.llm.providers.openai.model       # 'gpt-4' or custom
```

---

## Usage Examples

### Example 1: Dynamic LLM Provider Selection

```python
from app.core.config import Settings
from app.infrastructure.llm import LLMFactory

settings = Settings.instance()

# Get LLM configuration
llm_config = settings.llm

# Get default provider
provider_name = llm_config['default_provider']
print(f"Using provider: {provider_name}")

# Get provider-specific settings
provider_config = llm_config['providers'][provider_name]
print(f"Model: {provider_config['model']}")
print(f"Temperature: {provider_config['temperature']}")

# Create LLM instance
from app.core.constants import LLMProvider
llm = LLMFactory.get_llm(LLMProvider(provider_name))

# Generate with configured settings
response = await llm.generate(
    messages=["What is AI?"],
    temperature=provider_config['temperature'],
    max_tokens=provider_config['max_tokens']
)
```

### Example 2: Database Connection Setup

```python
from app.core.config import Settings
import asyncpg

settings = Settings.instance()

# Get database configuration
db_config = settings.db

# Get PostgreSQL config
pg = db_config['postgres']

# Build connection string
connection_string = (
    f"postgresql://{pg['user']}:{pg['password']}"
    f"@{pg['host']}:{pg['port']}/{pg['database']}"
)

# Create connection pool
pool = await asyncpg.create_pool(
    connection_string,
    min_size=pg.get('min_pool_size', 5),
    max_size=pg.get('pool_size', 10)
)
```

### Example 3: Vector Store Configuration

```python
from app.core.config import Settings
from app.db.vector.pgvector import PgVectorDB
from app.core.constants import EmbeddingType

settings = Settings.instance()

# Get vector store configuration
vector_config = settings.vector

# Get provider-specific config
pgvector_config = vector_config['pgvector']

# Initialize vector database with config
vector_db = PgVectorDB()
# Config is automatically loaded from settings

# Use configured settings
collection_name = pgvector_config['collection_name']
await vector_db.save_and_embed(
    docs=documents,
    embedding_type=EmbeddingType.OPENAI
)
```

### Example 4: Multi-Environment Configuration

```python
from app.core.config import Settings

settings = Settings.instance()

# Get application config
app_config = settings.app

# Check environment
environment = app_config['environment']

if environment == 'production':
    # Production settings
    debug = False
    log_level = 'WARNING'
    
    # Use production LLM provider
    llm_config = settings.llm
    provider = llm_config['providers']['azure_openai']  # Enterprise
    
elif environment == 'development':
    # Development settings
    debug = True
    log_level = 'DEBUG'
    
    # Use local LLM provider
    llm_config = settings.llm
    provider = llm_config['providers']['ollama']  # Local
```

### Example 5: Custom Configuration Profile

You can add your own configuration files!

**Create**: `resources/application-custom.yaml`
```yaml
custom:
  feature_flags:
    enable_caching: true
    enable_monitoring: true
    enable_rate_limiting: false
  
  api:
    rate_limit: 100
    cache_ttl: 3600
```

**Access**:
```python
settings = Settings.instance()

# Access your custom profile
custom_config = settings.custom

# Use feature flags
if custom_config['feature_flags']['enable_caching']:
    # Enable caching
    pass

# Use API settings
rate_limit = custom_config['api']['rate_limit']
cache_ttl = custom_config['api']['cache_ttl']
```

---

## Best Practices

### 1. Use Environment Variables for Secrets

```yaml
# GOOD: Use environment variables for sensitive data
database:
  password: "${POSTGRES_PASSWORD}"

# BAD: Don't hardcode secrets
database:
  password: "my_secret_password"  # Never do this!
```

### 2. Provide Sensible Defaults

```yaml
# GOOD: Provide defaults for non-sensitive settings
llm:
  temperature: "${TEMPERATURE:0.7}"   # Default to 0.7
  max_tokens: "${MAX_TOKENS:1000}"    # Default to 1000

# BAD: No defaults means it will fail if env var missing
llm:
  temperature: "${TEMPERATURE}"       # Will error if not set
```

### 3. Group Related Settings

```yaml
# GOOD: Logical grouping
llm:
  providers:
    openai:
      api_key: "..."
      model: "..."
      temperature: 0.1
    
    anthropic:
      api_key: "..."
      model: "..."
      temperature: 0.1

# BAD: Flat structure
openai_api_key: "..."
openai_model: "..."
anthropic_api_key: "..."
anthropic_model: "..."
```

### 4. Document Your Configuration

```yaml
# GOOD: Add comments
llm:
  # Default LLM provider (openai, anthropic, groq, etc.)
  default_provider: "openai"
  
  # Temperature controls randomness (0.0 = deterministic, 2.0 = very random)
  temperature: 0.1
  
  # Maximum tokens in response (limits output length and cost)
  max_tokens: 1000
```

### 5. Validate Configuration at Startup

```python
from app.core.config import Settings

settings = Settings.instance()

# Validate required profiles exist
required_profiles = ['llm', 'db', 'vector']
for profile in required_profiles:
    if not hasattr(settings, profile):
        raise ValueError(f"Missing required configuration profile: {profile}")

# Validate required keys
llm_config = settings.llm
if 'default_provider' not in llm_config:
    raise ValueError("LLM configuration missing 'default_provider'")
```

### 6. Use Type Hints in Your Code

```python
from typing import Dict, Any

def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from settings."""
    settings = Settings.instance()
    return settings.llm

def get_provider_config(provider: str) -> Dict[str, Any]:
    """Get configuration for a specific LLM provider."""
    llm_config = get_llm_config()
    return llm_config['providers'][provider]
```

---

## Configuration Approaches: Choosing Your Strategy

AgentHub supports **two flexible approaches** to managing configuration. Choose the one that best fits your project's needs:

### Approach 1: Centralized Settings Object (Recommended)

Use the global `Settings` singleton to access all configuration throughout your application.

**When to use:**
- Small to medium projects
- You want consistent configuration access everywhere
- You prefer a single source of truth
- You're building a monolithic application

**Example:**

```python
# In any module across your application
from app.core.config import Settings

settings = Settings.instance()

# Access any configuration
llm_config = settings.llm
db_config = settings.db
vector_config = settings.vector

# Use directly in functions
def create_database_connection():
    db = settings.db['postgres']
    return f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"

def create_llm():
    llm_config = settings.llm
    provider = llm_config['default_provider']
    return LLMFactory.create_llm(provider)
```

**Pros:**
- Simple and consistent
- One import pattern everywhere
- Easy to test (mock Settings.instance())
- Automatic discovery of new configuration files
- No need to maintain separate config classes

**Cons:**
- Global state (can make testing more complex)
- Less explicit dependencies
- Everything loads at startup (even unused configs)

### Approach 2: Domain-Specific Config Classes

Create dedicated configuration classes for each domain, backed by the settings object.

**When to use:**
- Large, complex applications
- You want strong typing and IDE autocompletion
- You need domain-specific validation logic
- You're building microservices or modules
- You want explicit dependencies

**Example:**

```python
# src/app/core/config/database_config.py
from dataclasses import dataclass
from typing import Dict, Any
from .framework.settings import Settings

@dataclass
class DatabaseConfig:
    """Database configuration with type safety."""
    
    def __init__(self):
        settings = Settings.instance()
        self._config = settings.db
    
    @property
    def postgres_host(self) -> str:
        return self._config['postgres']['host']
    
    @property
    def postgres_port(self) -> int:
        return self._config['postgres']['port']
    
    @property
    def postgres_database(self) -> str:
        return self._config['postgres']['database']
    
    def get_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        pg = self._config['postgres']
        return f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"

# src/app/core/config/llm_config.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .framework.settings import Settings

@dataclass
class LLMConfig:
    """LLM configuration with type safety."""
    
    def __init__(self):
        settings = Settings.instance()
        self._config = settings.llm
    
    @property
    def default_provider(self) -> str:
        return self._config['default_provider']
    
    @property
    def temperature(self) -> float:
        return self._config.get('temperature', 0.7)
    
    @property
    def max_tokens(self) -> int:
        return self._config.get('max_tokens', 1000)
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        return self._config['providers'][provider]

# Usage in your application
from app.core.config import DatabaseConfig, LLMConfig

# Inject configs explicitly
db_config = DatabaseConfig()
llm_config = LLMConfig()

# Type-safe access with IDE autocompletion
connection_string = db_config.get_connection_string()
provider = llm_config.default_provider
temperature = llm_config.temperature
```

**Pros:**
- Strong typing and IDE support
- Explicit dependencies (easier to test)
- Domain-specific validation and methods
- Better for large teams
- Encapsulates configuration logic

**Cons:**
- More boilerplate code
- Need to create/update config classes
- Two layers (YAML → Settings → Config classes)

### Comparison Table

| Aspect | Centralized Settings | Domain-Specific Classes |
|--------|---------------------|-------------------------|
| **Complexity** | Low - direct access | Medium - wrapper classes |
| **Type Safety** | Runtime (dict access) | Compile-time (properties) |
| **IDE Support** | Limited autocompletion | Full autocompletion |
| **Testing** | Mock Settings.instance() | Inject config classes |
| **Setup** | Zero - automatic | Manual - create classes |
| **Best For** | Rapid development, small apps | Large apps, strong typing |
| **Code Coupling** | Higher (global settings) | Lower (dependency injection) |
| **Extensibility** | High - just add YAML files | Medium - update classes |

### Hybrid Approach (Best of Both)

You can combine both approaches:

```python
# Use centralized settings for simple cases
from app.core.config import Settings

settings = Settings.instance()
app_name = settings.app['name']  # Quick access

# Use domain configs for complex cases
from app.core.config import DatabaseConfig, LLMConfig

class UserService:
    def __init__(self, db_config: DatabaseConfig, llm_config: LLMConfig):
        self.db = db_config
        self.llm = llm_config
    
    def create_user(self, user_data: dict):
        # Type-safe config access
        conn_string = self.db.get_connection_string()
        # ... database logic
```

### Recommendation

**For most users**: Start with **Approach 1 (Centralized Settings)**
- Simpler to understand and use
- Less code to maintain
- Faster development
- Automatic discovery of new configs

**Upgrade to Approach 2 when:**
- Your codebase exceeds 10,000 lines
- You have 3+ developers on the team
- You need strict type checking
- You're building reusable modules/microservices

**The beauty of AgentHub's configuration system**: You can switch between approaches at any time! The underlying YAML files and automatic loading remain the same - you just change how you access the configuration.

---

## Advanced: Dynamic Configuration

### Loading Configuration Dynamically

```python
from app.core.config import Settings

settings = Settings.instance()

# Get all available profiles
profiles = settings.list_sections()
print(f"Available profiles: {profiles}")
# Output: ['llm', 'db', 'vector', 'embeddings', ...]

# Dynamically access any profile
for profile_name in profiles:
    config = getattr(settings, profile_name)
    print(f"{profile_name}: {config}")
```

### Merging Configurations

```python
# Merge multiple configurations
base_config = settings.llm
custom_overrides = {
    'temperature': 0.5,
    'max_tokens': 2000
}

# Merge
merged_config = {**base_config, **custom_overrides}

# Use merged config
llm = LLMFactory.get_default_llm()
response = await llm.generate(
    messages=["Hello"],
    temperature=merged_config['temperature'],
    max_tokens=merged_config['max_tokens']
)
```

---

## Troubleshooting

### Issue 1: Profile Not Found

```python
# Error: AttributeError: 'Settings' object has no attribute 'my_custom'

# Solution: Ensure YAML file exists
# resources/application-my-custom.yaml  (hyphens)
#                     ↓
# settings.my_custom  (underscores)
```

### Issue 2: Environment Variable Not Interpolated

```yaml
# If ${VAR_NAME} appears literally in config:

# Check 1: Environment variable is set
echo $OPENAI_API_KEY

# Check 2: Syntax is correct
api_key: "${OPENAI_API_KEY}"  # Correct
api_key: "$OPENAI_API_KEY"    # Wrong (missing braces)
```

### Issue 3: KeyError When Accessing Nested Config

```python
# Error: KeyError: 'providers'

# Solution: Check for key existence
llm_config = settings.llm
if 'providers' in llm_config:
    provider = llm_config['providers']['openai']
else:
    raise ValueError("LLM configuration missing 'providers' section")
```

---

## Summary

The `resources/` directory provides a **powerful, flexible configuration system**:

| Feature | Benefit |
|---------|---------|
| **YAML Files** | Human-readable, version-controlled |
| **Profile Access** | `settings.profile_name` returns dict |
| **Environment Variables** | Override any setting with `${VAR:default}` |
| **Type Safety** | Validated with Pydantic |
| **Flexible** | Add custom profiles anytime |
| **Centralized** | Single source of truth |

### Quick Reference

```python
from app.core.config import Settings

settings = Settings.instance()

# Access profiles as dictionaries
llm = settings.llm                    # Full LLM config
db = settings.db                      # Full DB config
vector = settings.vector              # Full vector config

# Get specific values
provider = settings.llm['default_provider']
temperature = settings.llm['temperature']
pg_host = settings.db['postgres']['host']

# List all profiles
profiles = settings.list_sections()
```

---

## Next Steps

- **[Configuration System](./configuration-system.md)** - Deep dive into the configuration architecture
- **[Quick Start](../getting-started/quick-start.md)** - See configuration in action
- **[Deployment](../deployment/overview.md)** - Production configuration best practices

---

**Last Updated**: January 8, 2026  
**Related**: Configuration System, Settings, Environment Variables
