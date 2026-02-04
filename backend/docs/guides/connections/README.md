# Connection Management System

> **Unified connection management** for databases, vector stores, and external services with automatic configuration, health checking, and resilience patterns

## Table of Contents

### Overview
- [What is the Connection System?](#what-is-the-connection-system)
- [Key Features](#key-features)
- [Quick Start](#quick-start)

### Architecture
- [System Architecture](#system-architecture)
- [Base Layer](#base-layer)
- [Registry Pattern](#registry-pattern)
- [Factory Pattern](#factory-pattern)
- [Connection Types](#connection-types)

### Using Connections
- [Getting Started](#getting-started)
- [Database Connections](#database-connections)
- [PostgreSQL](#postgresql)
- [Redis](#redis)
- [MongoDB](#mongodb)
- [Vector Store Connections](#vector-store-connections)
- [Qdrant](#qdrant)
- [PgVector](#pgvector)
- [ChromaDB](#chromadb)
- [External Service Connections](#external-service-connections)
- [Confluence](#confluence)
- [Jira](#jira)
- [S3](#s3)

### Extending Connections
- [Creating Custom Connection Managers](#creating-custom-connection-managers)
- [Step-by-Step Guide](#step-by-step-guide)
- [Sync vs Async Connections](#sync-vs-async-connections)
- [Best Practices](#best-practices-for-custom-managers)

### Advanced Topics
- [Connection Lifecycle](#connection-lifecycle)
- [Health Checking](#health-checking)
- [Resilience Patterns](#resilience-patterns)
- [Connection Pooling](#connection-pooling)
- [Testing Connections](#testing-connections)

### Reference
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## What is the Connection System?

AgentHub's connection management system provides a **unified, type-safe interface** for managing connections to:

- **Databases** (PostgreSQL, Redis, MongoDB)
- **Vector Stores** (Qdrant, PgVector, ChromaDB)
- **External Services** (Confluence, Jira, S3, SharePoint, GitHub)

### Key Features

| Feature | Description |
|---------|-------------|
| **Unified Interface** | Single API for all connection types via `BaseConnectionManager` |
| **Automatic Configuration** | Connections self-configure from YAML files via registry pattern |
| **Registry Pattern** | Decorator-based registration for automatic discovery |
| **Factory Pattern** | Centralized connection creation via `ConnectionFactory` |
| **Health Checking** | Built-in health monitoring for all connections |
| **Resilience** | Retry logic, circuit breakers, and automatic reconnection |
| **Type Safety** | Enum-based connection types with full IDE support |
| **Connection Pooling** | Efficient resource management for databases |
| **Async Support** | Full async/await support for async clients |
| **Extensibility** | Easy to add new connection types without modifying core code |

---

## Quick Start

### 1. Using Existing Connections

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get a connection manager instance
postgres_manager = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)

# Connect (async)
await postgres_manager.connect()

# Use the connection
result = await postgres_manager.execute_query("SELECT * FROM users")

# Health check
if postgres_manager.is_healthy():
    print("Connection is healthy!")

# Cleanup
await postgres_manager.disconnect()
```

### 2. Context Manager Pattern (Recommended)

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Automatic connection and cleanup
async with ConnectionFactory.get_connection_manager(ConnectionType.REDIS) as redis:
    await redis.set("key", "value")
    value = await redis.get("key")
```

### 3. Check Available Connections

```python
from app.infrastructure.connections import ConnectionFactory

# List all registered connection types
available = ConnectionFactory.list_available_connections()
print(f"Available connections: {available}")

# Get detailed status
status = ConnectionFactory.get_connection_status()
print(status)
# Output:
# {
#     'total_registered': 8,
#     'available_connections': ['postgres', 'redis', 'qdrant', ...],
#     'unavailable_connections': [],
#     'connection_details': {...}
# }
```

---

## System Architecture

The connection system uses multiple design patterns for flexibility and extensibility.

```
┌─────────────────────────────────────────────────────────────┐
│ Application Layer │
│ (Your code uses connections) │
└─────────────────────────┬───────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ ConnectionFactory │
│ (Create connection manager instances) │
└─────────────────────────┬───────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ ConnectionRegistry │
│ (Maps ConnectionType → Manager Class via decorator) │
└─────────────────────────┬───────────────────────────────────┘
│
┌──────────────┼──────────────┐
▼ ▼ ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ Database │ │ Vector Store │ │ External │
│ Managers │ │ Managers │ │ Service │
│ │ │ │ │ Managers │
└─────────────┘ └──────────────┘ └──────────────┘
│ │ │
└──────────────┼──────────────┘
│
▼
┌───────────────────────────────┐
│ BaseConnectionManager │
│ (Abstract base class) │
└───────────────┬───────────────┘
│
┌────────────┴────────────┐
▼ ▼
┌─────────────────────┐ ┌──────────────────────┐
│ BaseConnection │ │ AsyncBaseConnection │
│ Manager │ │ Manager │
│ (Sync connections) │ │ (Async connections) │
└─────────────────────┘ └──────────────────────┘
│ │
┌─────────┴─────────┐ ┌─────────┴──────────┐
│ Confluence │ │ PostgreSQL │
│ Jira │ │ Redis │
│ Qdrant │ │ MongoDB │
└───────────────────┘ └────────────────────┘
```

### Base Layer

#### `BaseConnectionManager` (Abstract Base Class)

**Location**: `src/app/connections/base/base_connection_manager.py`

**Purpose**: Defines the interface all connection managers must implement

**Core Methods**:
```python
class BaseConnectionManager(ABC):
# Must implement
@abstractmethod
def get_connection_name(self) -> str: pass

@abstractmethod
def validate_config(self) -> None: pass

@abstractmethod
def connect(self) -> Any: pass

@abstractmethod
def disconnect(self) -> None: pass

@abstractmethod
def is_healthy(self) -> bool: pass

# Provided by base class
def ensure_connected(self) -> Any: pass
def reconnect(self) -> Any: pass
def get_connection_info(self) -> Dict: pass
```

**Key Features**:
- **Template Method Pattern**: Child classes define connection name, base retrieves config
- **Automatic Configuration**: Uses `ConfigSourceRegistry` to get appropriate config
- **Early Validation**: Validates configuration in `__init__` to fail fast
- **Connection State**: Tracks `_connection` and `_is_connected` status

#### `AsyncBaseConnectionManager`

**Location**: `src/app/connections/base/async_base_connection_manager.py`

**Purpose**: Async variant for truly asynchronous clients (PostgreSQL, Redis, MongoDB)

**Key Differences**:
```python
class AsyncBaseConnectionManager(BaseConnectionManager):
# Async versions of abstract methods
@abstractmethod
async def connect(self) -> Any: pass

@abstractmethod
async def disconnect(self) -> None: pass

# Async context manager support
async def __aenter__(self): pass
async def __aexit__(self, ...): pass
```

**When to Use**:
- Use `AsyncBaseConnectionManager` for clients with native async support (asyncpg, redis.asyncio, motor)
- Use `BaseConnectionManager` for sync clients (atlassian-python-api, qdrant-client)

### Registry Pattern

#### `ConnectionRegistry`

**Location**: `src/app/connections/base/connection_registry.py`

**Purpose**: Decorator-based registration system for automatic connection discovery

**How It Works**:

1. **Registration** (happens at module import):
```python
from app.infrastructure.connections.base import ConnectionRegistry, ConnectionType

@ConnectionRegistry.register(ConnectionType.POSTGRES)
class PostgresConnectionManager(AsyncBaseConnectionManager):
pass
```

2. **Lookup** (happens at runtime):
```python
# Get connection manager class for a type
manager_class = ConnectionRegistry.get_connection_manager_class(ConnectionType.POSTGRES)

# Create instance
manager = manager_class()
```

**Key Methods**:
- `register(connection_type)` - Decorator to register a connection manager
- `get_connection_manager_class(connection_type)` - Retrieve registered class
- `is_connection_registered(connection_type)` - Check if type is registered
- `list_connections()` - List all registered types
- `get_registry_info()` - Get registry statistics

### Factory Pattern

#### `ConnectionFactory`

**Location**: `src/app/connections/factory/connection_factory.py`

**Purpose**: Centralized factory for creating connection manager instances

**Key Methods**:

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get a connection manager instance
manager = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)

# List available connections
available = ConnectionFactory.list_available_connections()

# Check if connection is available and configured
is_available = ConnectionFactory.is_connection_available(ConnectionType.REDIS)

# Get status of all connections
status = ConnectionFactory.get_connection_status()
```

**Singleton Pattern**: Factory is a singleton (one instance per application)

### Connection Types

**Location**: `src/app/core/core_enums.py`

**All Supported Types**:

```python
from app.infrastructure.connections import ConnectionType

# Database connections
ConnectionType.POSTGRES # PostgreSQL
ConnectionType.REDIS # Redis cache
ConnectionType.MONGODB # MongoDB

# Vector store connections
ConnectionType.QDRANT # Qdrant vector database
ConnectionType.PGVECTOR # PostgreSQL + pgvector
ConnectionType.CHROMADB # ChromaDB

# External service connections
ConnectionType.CONFLUENCE # Atlassian Confluence
ConnectionType.JIRA # Atlassian Jira
ConnectionType.S3 # AWS S3 (future)
```

---

## Getting Started

### Step 1: Ensure Configuration

Connection managers automatically load configuration from YAML files. Ensure your configuration exists:

```yaml
# resources/application-db.yaml
db:
postgres:
host: "${POSTGRES_HOST:localhost}"
port: "${POSTGRES_PORT:5432}"
database: "${POSTGRES_DB:agenthub}"
username: "${POSTGRES_USER:postgres}"
password: "${POSTGRES_PASSWORD}"
pool_size: 10
```

**See**: [Configuration Guide](../configuration/README.md) for details

### Step 2: Get Connection Manager

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get connection manager (not connected yet)
manager = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)
```

### Step 3: Connect

```python
# For async connections (PostgreSQL, Redis, MongoDB)
await manager.connect()

# For sync connections (Confluence, Jira, Qdrant)
manager.connect()
```

### Step 4: Use Connection

```python
# PostgreSQL example
result = await manager.execute_query("SELECT * FROM users WHERE id = $1", user_id)

# Redis example
await manager.set("key", "value")
value = await manager.get("key")

# Confluence example
pages = manager.get_space_pages("SPACE_KEY")
```

### Step 5: Cleanup

```python
# For async connections
await manager.disconnect()

# For sync connections
manager.disconnect()
```

### Recommended Pattern: Context Manager

```python
# Async connections
async with ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES) as pg:
result = await pg.execute_query("SELECT * FROM users")
# Automatic disconnect on exit

# Sync connections (not all support context manager)
manager = ConnectionFactory.get_connection_manager(ConnectionType.CONFLUENCE)
try:
manager.connect()
pages = manager.get_space_pages("SPACE_KEY")
finally:
manager.disconnect()
```

---

## Database Connections

### PostgreSQL

**Connection Type**: `ConnectionType.POSTGRES`

**Manager Class**: `PostgresConnectionManager`

**Configuration** (`application-db.yaml`):
```yaml
db:
postgres:
host: "${POSTGRES_HOST:localhost}"
port: "${POSTGRES_PORT:5432}"
database: "${POSTGRES_DB:agenthub}"
username: "${POSTGRES_USER:postgres}"
password: "${POSTGRES_PASSWORD}"
pool_size: 10
connection_timeout: 30
ssl_mode: "prefer" # optional
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
postgres = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)

# Connect (creates connection pool)
await postgres.connect()

# Execute query
users = await postgres.execute_query(
"SELECT * FROM users WHERE age > $1",
25
)

# Execute command
status = await postgres.execute_command(
"INSERT INTO users (name, email) VALUES ($1, $2)",
"John Doe",
"john@example.com"
)

# Get a connection from pool
async with postgres.connection_pool.acquire() as conn:
await conn.execute("UPDATE users SET active = true WHERE id = $1", user_id)

# Cleanup
await postgres.disconnect()
```

**Features**:
- Connection pooling (asyncpg)
- Prepared statements support
- Transaction management
- SSL/TLS support
- Health checking

---

### Redis

**Connection Type**: `ConnectionType.REDIS`

**Manager Class**: `RedisConnectionManager`

**Configuration** (`application-db.yaml`):
```yaml
db:
redis:
host: "${REDIS_HOST:localhost}"
port: "${REDIS_PORT:6379}"
password: "${REDIS_PASSWORD:}"
database: "${REDIS_DB:0}"
connection_pool_size: 10
socket_timeout: 5
health_check_interval: 30
ssl: false
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
redis = ConnectionFactory.get_connection_manager(ConnectionType.REDIS)

# Connect
await redis.connect()

# Set/Get operations
await redis.set("user:123", "John Doe", ex=3600) # Expires in 1 hour
value = await redis.get("user:123")

# Hash operations
await redis.hset("user:123:profile", mapping={"name": "John", "age": 30})
profile = await redis.hgetall("user:123:profile")

# List operations
await redis.lpush("queue", "task1", "task2")
task = await redis.rpop("queue")

# Advanced: Pipeline for bulk operations
async with redis.pipeline() as pipe:
pipe.set("key1", "value1")
pipe.set("key2", "value2")
pipe.get("key1")
results = await pipe.execute()

# Cleanup
await redis.disconnect()
```

**Features**:
- Connection pooling
- Pipeline support for bulk operations
- Pub/Sub support
- SSL/TLS support
- Automatic decode to strings
- Health checking with ping

---

### MongoDB

**Connection Type**: `ConnectionType.MONGODB`

**Manager Class**: `MongoDBConnectionManager`

**Configuration** (`application-db.yaml`):
```yaml
db:
mongodb:
host: "${MONGODB_HOST:localhost}"
port: "${MONGODB_PORT:27017}"
database: "${MONGODB_DB:agenthub}"
username: "${MONGODB_USER:}"
password: "${MONGODB_PASSWORD:}"
# OR use connection string for Atlas
connection_string: "${MONGODB_CONNECTION_STRING:}"
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
mongo = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)

# Connect
await mongo.connect()

# Get database
db = mongo.get_database()

# Insert document
result = await db.users.insert_one({
"name": "John Doe",
"email": "john@example.com",
"age": 30
})

# Find documents
users = await db.users.find({"age": {"$gt": 25}}).to_list(length=100)

# Update document
await db.users.update_one(
{"_id": result.inserted_id},
{"$set": {"active": True}}
)

# Delete document
await db.users.delete_one({"_id": result.inserted_id})

# Cleanup
await mongo.disconnect()
```

**Features**:
- MongoDB Atlas support (cloud)
- Local MongoDB support
- Async operations (motor)
- Full MongoDB query API
- Health checking

---

## Vector Store Connections

### Qdrant

**Connection Type**: `ConnectionType.QDRANT`

**Manager Class**: `QdrantConnectionManager`

**Configuration** (`application-vector.yaml`):
```yaml
vector:
qdrant:
url: "${QDRANT_URL:http://localhost:6333}"
api_key: "${QDRANT_API_KEY:}"
collection_name: "${QDRANT_COLLECTION:agent_hub_collection}"
embedding_dimension: 1536
distance: "Cosine" # Cosine, Euclid, or Dot
timeout: 60
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
qdrant = ConnectionFactory.get_connection_manager(ConnectionType.QDRANT)

# Connect (auto-creates collection if needed)
qdrant.connect()

# Insert vectors
qdrant.upsert_vectors(
points=[
{
"id": "doc1",
"vector": [0.1, 0.2, ...], # 1536 dimensions
"payload": {"text": "Document content", "metadata": {...}}
}
]
)

# Search similar vectors
results = qdrant.search(
query_vector=[0.1, 0.2, ...],
limit=10,
score_threshold=0.7
)

# Get vector by ID
point = qdrant.get_vector("doc1")

# Delete vectors
qdrant.delete_vectors(["doc1", "doc2"])

# Cleanup
qdrant.disconnect()
```

**Features**:
- Automatic collection creation
- Multiple distance metrics
- Payload filtering
- Batch operations
- Cloud and self-hosted support

---

### PgVector

**Connection Type**: `ConnectionType.PGVECTOR`

**Manager Class**: `PgVectorConnectionManager`

**Configuration** (`application-vector.yaml`):
```yaml
vector:
pgvector:
connection_string: "${PGVECTOR_CONNECTION_STRING:}" # Or uses postgres config
collection_name: "${PGVECTOR_COLLECTION:documents}"
embedding_dimension: 1536
distance_strategy: "cosine" # cosine, l2, or inner_product
pre_delete_collection: false
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
pgvector = ConnectionFactory.get_connection_manager(ConnectionType.PGVECTOR)

# Connect
await pgvector.connect()

# Insert vectors
await pgvector.add_embeddings(
texts=["Document 1", "Document 2"],
embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
metadatas=[{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]
)

# Search similar vectors
results = await pgvector.similarity_search(
query_embedding=[0.1, 0.2, ...],
k=10
)

# Cleanup
await pgvector.disconnect()
```

**Features**:
- Leverages PostgreSQL infrastructure
- ACID transactions for vectors
- Multiple distance strategies
- Efficient indexing

---

### ChromaDB

**Connection Type**: `ConnectionType.CHROMADB`

**Manager Class**: `ChromaDBConnectionManager`

**Configuration** (`application-vector.yaml`):
```yaml
vector:
chromadb:
collection_name: "${CHROMA_COLLECTION:documents}"
persist_directory: "./volumes/chromadb"
embedding_type: "openai"
distance_metric: "cosine"
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
chroma = ConnectionFactory.get_connection_manager(ConnectionType.CHROMADB)

# Connect
chroma.connect()

# Add documents
chroma.add_documents(
documents=["Document 1", "Document 2"],
metadatas=[{"source": "doc1"}, {"source": "doc2"}],
ids=["id1", "id2"]
)

# Query
results = chroma.query(
query_texts=["search query"],
n_results=10
)

# Cleanup
chroma.disconnect()
```

**Features**:
- Embedded and client-server modes
- Automatic persistence
- Multiple embedding functions
- Simple API

---

## External Service Connections

### Confluence

**Connection Type**: `ConnectionType.CONFLUENCE`

**Manager Class**: `ConfluenceConnectionManager`

**Configuration** (`application-external.yaml`):
```yaml
external:
atlassian:
api_key: "${ATLASSIAN_API_KEY}"
email: "${ATLASSIAN_EMAIL}"
confluence_base_url: "${CONFLUENCE_BASE_URL}"
timeout: 30
page_limit: 100
space_keys: ["*"] # or specific spaces like ["ENG", "PROD"]
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
confluence = ConnectionFactory.get_connection_manager(ConnectionType.CONFLUENCE)

# Connect
confluence.connect()

# Get spaces
spaces = confluence.get_all_spaces()

# Get pages from space
pages = confluence.get_space_pages("SPACE_KEY", limit=50)

# Get page content
page = confluence.get_page_by_id("12345678", expand="body.storage")
content = page['body']['storage']['value']

# Search
results = confluence.search_content(
cql="type=page AND space=SPACE_KEY AND title~'API'",
limit=25
)

# Cleanup
confluence.disconnect()
```

**Features**:
- Full Confluence REST API access
- Resilience patterns (retry, circuit breaker)
- Space and page management
- CQL search support
- Automatic authentication

**See Also**: [Confluence Tools Guide](../tools/confluence-tools.md)

---

### Jira

**Connection Type**: `ConnectionType.JIRA`

**Manager Class**: `JiraConnectionManager`

**Configuration** (`application-external.yaml`):
```yaml
external:
atlassian:
api_key: "${ATLASSIAN_API_KEY}"
email: "${ATLASSIAN_EMAIL}"
jira_base_url: "${JIRA_BASE_URL}"
timeout: 30
```

**Usage**:
```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager
jira = ConnectionFactory.get_connection_manager(ConnectionType.JIRA)

# Connect
jira.connect()

# Get projects
projects = jira.get_all_projects()

# Create issue
issue = jira.create_issue(
project="PROJ",
summary="Bug in login",
description="Users cannot log in",
issue_type="Bug"
)

# Get issue
issue = jira.get_issue("PROJ-123")

# Search issues (JQL)
issues = jira.search_issues(
jql="project=PROJ AND status='In Progress'",
max_results=50
)

# Update issue
jira.update_issue("PROJ-123", fields={"status": "Done"})

# Cleanup
jira.disconnect()
```

**Features**:
- Full Jira REST API access
- Resilience patterns (retry, circuit breaker)
- JQL query support
- Issue management
- Automatic authentication

**See Also**: [Jira Tools Guide](../tools/jira-tools.md)

---

### S3

**Connection Type**: `ConnectionType.S3` (Future)

**Manager Class**: `S3ConnectionManager`

**Configuration** (`application-external.yaml`):
```yaml
external:
s3:
access_key_id: "${AWS_ACCESS_KEY_ID}"
secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
region: "${AWS_REGION:us-east-1}"
bucket_name: "${S3_BUCKET_NAME}"
endpoint_url: "${S3_ENDPOINT_URL:}" # For MinIO/custom endpoints
```

**Status**: Under development

---

## Creating Custom Connection Managers

### Configuration Pattern (Updated Feb 2026)

Connection managers now use a **simplified configuration access pattern**:

**How Configuration Works:**
1. Each manager implements `get_config_category()` → returns `"db"`, `"vector"`, or `"external"`
2. Each manager implements `get_connection_name()` → returns the connection name (e.g., `"elasticsearch"`)
3. Base class automatically constructs: `settings.{category}.{connection_name}`
4. Example: `get_config_category()` returns `"db"` + `get_connection_name()` returns `"elasticsearch"` → `settings.db.elasticsearch`

**Accessing Configuration:**
```python
# In your connection manager methods:
config_dict = self._get_config_dict()  # Always get as dictionary

# Use dictionary access
value = config_dict['key']
value = config_dict.get('key', default_value)
```

**Configuration File Structure:**
```yaml
# application-db.yaml (for databases)
db:
  elasticsearch:  # This is the connection_name
    hosts: ["http://localhost:9200"]
    api_key: "${ELASTICSEARCH_API_KEY}"

# application-vector.yaml (for vector stores)
vector:
  elasticsearch:
    hosts: ["http://localhost:9200"]

# application-external.yaml (for external services)
external:
  elasticsearch:
    hosts: ["http://localhost:9200"]
```

**Key Points:**
- ✅ No wrapper classes needed - direct `settings` access
- ✅ Base class handles configuration retrieval automatically
- ✅ Use `_get_config_dict()` in your methods for dictionary access
- ✅ Category determines which YAML file (`db`, `vector`, `external`)

### Step-by-Step Guide

Want to add support for a new database, vector store, or external service? Follow this guide!

#### Step 1: Choose Base Class

**Decision Matrix**:

| Client Type | Base Class | Example |
|-------------|-----------|---------|
| **Native async** (asyncio, async/await) | `AsyncBaseConnectionManager` | asyncpg, motor, redis.asyncio |
| **Sync only** | `BaseConnectionManager` | atlassian-python-api, qdrant-client |
| **Has async wrapper** | `AsyncBaseConnectionManager` | Use async wrapper if available |

#### Step 2: Define Connection Type

Add to `src/app/core/core_enums.py`:

```python
class ConnectionType(str, Enum):
# ... existing types ...

# Add your new type
ELASTICSEARCH = "elasticsearch"
```

#### Step 3: Create Connection Manager

Create file: `src/app/connections/[category]/[name]_connection_manager.py`

**Categories**:
- `database/` - Databases (SQL, NoSQL)
- `vector/` - Vector databases
- `external/` - External services/APIs

**Example** (Elasticsearch - Async):

```python
"""
Elasticsearch connection manager implementation.
"""

from typing import Any, Optional
from elasticsearch import AsyncElasticsearch

from app.infrastructure.connections.base import AsyncBaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.ELASTICSEARCH)
class ElasticsearchConnectionManager(AsyncBaseConnectionManager):
"""Elasticsearch connection manager implementation."""

def __init__(self):
super().__init__()
self._es_client: Optional[AsyncElasticsearch] = None

def get_connection_name(self) -> str:
"""Return the configuration name for Elasticsearch."""
return ConnectionType.ELASTICSEARCH.value
    
def get_config_category(self) -> str:
"""Return the configuration category for databases."""
return "db"  # or "vector" or "external" based on your service type

def validate_config(self) -> None:
"""Validate Elasticsearch configuration."""
config_dict = self._get_config_dict()  # Get config as dictionary
required_fields = ['hosts']

for field in required_fields:
if not config_dict.get(field):
raise ValueError(f"Elasticsearch requires '{field}' in configuration")

        # Validate hosts format
hosts = config_dict.get('hosts')
if not isinstance(hosts, list) or len(hosts) == 0:
raise ValueError("Elasticsearch hosts must be a non-empty list")

logger.info("Elasticsearch configuration validated successfully")

async def connect(self) -> AsyncElasticsearch:
"""Establish Elasticsearch connection."""
if self._es_client:
# Test existing connection
try:
await self._es_client.ping()
return self._es_client
except Exception:
# Connection stale, recreate
await self.disconnect()

try:
config_dict = self._get_config_dict()  # Get config as dictionary
            
# Create client
self._es_client = AsyncElasticsearch(
hosts=config_dict['hosts'],
api_key=config_dict.get('api_key'),
timeout=config_dict.get('timeout', 30),
max_retries=config_dict.get('max_retries', 3)
)

# Test connection
if not await self._es_client.ping():
raise ConnectionError("Failed to ping Elasticsearch")

self._connection = self._es_client
self._is_connected = True

logger.info(f"Elasticsearch connection established to {config_dict['hosts']}")
return self._es_clientexcept Exception as e:
self._connection = None
self._is_connected = False
logger.error(f"Failed to connect to Elasticsearch: {e}")
raise ConnectionError(f"Elasticsearch connection failed: {e}")

async def disconnect(self) -> None:
"""Close Elasticsearch connection."""
if self._es_client:
try:
await self._es_client.close()
logger.info("Elasticsearch connection closed")
except Exception as e:
logger.warning(f"Error closing Elasticsearch connection: {e}")
finally:
self._es_client = None
self._connection = None
self._is_connected = False

def is_healthy(self) -> bool:
"""Check if Elasticsearch connection is healthy."""
if not self._es_client:
return False

try:
# Basic check - connection exists
return True
except Exception:
return False

# Elasticsearch-specific methods
async def search(self, index: str, query: dict) -> dict:
"""Execute search query."""
await self.ensure_connected()
return await self._es_client.search(index=index, body=query)

async def index_document(self, index: str, document: dict, doc_id: Optional[str] = None) -> dict:
"""Index a document."""
await self.ensure_connected()
return await self._es_client.index(index=index, body=document, id=doc_id)
```

#### Step 4: Add Configuration

Add to appropriate config file (e.g., `resources/application-db.yaml` for databases):

```yaml
db:
elasticsearch:
hosts:
- "http://localhost:9200"
api_key: "${ELASTICSEARCH_API_KEY:}"
timeout: 30
max_retries: 3
```

#### Step 5: Register in Package Init

Update `src/app/connections/[category]/__init__.py`:

```python
"""Database connection managers."""

from .postgres_connection_manager import PostgresConnectionManager
from .redis_connection_manager import RedisConnectionManager
from .mongodb_connection_manager import MongoDBConnectionManager
from .elasticsearch_connection_manager import ElasticsearchConnectionManager # Add this

__all__ = [
'PostgresConnectionManager',
'RedisConnectionManager',
'MongoDBConnectionManager',
'ElasticsearchConnectionManager' # Add this
]
```

#### Step 6: Register Config Source

Add connection type to config source decorator in `src/app/core/config/providers/[category].py`:

```python
@register_config(['postgres', 'redis', 'mongodb', 'elasticsearch']) # Add 'elasticsearch'
class DatabaseConfig(BaseConfigSource):
# ... existing code ...

@property
def elasticsearch_config(self) -> Dict[str, Any]:
"""Elasticsearch configuration."""
if not hasattr(settings, 'db') or not hasattr(settings.db, 'elasticsearch'):
return {}

es = settings.db.elasticsearch
return {
'hosts': es.hosts,
'api_key': getattr(es, 'api_key', None),
'timeout': getattr(es, 'timeout', 30),
'max_retries': getattr(es, 'max_retries', 3)
}
```

#### Step 7: Test Your Connection

Create test file: `tests/integration/test_elasticsearch_connection.py`

```python
import pytest
from app.infrastructure.connections import ConnectionFactory, ConnectionType


@pytest.mark.asyncio
async def test_elasticsearch_connection():
"""Test Elasticsearch connection manager."""
# Get manager
manager = ConnectionFactory.get_connection_manager(ConnectionType.ELASTICSEARCH)

# Validate configuration
assert manager.config is not None
assert 'hosts' in manager.config

# Connect
await manager.connect()
assert manager.is_connected

# Test health check
assert manager.is_healthy()

# Test custom method
result = await manager.search(
index="test-index",
query={"query": {"match_all": {}}}
)
assert result is not None

# Cleanup
await manager.disconnect()
assert not manager.is_connected
```

#### Step 8: Usage Example

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Use your new connection manager!
async with ConnectionFactory.get_connection_manager(ConnectionType.ELASTICSEARCH) as es:
# Search
results = await es.search(
index="documents",
query={"query": {"match": {"title": "search term"}}}
)

# Index document
await es.index_document(
index="documents",
document={"title": "My Document", "content": "Document content"}
)
```

---

### Sync vs Async Connections

#### When to Use Async

Use `AsyncBaseConnectionManager` when:
- Client library has native async support (asyncpg, motor, redis.asyncio)
- High concurrency expected (many simultaneous connections)
- I/O-bound operations (network calls)
- Integration with async frameworks (FastAPI, aiohttp)

**Example Libraries**:
- `asyncpg` (PostgreSQL)
- `redis.asyncio` (Redis)
- `motor` (MongoDB)
- `elasticsearch[async]` (Elasticsearch)
- `httpx` (HTTP client)

#### When to Use Sync

Use `BaseConnectionManager` when:
- Client library is sync-only (atlassian-python-api, qdrant-client)
- Operations are fast and don't block
- Simpler implementation needed
- No async version available

**Example Libraries**:
- `atlassian-python-api` (Confluence, Jira)
- `qdrant-client` (Qdrant - has sync and async, we use sync)
- `boto3` (AWS S3 - sync only, use aioboto3 for async)

#### Comparison

```python
# ASYNC CONNECTION
@ConnectionRegistry.register(ConnectionType.POSTGRES)
class PostgresConnectionManager(AsyncBaseConnectionManager):
async def connect(self) -> Pool:
self._pool = await asyncpg.create_pool(...)
return self._pool

async def disconnect(self) -> None:
await self._pool.close()

# Usage
async with manager as conn:
result = await manager.execute_query("SELECT * FROM users")


# SYNC CONNECTION
@ConnectionRegistry.register(ConnectionType.CONFLUENCE)
class ConfluenceConnectionManager(BaseConnectionManager):
def connect(self) -> Confluence:
self._client = Confluence(...)
return self._client

def disconnect(self) -> None:
self._client = None

# Usage
manager = ConnectionFactory.get_connection_manager(ConnectionType.CONFLUENCE)
manager.connect()
pages = manager.get_space_pages("SPACE")
manager.disconnect()
```

---

### Best Practices for Custom Managers

#### 1. Configuration Validation

Always validate configuration in `validate_config()`:

```python
def validate_config(self) -> None:
"""Validate configuration early."""
# Check required fields
required_fields = ['host', 'port', 'api_key']
for field in required_fields:
if not self.config.get(field):
raise ValueError(f"Missing required field: '{field}'")

# Validate data types
port = self.config.get('port')
if not isinstance(port, int) or port <= 0:
raise ValueError(f"Port must be a positive integer, got: {port}")

# Validate format
url = self.config.get('url')
if not url.startswith(('http://', 'https://')):
raise ValueError(f"URL must start with http:// or https://, got: {url}")

logger.info(f"{self.__class__.__name__} configuration validated")
```

#### 2. Connection Testing

Test connection immediately after establishing:

```python
async def connect(self) -> Client:
"""Connect and test."""
try:
# Create client
self._client = await Client.connect(...)

# TEST CONNECTION IMMEDIATELY
await self._client.ping() # or similar health check

self._connection = self._client
self._is_connected = True

logger.info("Connection established and tested")
return self._client

except Exception as e:
self._connection = None
self._is_connected = False
raise ConnectionError(f"Connection failed: {e}")
```

#### 3. Proper Cleanup

Always cleanup resources in `disconnect()`:

```python
async def disconnect(self) -> None:
"""Cleanup all resources."""
if self._client:
try:
await self._client.close()
logger.info("Client closed")
except Exception as e:
logger.warning(f"Error closing client: {e}")
finally:
self._client = None

if self._connection_pool:
try:
await self._connection_pool.aclose()
except Exception as e:
logger.warning(f"Error closing pool: {e}")
finally:
self._connection_pool = None

# Reset state
self._connection = None
self._is_connected = False
```

#### 4. Health Checking

Implement meaningful health checks:

```python
def is_healthy(self) -> bool:
"""Check connection health."""
if not self._client:
return False

try:
# For async clients, basic check
return True

except Exception:
return False

async def async_is_healthy(self) -> bool:
"""Async health check with actual test."""
if not self._client:
return False

try:
# Perform actual health check
await self._client.ping()
return True
except Exception:
return False
```

#### 5. Logging

Log important events:

```python
# Configuration validation
logger.info("Configuration validated successfully")

# Connection established
logger.info(f"Connected to {service} at {host}:{port}")

# Connection failed
logger.error(f"Failed to connect: {error}")

# Connection closed
logger.info("Connection closed")

# Health check failed
logger.warning("Health check failed")
```

#### 6. Error Handling

Provide clear error messages:

```python
try:
connection = await create_connection()
except TimeoutError as e:
raise ConnectionError(f"Connection timed out after {timeout}s: {e}")
except AuthenticationError as e:
raise ConnectionError(f"Authentication failed: {e}")
except Exception as e:
raise ConnectionError(f"Unexpected connection error: {e}")
```

#### 7. Add Convenience Methods

Add domain-specific methods for common operations:

```python
class ElasticsearchConnectionManager(AsyncBaseConnectionManager):
# ... base methods ...

# Convenience methods
async def search(self, index: str, query: dict) -> dict:
"""Execute search query."""
await self.ensure_connected()
return await self._client.search(index=index, body=query)

async def bulk_index(self, index: str, documents: list) -> dict:
"""Bulk index documents."""
await self.ensure_connected()
# Implementation...

async def create_index(self, index: str, mappings: dict) -> dict:
"""Create index with mappings."""
await self.ensure_connected()
# Implementation...
```

---

## Connection Lifecycle

Understanding the connection lifecycle helps with proper resource management.

### Lifecycle States

```
┌─────────────────────────────────────────────────────────────┐
│ UNINITIALIZED │
│ (Manager instance created) │
└──────────────────────┬──────────────────────────────────────┘
│
│ __init__() called
│ - Loads configuration
│ - Validates config
│
▼
┌─────────────────────────────────────────────────────────────┐
│ INITIALIZED │
│ (Configured but not connected) │
│ _is_connected = False │
└──────────────────────┬──────────────────────────────────────┘
│
│ connect() called
│ - Establishes connection
│ - Tests connection
│ - Sets _is_connected = True
│
▼
┌─────────────────────────────────────────────────────────────┐
│ CONNECTED │
│ (Active connection established) │
│ _is_connected = True │
└─────┬──────────────────────────┬─────────────────────────────┘
│ │
│ is_healthy() → False │ disconnect() called
│ (connection lost) │ - Closes connection
│ │ - Cleanup resources
│ │
▼ ▼
┌─────────────────────┐ ┌─────────────────────┐
│ UNHEALTHY │ │ DISCONNECTED │
│ (Needs reconnect) │ │ (Cleanly closed) │
└─────┬───────────────┘ └─────────────────────┘
│ 
│ reconnect() called 
│ - Disconnects 
│ - Connects again 
│ 
└────────────► CONNECTED
```

### Automatic Reconnection

Use `ensure_connected()` for automatic reconnection:

```python
# Async example
async def my_operation():
# This will automatically reconnect if connection is lost
await manager.ensure_connected()

# Now safe to use
result = await manager.execute_query("SELECT * FROM users")

# Sync example
def my_operation():
manager.ensure_connected()
pages = manager.get_space_pages("SPACE")
```

### Manual Reconnection

Force reconnection when needed:

```python
# Check health
if not manager.is_healthy():
# Force reconnection
await manager.reconnect() # or manager.reconnect() for sync
```

---

## Health Checking

All connection managers implement health checking.

### Basic Health Check

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

manager = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)
await manager.connect()

# Check if healthy
if manager.is_healthy():
print("Connection is healthy")
else:
print("Connection is unhealthy")
await manager.reconnect()
```

### Periodic Health Monitoring

```python
import asyncio
from app.infrastructure.connections import ConnectionFactory, ConnectionType

async def monitor_connection(manager, interval: int = 30):
"""Monitor connection health periodically."""
while True:
try:
if not manager.is_healthy():
logger.warning("Connection unhealthy, reconnecting...")
await manager.reconnect()
logger.info("Reconnection successful")
except Exception as e:
logger.error(f"Health check failed: {e}")

await asyncio.sleep(interval)

# Start monitoring
manager = ConnectionFactory.get_connection_manager(ConnectionType.REDIS)
await manager.connect()
asyncio.create_task(monitor_connection(manager))
```

### Health Check Endpoint (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from app.infrastructure.connections import ConnectionFactory, ConnectionType

app = FastAPI()

@app.get("/health/connections")
async def check_connections():
"""Check health of all connections."""
results = {}

# Check each connection type
for conn_type in [ConnectionType.POSTGRES, ConnectionType.REDIS, ConnectionType.QDRANT]:
try:
manager = ConnectionFactory.get_connection_manager(conn_type)
results[conn_type.value] = {
"connected": manager.is_connected,
"healthy": manager.is_healthy()
}
except Exception as e:
results[conn_type.value] = {
"connected": False,
"healthy": False,
"error": str(e)
}

# Return 503 if any unhealthy
all_healthy = all(r["healthy"] for r in results.values())
if not all_healthy:
raise HTTPException(status_code=503, detail="Some connections unhealthy")

return results
```

---

## Resilience Patterns

Connection managers support resilience patterns for external services.

### Retry Pattern

Automatically retry failed operations:

```python
from app.core.resilience import retry, RetryConfig, RetryStrategy

# Define retry configuration
CONFLUENCE_RETRY_CONFIG = RetryConfig(
max_attempts=3,
base_delay=1.0,
max_delay=10.0,
strategy=RetryStrategy.EXPONENTIAL,
jitter=True
)

# Apply to methods
class ConfluenceConnectionManager(BaseConnectionManager):
@retry(CONFLUENCE_RETRY_CONFIG)
def get_space_pages(self, space_key: str):
"""Get pages with automatic retry on failure."""
return self._client.get_all_pages_from_space(space_key)
```

### Circuit Breaker Pattern

Prevent cascading failures:

```python
from app.core.resilience import circuit_breaker, CircuitBreakerConfig

# Define circuit breaker
JIRA_CIRCUIT_CONFIG = CircuitBreakerConfig(
name="jira_api",
failure_threshold=5, # Open after 5 failures
failure_window=60.0, # Within 60 seconds
recovery_timeout=30.0, # Wait 30s before retry
success_threshold=2 # Need 2 successes to close
)

# Apply to methods
class JiraConnectionManager(BaseConnectionManager):
@circuit_breaker(JIRA_CIRCUIT_CONFIG)
def search_issues(self, jql: str):
"""Search with circuit breaker protection."""
return self._client.jql(jql)
```

### Combined Patterns

Use both retry and circuit breaker:

```python
class ExternalServiceManager(BaseConnectionManager):
@retry(RETRY_CONFIG)
@circuit_breaker(CIRCUIT_CONFIG)
def call_external_api(self, endpoint: str):
"""Call API with retry and circuit breaker."""
return self._client.get(endpoint)
```

---

## Connection Pooling

### PostgreSQL Connection Pooling

PostgreSQL manager uses asyncpg connection pooling:

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager with pool
postgres = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)
await postgres.connect() # Creates pool

# Get connection from pool
async with postgres.connection_pool.acquire() as conn:
await conn.execute("INSERT INTO users ...")

# Pool automatically manages connections
# - Reuses connections
# - Limits maximum connections
# - Health checks idle connections
```

**Configuration**:
```yaml
db:
postgres:
pool_size: 10 # Max connections in pool
connection_timeout: 30 # Connection timeout
```

### Redis Connection Pooling

Redis manager uses redis.asyncio connection pooling:

```python
from app.infrastructure.connections import ConnectionFactory, ConnectionType

# Get manager with pool
redis = ConnectionFactory.get_connection_manager(ConnectionType.REDIS)
await redis.connect() # Creates pool

# Use client (automatically uses pool)
await redis.set("key", "value")
await redis.get("key")

# Pool configuration
```

**Configuration**:
```yaml
db:
redis:
connection_pool_size: 10
health_check_interval: 30
```

---

## Testing Connections

### Unit Tests

Mock connection managers in unit tests:

```python
import pytest
from unittest.mock import Mock, AsyncMock
from app.infrastructure.connections import ConnectionType

@pytest.fixture
def mock_postgres_manager():
"""Mock PostgreSQL connection manager."""
manager = Mock()
manager.connect = AsyncMock()
manager.disconnect = AsyncMock()
manager.execute_query = AsyncMock(return_value=[{"id": 1, "name": "test"}])
manager.is_healthy.return_value = True
return manager

@pytest.mark.asyncio
async def test_my_service(mock_postgres_manager):
"""Test service with mocked connection."""
# Your test code
result = await mock_postgres_manager.execute_query("SELECT * FROM users")
assert len(result) == 1
```

### Integration Tests

Test actual connections:

```python
import pytest
from app.infrastructure.connections import ConnectionFactory, ConnectionType

@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_connection():
"""Test actual PostgreSQL connection."""
# Get manager
manager = ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)

try:
# Connect
await manager.connect()
assert manager.is_connected

# Test query
result = await manager.execute_query("SELECT 1")
assert result is not None

# Test health
assert manager.is_healthy()

finally:
# Cleanup
await manager.disconnect()
```

### Test Configuration

Use test-specific configuration:

```yaml
# resources/test-application-db.yaml
db:
postgres:
host: "localhost"
port: 5432
database: "test_db"
username: "test_user"
password: "test_password"
```

---

## API Reference

### ConnectionFactory

```python
from app.infrastructure.connections import ConnectionFactory

# Get connection manager instance
manager = ConnectionFactory.get_connection_manager(connection_type: ConnectionType) -> BaseConnectionManager

# List available connections
connections = ConnectionFactory.list_available_connections() -> List[ConnectionType]

# Check if connection is available
available = ConnectionFactory.is_connection_available(connection_type: ConnectionType) -> bool

# Get status of all connections
status = ConnectionFactory.get_connection_status() -> dict
```

### BaseConnectionManager

```python
# Abstract methods (must implement)
def get_connection_name(self) -> str: pass
def validate_config(self) -> None: pass
def connect(self) -> Any: pass
def disconnect(self) -> None: pass
def is_healthy(self) -> bool: pass

# Provided methods
def ensure_connected(self) -> Any # Auto-connect if needed
def reconnect(self) -> Any # Force reconnection
def get_connection_info(self) -> Dict # Get connection details

# Properties
manager.is_connected -> bool # Connection status
manager.connection -> Any # Connection object
manager.config -> Dict # Configuration dict
```

### AsyncBaseConnectionManager

```python
# Async abstract methods
async def connect(self) -> Any: pass
async def disconnect(self) -> None: pass

# Async provided methods
async def ensure_connected(self) -> Any
async def reconnect(self) -> Any

# Context manager
async with manager as conn:
# Use connection
pass
```

### ConnectionRegistry

```python
from app.infrastructure.connections.base import ConnectionRegistry

# Register connection manager (decorator)
@ConnectionRegistry.register(ConnectionType.CUSTOM)
class CustomConnectionManager(BaseConnectionManager):
pass

# Get manager class
manager_class = ConnectionRegistry.get_connection_manager_class(ConnectionType.CUSTOM)

# Check registration
registered = ConnectionRegistry.is_connection_registered(ConnectionType.CUSTOM) -> bool

# List registered connections
connections = ConnectionRegistry.list_connections() -> List[ConnectionType]

# Get registry info
info = ConnectionRegistry.get_registry_info() -> dict
```

---

## Troubleshooting

### Issue 1: Connection Type Not Registered

**Error**: `KeyError: Connection type 'custom' not registered`

**Cause**: Connection manager not registered or not imported

**Solution**:
1. Ensure decorator is used: `@ConnectionRegistry.register(ConnectionType.CUSTOM)`
2. Import in package `__init__.py`:
```python
# src/app/connections/[category]/__init__.py
from .custom_connection_manager import CustomConnectionManager
```
3. Import category in main `__init__.py`:
```python
# src/app/connections/__init__.py
import app.connections.[category]
```

### Issue 2: Configuration Not Found

**Error**: `ValueError: Connection requires 'host' in configuration`

**Cause**: Configuration file missing or incorrect

**Solution**:
1. Check YAML file exists: `resources/application-[profile].yaml`
2. Verify configuration structure matches expected format
3. Check environment variables are set
4. Verify ConfigSource registration includes your connection type

### Issue 3: Connection Timeout

**Error**: `ConnectionError: Connection timed out`

**Cause**: Service not reachable or wrong configuration

**Solution**:
1. Verify service is running: `telnet localhost <port>`
2. Check firewall rules
3. Verify host/port in configuration
4. Increase timeout in configuration

### Issue 4: Import Errors

**Error**: `ImportError: cannot import name 'ConnectionFactory'`

**Cause**: Circular import or missing import

**Solution**:
```python
# BAD (module level import in connection manager)
from app.infrastructure.connections import ConnectionFactory

# GOOD (local import where needed)
def my_method(self):
from app.infrastructure.connections import ConnectionFactory
factory = ConnectionFactory()
```

### Issue 5: Async/Sync Mismatch

**Error**: `RuntimeError: coroutine not awaited`

**Cause**: Using async manager without await

**Solution**:
```python
# BAD
manager.connect() # For async manager

# GOOD
await manager.connect() # Use await
```

### Issue 6: Connection Pool Exhausted

**Error**: `PoolTimeout: pool is exhausted`

**Cause**: Too many concurrent connections

**Solution**:
1. Increase pool size in configuration
2. Ensure connections are properly closed
3. Use context managers for automatic cleanup
4. Review connection usage patterns

---

## Next Steps

- **[Configuration Guide](../configuration/README.md)** - Configure connection settings
- **[Tools Documentation](../tools/README.md)** - Use connections through tools
- **[LLM Providers Guide](../llm-providers/README.md)** - Integrate with LLMs

---

**Last Updated**: January 10, 2026 
**Version**: 1.0 
**Related**: Connection Management, Database Integration, External Services

---

## Contributing

Want to contribute a new connection manager? We welcome contributions!

### Contribution Guidelines

1. **Follow the architecture** - Use `BaseConnectionManager` or `AsyncBaseConnectionManager`
2. **Add comprehensive tests** - Unit and integration tests required
3. **Document thoroughly** - Add to this guide with examples
4. **Configuration first** - Ensure configuration is well-defined
5. **Error handling** - Provide clear error messages
6. **Logging** - Log important events
7. **Type hints** - Use type hints throughout
8. **Health checks** - Implement meaningful health checking

### Submission Process

1. Create connection manager following [Step-by-Step Guide](#step-by-step-guide)
2. Add unit tests and integration tests
3. Update documentation (this file)
4. Add configuration example
5. Submit pull request with:
- Description of connection type
- Use cases
- Example usage
- Test results

### Community

- **GitHub**: [agenthub-be](https://github.com/timothy-odofin/agenthub-be)
- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Report bugs or request features via GitHub Issues

---

Thank you for using and contributing to AgentHub! 
