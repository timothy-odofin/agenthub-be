# Session Management Layer

> 💬 **Multi-backend session management** for chat conversations with PostgreSQL and MongoDB support, factory pattern for extensibility, and resilience patterns

## Table of Contents

### Overview
- [What is the Session Layer?](#what-is-the-session-layer)
- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)

### Core Components
- [Session Models](#session-models)
  - [ChatSession](#chatsession)
  - [ChatMessage](#chatmessage)
- [Base Repository](#base-repository)
  - [BaseSessionRepository](#basesessionrepository)
  - [Connection Management](#connection-management)

### Repository Implementations
- [MongoDB Session Repository](#mongodb-session-repository)
  - [Features](#mongodb-features)
  - [Usage Examples](#mongodb-usage)
  - [Resilience Patterns](#mongodb-resilience)
- [PostgreSQL Session Repository](#postgresql-session-repository)
  - [Features](#postgres-features)
  - [Database Schema](#postgres-schema)
  - [Usage Examples](#postgres-usage)

### Factory Pattern
- [Session Repository Factory](#session-repository-factory)
  - [Registry Pattern](#registry-pattern)
  - [Creating Repositories](#creating-repositories)
  - [Default Repository](#default-repository)

### Usage Patterns
- [Getting Started](#getting-started)
- [Creating Sessions](#creating-sessions)
- [Managing Messages](#managing-messages)
- [Querying Sessions](#querying-sessions)
- [Integration with Chat Service](#integration-with-chat-service)

### Extending Sessions
- [Creating Custom Repository](#creating-custom-repository)
- [Step-by-Step Guide](#step-by-step-guide)
- [Best Practices](#best-practices)

### Reference
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## What is the Session Layer?

The session layer (`src/app/sessions/`) provides **conversation persistence** for the chat system, enabling:

- **Multi-turn conversations** with full history tracking
- **Multiple backend support** (PostgreSQL, MongoDB)
- **User isolation** - sessions are user-scoped
- **Pagination** for efficient session listing
- **Message ordering** with timestamps

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat Service Layer                        │
│              (Business Logic, Agent Integration)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           SessionRepositoryFactory (Factory Pattern)         │
│         Creates appropriate repository based on type         │
└─────────────────────────┬───────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ MongoDB  │   │PostgreSQL│   │  Redis   │
    │   Repo   │   │   Repo   │   │  (Future)│
    └─────┬────┘   └─────┬────┘   └──────────┘
          │              │
          │              │
          ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│              BaseSessionRepository                           │
│         (Abstract base with connection management)           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              ConnectionFactory                               │
│         (Via existing connection infrastructure)             │
└─────────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ MongoDB  │   │PostgreSQL│   │  Models  │
    │Connection│   │Connection│   │ (Domain) │
    └──────────┘   └──────────┘   └──────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Backend** | PostgreSQL and MongoDB support with unified interface |
| **Factory Pattern** | Easy switching between backends |
| **Registry Pattern** | Decorator-based repository registration |
| **Auto-Connection** | Automatic connection management via ConnectionFactory |
| **User Isolation** | All operations are user-scoped for security |
| **Pagination** | Efficient session listing with skip/limit |
| **Message Ordering** | Chronological message retrieval |
| **Resilience** | Retry patterns for MongoDB operations |
| **Async/Sync Hybrid** | Handles both async and sync contexts |
| **Type Safety** | Full dataclass models for sessions and messages |

---

## Session Models

### ChatSession

**Location**: `src/app/sessions/models/session.py`

Represents a conversation session between a user and the agent.

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChatSession:
    session_id: str          # Unique session identifier (UUID)
    title: str               # Session title (e.g., "New Chat")
    user_id: str             # User who owns this session
    created_at: datetime     # Session creation timestamp
    updated_at: datetime     # Last update timestamp
    metadata: dict[str, any] # Additional session metadata
```

**Usage**:
```python
from src.app.sessions.models.session import ChatSession
from datetime import datetime

session = ChatSession(
    session_id="550e8400-e29b-41d4-a716-446655440000",
    title="Product Discussion",
    user_id="user123",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    metadata={"topic": "pricing", "priority": "high"}
)
```

---

### ChatMessage

**Location**: `src/app/sessions/models/message.py`

Represents a single message in a conversation.

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChatMessage:
    message_id: str   # Unique message identifier (UUID)
    session_id: str   # Session this message belongs to
    role: str         # "user" or "assistant"
    content: str      # Message content
    timestamp: datetime  # When message was sent
```

**Usage**:
```python
from src.app.sessions.models.message import ChatMessage
from datetime import datetime

# User message
user_msg = ChatMessage(
    message_id="msg-001",
    session_id="session-123",
    role="user",
    content="What are your pricing plans?",
    timestamp=datetime.utcnow()
)

# Assistant response
assistant_msg = ChatMessage(
    message_id="msg-002",
    session_id="session-123",
    role="assistant",
    content="We offer three pricing tiers...",
    timestamp=datetime.utcnow()
)
```

---

## Base Repository

### BaseSessionRepository

**Location**: `src/app/sessions/repositories/base_session_repository.py`

Abstract base class defining the session repository interface.

#### Key Features

1. **Centralized Connection Management** via ConnectionFactory
2. **Smart Async/Sync Detection** - handles both patterns
3. **Template Method Pattern** - child classes implement specifics
4. **Automatic Table Creation** on first connection

#### Architecture

```python
from abc import ABC, abstractmethod

class BaseSessionRepository(ABC):
    """Base class for session repositories."""
    
    def __init__(self, connection_type: ConnectionType):
        """Initialize with connection type (MONGODB or POSTGRES)."""
        self.connection_type = connection_type
        self._connection_manager = None
        self._connection = None
        self.load_and_validate_connection()
    
    async def _ensure_connection(self):
        """Ensure connection is established and tables exist."""
        pass
    
    # Abstract methods that implementations must provide
    @abstractmethod
    def create_session(self, user_id: str, session_data: dict) -> str:
        pass
    
    @abstractmethod
    async def get_session_history(
        self, 
        user_id: str, 
        session_id: str
    ) -> List[ChatMessage]:
        pass
    
    @abstractmethod
    def update_session(
        self, 
        user_id: str, 
        session_id: str, 
        data: dict
    ) -> bool:
        pass
    
    @abstractmethod
    def list_paginated_sessions(
        self, 
        user_id: str, 
        page: int = 0, 
        limit: int = 10
    ) -> List[ChatSession]:
        pass
    
    @abstractmethod
    def delete_session(
        self, 
        user_id: str, 
        session_id: str
    ) -> bool:
        pass
    
    @abstractmethod
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str
    ) -> str:
        pass
```

### Connection Management

The base repository automatically manages connections via ConnectionFactory:

```python
def load_and_validate_connection(self):
    """Load connection manager from factory."""
    self._connection_manager = ConnectionFactory.get_connection_manager(
        self.connection_type
    )

async def _ensure_connection(self):
    """Establish connection and create tables/collections."""
    if self._connection is None:
        # Auto-detect async vs sync connection manager
        if isinstance(self._connection_manager, AsyncBaseConnectionManager):
            self._connection = await self._connection_manager.connect()
        else:
            self._connection = self._connection_manager.connect()
        
        # Auto-detect async vs sync table creation
        if inspect.iscoroutinefunction(self._create_tables_if_not_exist):
            await self._create_tables_if_not_exist()
        else:
            self._create_tables_if_not_exist()
```

---

## MongoDB Session Repository

**Location**: `src/app/sessions/repositories/mongo_session_repository.py`

**Registry**: `@register_repository(SessionRepositoryType.MONGODB)`

### MongoDB Features

| Feature | Description |
|---------|-------------|
| **Document Storage** | Natural fit for session/message data |
| **Flexible Schema** | Easy metadata extension |
| **Thread Pool Pattern** | Sync PyMongo operations in thread pool for async context |
| **Resilience Patterns** | Retry logic with exponential backoff |
| **Indexes** | Optimized for user_id and session_id queries |
| **Cascade Delete** | Messages auto-deleted with session |

### MongoDB Database Structure

**Collections**:
- `chat_sessions` - Session metadata
- `chat_messages` - Message history

**Indexes**:
```python
# chat_sessions collection
- user_id (non-unique)
- session_id (unique)

# chat_messages collection
- session_id (non-unique)
- (session_id, timestamp) compound index (for ordered retrieval)
```

### MongoDB Resilience

Retry configuration with exponential backoff:

```python
MONGODB_RETRY_CONFIG = RetryConfig(
    max_attempts=3,           # Retry up to 3 times
    base_delay=0.5,           # Start with 500ms delay
    max_delay=5.0,            # Max 5 second delay
    strategy=RetryStrategy.EXPONENTIAL,  # Exponential backoff
    jitter=True               # Add randomness to prevent thundering herd
)

@async_retry(MONGODB_RETRY_CONFIG)
async def get_session_history(self, user_id: str, session_id: str):
    # Automatically retried on failure
    pass
```

### MongoDB Usage

```python
from app.sessions.repositories.session_repository_factory import (
    SessionRepositoryFactory, 
    SessionRepositoryType
)

# Create MongoDB repository
repo = SessionRepositoryFactory.create_repository(SessionRepositoryType.MONGODB)

# Create session
session_id = repo.create_session(
    user_id="user123",
    session_data={
        "title": "Product Questions",
        "metadata": {"source": "web"}
    }
)

# Async: Create session (in async context)
session_id = await repo.create_session_async(
    user_id="user123",
    session_data={"title": "New Chat"}
)

# Ensure session exists (idempotent)
created = await repo.ensure_session_exists(
    session_id="existing-session-id",
    user_id="user123",
    session_data={"title": "Restored Session"}
)

# Add messages
message_id = await repo.add_message(
    session_id=session_id,
    role="user",
    content="What is your pricing?"
)

# Get session history
messages = await repo.get_session_history(
    user_id="user123",
    session_id=session_id
)

# List sessions with pagination
sessions = repo.list_paginated_sessions(
    user_id="user123",
    page=0,
    limit=10
)

# Update session
success = repo.update_session(
    user_id="user123",
    session_id=session_id,
    data={"title": "Updated Title"}
)

# Delete session (and all messages)
success = repo.delete_session(
    user_id="user123",
    session_id=session_id
)
```

#### Thread Pool Pattern

MongoDB repository uses thread pools to run sync PyMongo operations in async contexts:

```python
async def get_session_history(self, user_id: str, session_id: str):
    await self._ensure_connection()
    
    # Define sync operation
    def get_session_and_messages():
        # Sync PyMongo operations
        session = self._sessions_collection.find_one(...)
        messages = self._messages_collection.find(...)
        return messages
    
    # Run in thread pool
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await asyncio.get_event_loop().run_in_executor(
            executor, 
            get_session_and_messages
        )
```

---

## PostgreSQL Session Repository

**Location**: `src/app/sessions/repositories/postgres_session_repository.py`

**Registry**: `@register_repository(SessionRepositoryType.POSTGRES)`

### Postgres Features

| Feature | Description |
|---------|-------------|
| **Relational Model** | Foreign key constraints for referential integrity |
| **ACID Transactions** | Guaranteed consistency |
| **Native Async** | Uses asyncpg for true async operations |
| **Cascade Delete** | SQL ON DELETE CASCADE for messages |
| **JSON Support** | JSONB for flexible metadata |
| **Indexes** | Optimized for user_id and session_id queries |

### Postgres Schema

```sql
-- Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Messages table with foreign key
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages(session_id);
```

**Key Features**:
- ✅ **UUID Primary Keys** - Globally unique identifiers
- ✅ **Foreign Key Constraint** - Messages reference sessions
- ✅ **Cascade Delete** - Deleting session deletes messages
- ✅ **Check Constraint** - Role must be 'user' or 'assistant'
- ✅ **JSONB Metadata** - Flexible schema for session metadata
- ✅ **Indexes** - Fast lookups by user_id and session_id

### Postgres Usage

```python
from app.sessions.repositories.session_repository_factory import (
    SessionRepositoryFactory, 
    SessionRepositoryType
)

# Create PostgreSQL repository
repo = SessionRepositoryFactory.create_repository(SessionRepositoryType.POSTGRES)

# Create session (sync wrapper)
session_id = repo.create_session(
    user_id="user123",
    session_data={
        "title": "Support Ticket",
        "metadata": {"priority": "high"}
    }
)

# Add message
message_id = await repo.add_message(
    session_id=session_id,
    role="user",
    content="I need help with billing"
)

# Get session history
messages = await repo.get_session_history(
    user_id="user123",
    session_id=session_id
)

# List sessions
sessions = repo.list_paginated_sessions(
    user_id="user123",
    page=0,
    limit=20
)

# Update session
success = repo.update_session(
    user_id="user123",
    session_id=session_id,
    data={"title": "Billing Issue - Resolved"}
)

# Delete session (cascade deletes messages)
success = repo.delete_session(
    user_id="user123",
    session_id=session_id
)
```

---

## Session Repository Factory

**Location**: `src/app/sessions/repositories/session_repository_factory.py`

Factory pattern for creating session repositories with decorator-based registration.

### Registry Pattern

Repositories self-register using decorators:

```python
from app.sessions.repositories.session_repository_factory import (
    register_repository,
    SessionRepositoryType
)

@register_repository(SessionRepositoryType.MONGODB)
class MongoSessionRepository(BaseSessionRepository):
    # Implementation
    pass

@register_repository(SessionRepositoryType.POSTGRES)
class PostgresSessionRepository(BaseSessionRepository):
    # Implementation
    pass
```

### Creating Repositories

```python
from app.sessions.repositories.session_repository_factory import (
    SessionRepositoryFactory,
    SessionRepositoryType
)

# Create MongoDB repository
mongo_repo = SessionRepositoryFactory.create_repository(
    SessionRepositoryType.MONGODB
)

# Create PostgreSQL repository
postgres_repo = SessionRepositoryFactory.create_repository(
    SessionRepositoryType.POSTGRES
)

# List available repository types
available = SessionRepositoryFactory.list_repositories()
# Returns: [SessionRepositoryType.MONGODB, SessionRepositoryType.POSTGRES]
```

### Default Repository

```python
from app.sessions.repositories.session_repository_factory import SessionRepositoryFactory

# Get default repository (currently MongoDB)
repo = SessionRepositoryFactory.get_default_repository()
```

**Configuration Note**: Default repository is set to MongoDB. To change:

```python
# In session_repository_factory.py
@staticmethod
def get_default_repository() -> BaseSessionRepository:
    return SessionRepositoryFactory.create_repository(
        SessionRepositoryType.POSTGRES  # Change to PostgreSQL
    )
```

---

## Getting Started

### Basic Session Flow

```python
from app.sessions.repositories.session_repository_factory import SessionRepositoryFactory
import uuid

# 1. Get repository
repo = SessionRepositoryFactory.get_default_repository()

# 2. Create session
session_id = repo.create_session(
    user_id="user123",
    session_data={"title": "New Chat"}
)

# 3. Add user message
await repo.add_message(
    session_id=session_id,
    role="user",
    content="Hello, I need help"
)

# 4. Add assistant response
await repo.add_message(
    session_id=session_id,
    role="assistant",
    content="I'm here to help! What do you need assistance with?"
)

# 5. Get conversation history
messages = await repo.get_session_history(
    user_id="user123",
    session_id=session_id
)

for msg in messages:
    print(f"{msg.role}: {msg.content}")
```

---

## Creating Sessions

### Simple Session Creation

```python
# Minimal session
session_id = repo.create_session(
    user_id="user123",
    session_data={"title": "New Chat"}
)

# With metadata
session_id = repo.create_session(
    user_id="user123",
    session_data={
        "title": "Product Support",
        "metadata": {
            "source": "web",
            "category": "billing",
            "priority": "high",
            "tags": ["urgent", "payment"]
        }
    }
)
```

### Async Session Creation (MongoDB)

```python
# In async context
session_id = await repo.create_session_async(
    user_id="user123",
    session_data={"title": "Async Chat"}
)

# Idempotent creation (MongoDB only)
created = await repo.ensure_session_exists(
    session_id="predetermined-session-id",
    user_id="user123",
    session_data={"title": "Restored Chat"}
)
# Returns: True if created, False if already existed
```

---

## Managing Messages

### Adding Messages

```python
# Add user message
user_msg_id = await repo.add_message(
    session_id=session_id,
    role="user",
    content="What are your pricing plans?"
)

# Add assistant message
assistant_msg_id = await repo.add_message(
    session_id=session_id,
    role="assistant",
    content="We offer three tiers: Basic ($10/mo), Pro ($25/mo), Enterprise (custom)"
)
```

### Retrieving Message History

```python
# Get all messages for session
messages = await repo.get_session_history(
    user_id="user123",
    session_id=session_id
)

# Messages are ordered by timestamp (oldest first)
for msg in messages:
    print(f"[{msg.timestamp}] {msg.role}: {msg.content}")
```

### Message Format

```python
# Each message is a ChatMessage dataclass
message = messages[0]

print(message.message_id)   # "550e8400-..."
print(message.session_id)   # "7c9e6679-..."
print(message.role)         # "user" or "assistant"
print(message.content)      # Message text
print(message.timestamp)    # datetime object
```

---

## Querying Sessions

### List User Sessions

```python
# Get first page (10 sessions)
sessions = repo.list_paginated_sessions(
    user_id="user123",
    page=0,
    limit=10
)

# Get second page
sessions_page2 = repo.list_paginated_sessions(
    user_id="user123",
    page=1,
    limit=10
)

# Custom page size
sessions = repo.list_paginated_sessions(
    user_id="user123",
    page=0,
    limit=50  # Get 50 sessions
)
```

### Session List Format

```python
# Sessions are ordered by updated_at (newest first)
for session in sessions:
    print(f"Session: {session.title}")
    print(f"  ID: {session.session_id}")
    print(f"  Created: {session.created_at}")
    print(f"  Updated: {session.updated_at}")
    print(f"  Metadata: {session.metadata}")
```

### Update Session

```python
# Update title
success = repo.update_session(
    user_id="user123",
    session_id=session_id,
    data={"title": "Updated Title"}
)

# Update metadata
success = repo.update_session(
    user_id="user123",
    session_id=session_id,
    data={
        "metadata": {
            "status": "resolved",
            "resolution_time": "5 minutes"
        }
    }
)

# Update both
success = repo.update_session(
    user_id="user123",
    session_id=session_id,
    data={
        "title": "Issue Resolved",
        "metadata": {"status": "closed"}
    }
)
```

### Delete Session

```python
# Delete session (and all messages)
success = repo.delete_session(
    user_id="user123",
    session_id=session_id
)

if success:
    print("Session deleted successfully")
else:
    print("Session not found or already deleted")
```

---

## Integration with Chat Service

**Location**: `src/app/services/chat_service.py`

The chat service uses sessions for conversation persistence:

```python
class ChatService:
    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        protocol: str = "rest"
    ) -> Dict[str, Any]:
        # Auto-generate session if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Get session repository
        session_repo = SessionRepositoryFactory.get_default_repository()
        
        # Create agent with session support
        agent = await AgentFactory.create_agent(
            agent_type=self._agent_type,
            framework=self._agent_framework,
            llm_provider=llm,
            session_repository=session_repo,  # Pass repository to agent
            verbose=self.agent_verbose
        )
        
        # Execute with context
        context = AgentContext(
            user_id=user_id,
            session_id=session_id,
            metadata={"protocol": protocol}
        )
        
        response = await agent.execute(message, context)
        return response
```

---

## Creating Custom Repository

Want to add support for a new database backend (e.g., Redis, Cassandra)?

### Step-by-Step Guide

#### 1. Add Repository Type

```python
# In session_repository_factory.py
class SessionRepositoryType(str, Enum):
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    REDIS = "redis"  # Add new type
```

#### 2. Create Repository Class

```python
# src/app/sessions/repositories/redis_session_repository.py
from app.sessions.repositories.base_session_repository import BaseSessionRepository
from app.sessions.repositories.session_repository_factory import (
    register_repository,
    SessionRepositoryType
)
from app.connections.base import ConnectionType

@register_repository(SessionRepositoryType.REDIS)
class RedisSessionRepository(BaseSessionRepository):
    """Redis implementation using sorted sets for message ordering."""
    
    def __init__(self):
        super().__init__(ConnectionType.REDIS)
    
    def _create_tables_if_not_exist(self):
        """No table creation needed for Redis."""
        pass
    
    def create_session(self, user_id: str, session_data: dict) -> str:
        """Create session in Redis."""
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store session metadata as hash
        session_key = f"session:{session_id}"
        self._connection.hset(session_key, mapping={
            "session_id": session_id,
            "user_id": user_id,
            "title": session_data.get("title", "New Chat"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": json.dumps(session_data.get("metadata", {}))
        })
        
        # Add to user's session list
        user_sessions_key = f"user:{user_id}:sessions"
        self._connection.zadd(
            user_sessions_key,
            {session_id: datetime.utcnow().timestamp()}
        )
        
        return session_id
    
    async def get_session_history(
        self, 
        user_id: str, 
        session_id: str
    ) -> List[ChatMessage]:
        """Get message history from Redis sorted set."""
        # Verify session ownership
        session_key = f"session:{session_id}"
        session_user = self._connection.hget(session_key, "user_id")
        
        if session_user != user_id:
            return []
        
        # Get messages from sorted set (ordered by timestamp)
        messages_key = f"session:{session_id}:messages"
        messages_data = self._connection.zrange(messages_key, 0, -1)
        
        messages = []
        for msg_json in messages_data:
            msg_dict = json.loads(msg_json)
            messages.append(ChatMessage(
                message_id=msg_dict["message_id"],
                session_id=msg_dict["session_id"],
                role=msg_dict["role"],
                content=msg_dict["content"],
                timestamp=datetime.fromisoformat(msg_dict["timestamp"])
            ))
        
        return messages
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str
    ) -> str:
        """Add message to Redis sorted set."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        message_data = {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": timestamp.isoformat()
        }
        
        # Add to sorted set with timestamp as score
        messages_key = f"session:{session_id}:messages"
        self._connection.zadd(
            messages_key,
            {json.dumps(message_data): timestamp.timestamp()}
        )
        
        return message_id
    
    # Implement other abstract methods...
```

#### 3. Register in Package

```python
# src/app/sessions/repositories/__init__.py
from .mongo_session_repository import MongoSessionRepository
from .postgres_session_repository import PostgresSessionRepository
from .redis_session_repository import RedisSessionRepository  # Add this

__all__ = [
    'MongoSessionRepository',
    'PostgresSessionRepository',
    'RedisSessionRepository'  # Add this
]
```

#### 4. Use Custom Repository

```python
from app.sessions.repositories.session_repository_factory import (
    SessionRepositoryFactory,
    SessionRepositoryType
)

# Create Redis repository
redis_repo = SessionRepositoryFactory.create_repository(
    SessionRepositoryType.REDIS
)

# Use same interface
session_id = redis_repo.create_session(
    user_id="user123",
    session_data={"title": "Redis Chat"}
)
```

---

## Best Practices

### 1. Use Factory for Repository Creation

```python
# ✅ GOOD - Use factory
repo = SessionRepositoryFactory.get_default_repository()

# ❌ BAD - Direct instantiation
from app.sessions.repositories.mongo_session_repository import MongoSessionRepository
repo = MongoSessionRepository()
```

### 2. Always Scope by User ID

```python
# ✅ GOOD - User-scoped operations
messages = await repo.get_session_history(
    user_id="user123",
    session_id=session_id
)

# ❌ BAD - No user validation (security risk)
messages = await repo.get_messages(session_id)  # Don't do this
```

### 3. Handle Session Creation Carefully

```python
# ✅ GOOD - Auto-generate if not provided
session_id = session_id or str(uuid.uuid4())

# ✅ GOOD - Use idempotent creation (MongoDB)
created = await repo.ensure_session_exists(
    session_id=session_id,
    user_id=user_id
)

# ❌ BAD - Assume session always exists
messages = await repo.get_session_history(user_id, session_id)
# Should check if session exists first
```

### 4. Use Pagination for Session Lists

```python
# ✅ GOOD - Paginated
sessions = repo.list_paginated_sessions(
    user_id="user123",
    page=0,
    limit=20
)

# ❌ BAD - Fetch all sessions (memory issues for active users)
# Don't do: sessions = repo.get_all_sessions(user_id)
```

### 5. Clean Up Old Sessions

```python
# ✅ GOOD - Implement session cleanup
async def cleanup_old_sessions(user_id: str, keep_last_n: int = 50):
    """Keep only last N sessions for user."""
    sessions = repo.list_paginated_sessions(user_id, page=0, limit=1000)
    
    # Delete sessions beyond keep_last_n
    for session in sessions[keep_last_n:]:
        repo.delete_session(user_id, session.session_id)
```

### 6. Add Meaningful Metadata

```python
# ✅ GOOD - Rich metadata
session_data = {
    "title": "Billing Support",
    "metadata": {
        "source": "web",
        "category": "billing",
        "priority": "high",
        "agent_version": "1.0",
        "resolved": False
    }
}

# ❌ BAD - No metadata
session_data = {"title": "New Chat"}
```

---

## API Reference

### BaseSessionRepository

```python
class BaseSessionRepository(ABC):
    def __init__(self, connection_type: ConnectionType)
    
    # Core operations
    def create_session(user_id: str, session_data: dict) -> str
    async def get_session_history(user_id: str, session_id: str) -> List[ChatMessage]
    def update_session(user_id: str, session_id: str, data: dict) -> bool
    def list_paginated_sessions(user_id: str, page: int, limit: int) -> List[ChatSession]
    def delete_session(user_id: str, session_id: str) -> bool
    async def add_message(session_id: str, role: str, content: str) -> str
    
    # Connection management
    async def _ensure_connection()
    def load_and_validate_connection()
    
    # Template method
    @abstractmethod
    def _create_tables_if_not_exist()
```

### MongoSessionRepository

```python
class MongoSessionRepository(BaseSessionRepository):
    # Additional async methods
    async def create_session_async(user_id: str, session_data: dict) -> str
    async def ensure_session_exists(session_id: str, user_id: str, session_data: dict) -> bool
    
    # Resilience (all async methods have retry)
    MONGODB_RETRY_CONFIG = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter=True
    )
```

### SessionRepositoryFactory

```python
class SessionRepositoryFactory:
    @staticmethod
    def create_repository(repo_type: SessionRepositoryType) -> BaseSessionRepository
    
    @staticmethod
    def get_default_repository() -> BaseSessionRepository
    
    @staticmethod
    def list_repositories() -> List[SessionRepositoryType]
```

### SessionRepositoryRegistry

```python
class SessionRepositoryRegistry:
    @classmethod
    def register_repository(cls, repo_type: SessionRepositoryType)
    
    @classmethod
    def get_repository_class(cls, repo_type: SessionRepositoryType) -> Type[BaseSessionRepository]
    
    @classmethod
    def list_repositories(cls) -> List[SessionRepositoryType]
```

---

## Configuration

### MongoDB Configuration

```yaml
# resources/application-db.yaml
db:
  mongodb:
    host: "${MONGODB_HOST:localhost}"
    port: "${MONGODB_PORT:27017}"
    database: "${MONGODB_DB:agenthub}"
    username: "${MONGODB_USER:}"
    password: "${MONGODB_PASSWORD:}"
```

### PostgreSQL Configuration

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

### Changing Default Repository

```python
# In session_repository_factory.py
@staticmethod
def get_default_repository() -> BaseSessionRepository:
    # Change from MONGODB to POSTGRES
    return SessionRepositoryFactory.create_repository(
        SessionRepositoryType.POSTGRES
    )
```

---

## Troubleshooting

### Issue 1: Connection Not Established

**Error**: `AttributeError: 'NoneType' object has no attribute '...'`

**Cause**: Repository not connected

**Solution**:
```python
# Ensure connection before operations
await repo._ensure_connection()

# Or use methods that call _ensure_connection internally
messages = await repo.get_session_history(user_id, session_id)
```

### Issue 2: Session Not Found

**Error**: Empty list returned from `get_session_history`

**Cause**: Session doesn't exist or wrong user_id

**Solution**:
```python
# Check session ownership
sessions = repo.list_paginated_sessions(user_id, page=0, limit=100)
session_exists = any(s.session_id == session_id for s in sessions)

if not session_exists:
    # Create session first
    repo.create_session(user_id, {"title": "New Chat"})
```

### Issue 3: Async/Sync Mismatch

**Error**: `RuntimeError: coroutine not awaited`

**Cause**: Calling async method without await

**Solution**:
```python
# ❌ BAD
messages = repo.get_session_history(user_id, session_id)

# ✅ GOOD
messages = await repo.get_session_history(user_id, session_id)
```

### Issue 4: MongoDB Thread Pool Issues

**Error**: Event loop issues in async context

**Cause**: MongoDB uses sync driver with thread pools

**Solution**:
```python
# Use async methods when available
session_id = await repo.create_session_async(user_id, session_data)

# Or let the repository handle the context detection
session_id = repo.create_session(user_id, session_data)  # Auto-detects context
```

### Issue 5: Foreign Key Constraint (PostgreSQL)

**Error**: `ForeignKeyViolation: insert or update on table "chat_messages"`

**Cause**: Trying to add message to non-existent session

**Solution**:
```python
# Create session first
session_id = repo.create_session(user_id, session_data)

# Then add messages
await repo.add_message(session_id, "user", "Hello")
```

---

## Related Documentation

- **[Connection Management](../connections/README.md)** - Database connections
- **[Database Layer](../database/README.md)** - Repository pattern and models
- **[Configuration Guide](../configuration/README.md)** - Configuration setup

---

**Last Updated**: January 10, 2026  
**Version**: 1.0  
**Related**: Session Management, Chat History, Conversation Persistence

---

## Contributing

Want to contribute a new session repository backend?

### Areas for Contribution

1. **Redis Repository** - High-performance session storage
2. **Cassandra Repository** - Distributed session storage
3. **DynamoDB Repository** - AWS-native session storage
4. **Cache Layer** - Add caching to existing repositories
5. **Session Analytics** - Add metrics and monitoring

### Submission Process

1. Follow the [Creating Custom Repository](#creating-custom-repository) guide
2. Add comprehensive tests
3. Update this documentation
4. Submit pull request with clear description

---

Thank you for using AgentHub's session management system! 💬
