# Database Layer Architecture

> **Multi-database architecture** with MongoDB for document storage, Redis for sessions/caching, PostgreSQL for relational data, and vector databases for embeddings

## Table of Contents

### Overview
- [What is the Database Layer?](#what-is-the-database-layer)
- [Architecture Overview](#architecture-overview)
- [Key Components](#key-components)

### Database Systems
- [MongoDB - Document Storage](#mongodb---document-storage)
  - [User Repository](#user-repository)
  - [Models](#models)
- [Redis - Session & Cache](#redis---session--cache)
  - [Signup Session Repository](#signup-session-repository)
- [Vector Databases](#vector-databases)
  - [Base Architecture](#base-architecture)
  - [Qdrant Implementation](#qdrant-implementation)
  - [PgVector Implementation](#pgvector-implementation)
  - [ChromaDB Implementation](#chromadb-implementation)
- [Embedding System](#embedding-system)
  - [Embedding Factory](#embedding-factory)
  - [Supported Providers](#supported-providers)

### Repository Pattern
- [Repository Design](#repository-design)
- [Creating Custom Repositories](#creating-custom-repositories)
- [Best Practices](#best-practices)

### Reference
- [API Reference](#api-reference)
- [Future Improvements](#future-improvements)

---

## What is the Database Layer?

The database layer (`src/app/db/`) provides a **unified data access layer** for the application using the **Repository Pattern**. It abstracts database operations and provides clean, testable interfaces for data persistence.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│              (Services, API Endpoints)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                           │
│         (UserRepository, SessionRepository, etc.)            │
└─────────────────────────┬───────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┬──────────────┐
           ▼              ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ MongoDB  │   │  Redis   │   │  Vector  │   │ Models   │
    │  Repos   │   │  Repos   │   │  Stores  │   │(Pydantic)│
    └─────┬────┘   └─────┬────┘   └─────┬────┘   └──────────┘
          │              │              │
          │              │              ▼
          │              │    ┌──────────────────┐
          │              │    │ Vector Providers │
          │              │    │  (Registry)      │
          │              │    └─────┬────────────┘
          │              │          │
          │              │          ├── Qdrant
          │              │          ├── PgVector
          │              │          └── ChromaDB
          │              │
          │              ▼
          │    ┌──────────────────┐
          │    │ Embedding System │
          │    │    (Factory)     │
          │    └─────┬────────────┘
          │          │
          │          ├── OpenAI
          │          ├── HuggingFace
          │          ├── Instructor
          │          └── Cohere
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│              Connection Management Layer                     │
│         (Via ConnectionFactory - see connections docs)       │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Models** | Data validation and structure | Pydantic (BaseModel) |
| **Repositories** | Data access abstraction | Repository Pattern |
| **Vector Stores** | Embedding storage and retrieval | Qdrant, PgVector, ChromaDB |
| **Embeddings** | Text-to-vector conversion | OpenAI, HuggingFace, etc. |
| **Connections** | Database connection management | ConnectionFactory |

---

## MongoDB - Document Storage

MongoDB is used for **user data** and **document storage** with flexible schemas.

### User Repository

**Location**: `src/app/db/repositories/user_repository.py`

**Purpose**: CRUD operations for user authentication and management

**Key Features**:
- Automatic connection management via ConnectionFactory
- Unique indexes on email and username
- Field normalization (lowercase emails/usernames)
- Singleton-ready pattern
- Comprehensive error handling

#### Usage

```python
from src.app.db.repositories.user_repository import UserRepository
from src.app.db.models.user import User, UserInDB

# Initialize repository (auto-connects to MongoDB)
repo = UserRepository()

# Create a user
user = await repo.create_user(
    email="john@example.com",
    username="johndoe",
    firstname="John",
    lastname="Doe",
    password_hash="$2b$12$..."  # bcrypt hash
)

# Get user by email
user = await repo.get_user_by_email("john@example.com")

# Get user by username
user = await repo.get_user_by_username("johndoe")

# Get user by ID
user = await repo.get_user_by_id("507f1f77bcf86cd799439011")

# Update user
success = await repo.update_user(
    user_id="507f1f77bcf86cd799439011",
    update_data={"firstname": "Jonathan"}
)

# Check for duplicates
email_exists = await repo.check_email_exists("john@example.com")
username_exists = await repo.check_username_exists("johndoe")
```

#### API Reference

```python
class UserRepository:
    """Repository for User model operations in MongoDB."""
    
    # Collection name
    COLLECTION_NAME = "users"
    
    # Constructor
    def __init__(self, db: Optional[Database] = None)
    
    # CRUD operations
    async def create_user(
        self,
        email: str,
        username: str,
        firstname: str,
        lastname: str,
        password_hash: str
    ) -> Optional[UserInDB]
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]
    
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]
    
    async def update_user(
        self,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> bool
    
    # Duplicate checking
    async def check_email_exists(self, email: str) -> bool
    
    async def check_username_exists(self, username: str) -> bool
```

#### Database Schema

**Collection**: `users`

**Indexes**:
- `email` (unique)
- `username` (unique)

**Document Structure**:
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "john@example.com",
  "username": "johndoe",
  "firstname": "John",
  "lastname": "Doe",
  "password_hash": "$2b$12$...",
  "created_at": "2026-01-10T12:00:00Z",
  "updated_at": "2026-01-10T12:00:00Z",
  "is_active": true
}
```

---

### Models

**Location**: `src/app/db/models/user.py`

#### User Model

Base user model with validation:

```python
from src.app.db.models.user import User

user = User(
    email="john@example.com",
    username="johndoe",
    firstname="John",
    lastname="Doe",
    password_hash="$2b$12$..."
)
```

**Validation Rules**:
- **Email**: Must be valid email format (uses Pydantic EmailStr)
- **Username**: 
  - 3-30 characters
  - Alphanumeric + underscores
  - Must start with letter
  - Stored in lowercase
- **Firstname/Lastname**:
  - 2-50 characters
  - Letters, spaces, hyphens, apostrophes only
  - Capitalized on storage
- **Password Hash**: Bcrypt hash format

#### UserInDB Model

Extended model with MongoDB ID:

```python
from src.app.db.models.user import UserInDB

user = UserInDB(
    _id="507f1f77bcf86cd799439011",  # MongoDB ObjectId as string
    email="john@example.com",
    username="johndoe",
    firstname="John",
    lastname="Doe",
    password_hash="$2b$12$...",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    is_active=True
)
```

**Additional Fields**:
- `_id`: MongoDB document ID (string)

**Model Features**:
```python
# Exclude password_hash from dict
user_dict = user.to_dict()  # No password_hash

# Exclude password_hash from JSON
user_json = user.to_json()  # No password_hash

# Get safe dict (without password)
safe_dict = user.to_safe_dict()
```

---

## Redis - Session & Cache

Redis is used for **temporary session storage** and **caching** with automatic TTL expiration.

### Signup Session Repository

**Location**: `src/app/db/repositories/signup_session_repository.py`

**Purpose**: Server-side state management for conversational signup flow

**Key Features**:
- Server-side state (prevents client tampering)
- Automatic expiration (5 minute TTL)
- Password hashing on storage
- Validation tracking
- Uses existing RedisConnectionManager

#### Session Data Structure

```json
{
  "session_id": "uuid-123",
  "email": "john@example.com",
  "username": "johndoe",
  "password_hash": "$2b$12$...",
  "firstname": "John",
  "lastname": "Doe",
  "current_step": "LASTNAME",
  "created_at": 1704638400.0,
  "last_updated": 1704638400.0,
  "attempt_count": 1
}
```

#### Usage

```python
from src.app.db.repositories.signup_session_repository import SignupSessionRepository
import uuid

# Initialize repository
repo = SignupSessionRepository()

# Create session
session_id = str(uuid.uuid4())
await repo.create_session(
    session_id=session_id,
    initial_data={"current_step": "EMAIL"}
)

# Get session
session_data = await repo.get_session(session_id)

# Update session
await repo.update_session(
    session_id=session_id,
    update_data={
        "email": "john@example.com",
        "current_step": "USERNAME"
    }
)

# Update specific field
await repo.update_field(
    session_id=session_id,
    field="username",
    value="johndoe"
)

# Increment attempt counter
await repo.increment_attempt(session_id)

# Delete session (cleanup)
await repo.delete_session(session_id)

# Check if session exists
exists = await repo.session_exists(session_id)
```

#### API Reference

```python
class SignupSessionRepository:
    """Repository for managing temporary signup sessions in Redis."""
    
    # Configuration
    KEY_PREFIX = "signup"
    SESSION_TTL = 300  # 5 minutes
    
    # Constructor
    def __init__(self)
    
    # Session operations
    async def create_session(
        self, 
        session_id: str, 
        initial_data: Optional[Dict[str, Any]] = None
    ) -> bool
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]
    
    async def update_session(
        self, 
        session_id: str, 
        update_data: Dict[str, Any]
    ) -> bool
    
    async def update_field(
        self, 
        session_id: str, 
        field: str, 
        value: Any
    ) -> bool
    
    async def delete_session(self, session_id: str) -> bool
    
    async def session_exists(self, session_id: str) -> bool
    
    async def increment_attempt(self, session_id: str) -> int
    
    async def refresh_ttl(self, session_id: str) -> bool
```

#### Redis Key Format

```
signup:{session_id}
```

**Examples**:
- `signup:550e8400-e29b-41d4-a716-446655440000`
- `signup:7c9e6679-7425-40de-944b-e07fc1f90ae7`

---

## Vector Databases

Vector databases store **embeddings** for semantic search and similarity matching.

### Base Architecture

**Location**: `src/app/db/vector/base.py`

All vector databases extend the abstract `VectorDB` base class.

#### VectorDB Base Class

```python
from abc import ABC, abstractmethod

class VectorDB(ABC):
    """Abstract base class for vector database implementations."""
    
    @abstractmethod
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get configuration for this vector database."""
        pass
    
    @abstractmethod
    async def _create_connection(self):
        """Create connection to vector database."""
        pass
    
    @abstractmethod
    async def save_and_embed(
        self, 
        embedding_type: EmbeddingType, 
        docs: List[Document]
    ) -> List[str]:
        """Save documents and generate embeddings."""
        pass
    
    @abstractmethod
    async def update_document(
        self, 
        document_id: str, 
        updated_doc: Document, 
        embedding_type: EmbeddingType
    ) -> bool:
        """Update an existing document."""
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: str) -> bool:
        """Delete document by ID."""
        pass
    
    @abstractmethod
    async def get_document_metadata(
        self, 
        document_id: str
    ) -> Optional[DocumentMetadata]:
        """Get document metadata."""
        pass
```

#### DocumentMetadata

Metadata tracking for documents:

```python
@dataclass
class DocumentMetadata:
    """Metadata for tracking documents in vector store."""
    
    document_id: str
    source_path: str
    file_type: str
    embedded_at: datetime
    custom_metadata: Dict[str, Any]
    
    @classmethod
    def create_hash(cls, content: str) -> str:
        """Create SHA-256 hash for change detection."""
        pass
    
    @classmethod
    def get_change_detection_info(cls, source_path: str) -> Dict[str, Any]:
        """Get file metadata for change detection (fast)."""
        pass
    
    @classmethod
    def generate_document_id(cls, source_path: str) -> str:
        """Generate deterministic document ID."""
        pass
```

---

### Qdrant Implementation

**Location**: `src/app/db/vector/qdrant.py`

**Registry**: `@VectorDBRegistry.register(VectorDBType.QDRANT)`

#### Usage

```python
from src.app.db.vector.providers.db_provider import VectorStoreFactory
from src.app.core.constants import VectorDBType, EmbeddingType
from langchain.schema import Document

# Get Qdrant vector store
vector_store = VectorStoreFactory.get_vector_store(VectorDBType.QDRANT)

# Create connection
vector_store._create_connection()

# Save and embed documents
docs = [
    Document(page_content="Document 1", metadata={"source": "doc1.pdf"}),
    Document(page_content="Document 2", metadata={"source": "doc2.pdf"})
]

doc_ids = vector_store.save_and_embed(
    embedding_type=EmbeddingType.OPENAI,
    docs=docs
)

# Search similar documents
results = vector_store.search_similar(
    query="search query",
    k=5,
    filter_criteria={"source": "doc1.pdf"}
)

# Get as retriever (for LangChain)
retriever = vector_store.as_retriever(
    search_kwargs={"k": 5}
)

# Delete document
success = vector_store.delete_by_document_id("doc_id_123")

# Close connection
vector_store._close_connection()
```

#### Features

- Uses QdrantConnectionManager for connections
- Auto-creates collection if not exists
- LangChain integration via `langchain_qdrant`
- Metadata filtering support
- Multiple distance metrics (Cosine, Euclid, Dot)
- As retriever support

---

### PgVector Implementation

**Location**: `src/app/db/vector/pgvector.py`

**Purpose**: PostgreSQL + pgvector extension for vector storage

#### PgVector Repository

**Location**: `src/app/db/repositories/pgvector_repo.py`

```python
from src.app.db.repositories.pgvector_repo import PgVectorRepository
from langchain.schema import Document

# Initialize with PostgreSQL connection
repo = PgVectorRepository(connection=pg_connection)

# Create collection
await repo.create_collection(
    collection_name="documents",
    embedding_dimension=1536
)

# Add documents
docs = [Document(page_content="content", metadata={"key": "value"})]
embeddings = [[0.1, 0.2, ...]]  # 1536 dimensions

await repo.add_documents(
    collection_name="documents",
    documents=docs,
    embeddings=embeddings,
    ids=["doc1", "doc2"]
)

# Update document
await repo.update_document(
    collection_name="documents",
    document_id="doc1",
    document=updated_doc,
    embedding=new_embedding
)

# Search similar
results = await repo.search_similar(
    collection_name="documents",
    query_embedding=[0.1, 0.2, ...],
    k=5,
    filter_criteria={"key": "value"}
)

# Delete document
await repo.delete_document(
    collection_name="documents",
    document_id="doc1"
)

# Get metadata
metadata = await repo.get_document_metadata(
    collection_name="documents",
    document_id="doc1"
)
```

#### Database Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create collection table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    embedding vector(1536),
    metadata JSONB,
    embedded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create IVFFlat index for fast similarity search
CREATE INDEX documents_embedding_idx 
ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

#### Features

- Leverages PostgreSQL infrastructure
- ACID transactions for vectors
- IVFFlat indexing for performance
- JSONB metadata storage
- LangChain PGVector integration

---

### ChromaDB Implementation

**Location**: `src/app/db/vector/chromadb.py`

**Registry**: `@VectorDBRegistry.register(VectorDBType.CHROMADB)`

#### Features

- Embedded and client-server modes
- Automatic persistence
- Multiple embedding functions
- Simple API
- No external dependencies for embedded mode

**Status**: Implementation follows same pattern as Qdrant

---

## Embedding System

The embedding system converts text to vector representations for semantic search.

### Embedding Factory

**Location**: `src/app/db/vector/providers/embedding_provider.py`

**Pattern**: Factory + Registry Pattern

```python
from src.app.db.vector.embeddings.embedding import EmbeddingFactory
from src.app.core.constants import EmbeddingType

# Get embedding model
embedding_model = EmbeddingFactory.get_embedding_model(
    embedding_type=EmbeddingType.OPENAI,
    embedding_config=None  # Uses default from config
)

# Embed text
text = "This is a sample document"
embedding = embedding_model.embed_query(text)  # Returns List[float]

# Embed multiple documents
texts = ["doc1", "doc2", "doc3"]
embeddings = embedding_model.embed_documents(texts)  # Returns List[List[float]]
```

### Supported Providers

**Location**: `src/app/db/vector/embeddings/embedding.py`

#### OpenAI Embeddings

```python
@EmbeddingFactory.register(EmbeddingType.OPENAI)
def _create_openai_embedding(config):
    return OpenAIEmbeddings(
        openai_api_key=config["openai_api_key"],
        model=config["openai_model"]  # text-embedding-ada-002
    )
```

**Configuration**:
```yaml
embeddings:
  openai_api_key: "${OPENAI_API_KEY}"
  openai_model: "text-embedding-ada-002"
```

#### HuggingFace Embeddings

```python
@EmbeddingFactory.register(EmbeddingType.HUGGINGFACE)
def _create_huggingface_embedding(config):
    return HuggingFaceEmbeddings(
        model_name=config["huggingface_model"],
        model_kwargs={"device": config["device"]},
        encode_kwargs={"batch_size": config["batch_size"]}
    )
```

**Configuration**:
```yaml
embeddings:
  huggingface_model: "sentence-transformers/all-MiniLM-L6-v2"
  device: "cpu"  # or "cuda"
  batch_size: 32
```

#### Instructor Embeddings

```python
@EmbeddingFactory.register(EmbeddingType.INSTRUCTOR)
def _create_instructor_embedding(config):
    return HuggingFaceInstructEmbeddings(
        model_name=config["instructor_model"],
        model_kwargs={"device": config["device"]},
        encode_kwargs={"batch_size": config["batch_size"]}
    )
```

**Configuration**:
```yaml
embeddings:
  instructor_model: "hkunlp/instructor-large"
  device: "cpu"
  batch_size: 32
```

#### Cohere Embeddings

```python
@EmbeddingFactory.register(EmbeddingType.COHERE)
def _create_cohere_embedding(config):
    return CohereEmbeddings(
        cohere_api_key=config["cohere_api_key"]
    )
```

**Configuration**:
```yaml
embeddings:
  cohere_api_key: "${COHERE_API_KEY}"
```

---

## Repository Design

The database layer uses the **Repository Pattern** for clean separation of concerns.

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Single Responsibility** | Each repository manages one data model |
| **Dependency Injection** | Repositories accept optional DB connections |
| **Auto-Connection** | Repositories auto-connect if no DB provided |
| **Error Handling** | Comprehensive logging and error messages |
| **Type Safety** | Full type hints throughout |

### Repository Template

```python
"""
{Entity} Repository for {Database} operations.
"""

from typing import Optional, Dict, Any
from pymongo.database import Database

from src.app.db.models.{entity} import {Entity}
from src.app.core.utils.logger import get_logger

logger = get_logger(__name__)


class {Entity}Repository:
    """
    Repository for {Entity} model operations.
    
    Supports both dependency injection and automatic connection management.
    """
    
    COLLECTION_NAME = "{collection_name}"
    _instance: Optional['{Entity}Repository'] = None
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize the repository.
        
        Args:
            db: Database instance (optional - will auto-connect if not provided)
        """
        self._db = db
        self._collection = None
        self._indexes_ensured = False
    
    @property
    def db(self) -> Database:
        """Get database instance, connecting if necessary."""
        if self._db is None:
            from src.app.connections import ConnectionFactory, ConnectionType
            connection_manager = ConnectionFactory.get_connection_manager(
                ConnectionType.MONGODB
            )
            connection_manager.connect()
            self._db = connection_manager.get_database()
            logger.info(f"Auto-connected to MongoDB for {self.__class__.__name__}")
        return self._db
    
    @property
    def collection(self):
        """Get collection, ensuring indexes on first access."""
        if self._collection is None:
            self._collection = self.db[self.COLLECTION_NAME]
            if not self._indexes_ensured:
                self._ensure_indexes()
                self._indexes_ensured = True
        return self._collection
    
    def _ensure_indexes(self):
        """Create indexes if they don't exist."""
        try:
            # Create your indexes here
            self.collection.create_index("field_name", unique=True)
            logger.info(f"{self.COLLECTION_NAME} indexes ensured")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}", exc_info=True)
    
    # Add your CRUD methods here
```

---

## Creating Custom Repositories

### Step-by-Step Guide

#### 1. Create Model

```python
# src/app/db/models/product.py
from pydantic import BaseModel, Field
from datetime import datetime

class Product(BaseModel):
    """Product model."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    price: float = Field(..., gt=0)
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()

class ProductInDB(Product):
    """Product with MongoDB ID."""
    
    _id: str = Field(..., alias="_id")
```

#### 2. Create Repository

```python
# src/app/db/repositories/product_repository.py
from typing import Optional, List, Dict, Any
from pymongo.database import Database
from pymongo.errors import PyMongoError

from src.app.db.models.product import Product, ProductInDB
from src.app.core.utils.logger import get_logger

logger = get_logger(__name__)


class ProductRepository:
    """Repository for Product model operations."""
    
    COLLECTION_NAME = "products"
    
    def __init__(self, db: Optional[Database] = None):
        self._db = db
        self._collection = None
        self._indexes_ensured = False
    
    @property
    def db(self) -> Database:
        """Get database instance, connecting if necessary."""
        if self._db is None:
            from src.app.connections import ConnectionFactory, ConnectionType
            connection_manager = ConnectionFactory.get_connection_manager(
                ConnectionType.MONGODB
            )
            connection_manager.connect()
            self._db = connection_manager.get_database()
            logger.info("Auto-connected to MongoDB for ProductRepository")
        return self._db
    
    @property
    def collection(self):
        """Get collection, ensuring indexes."""
        if self._collection is None:
            self._collection = self.db[self.COLLECTION_NAME]
            if not self._indexes_ensured:
                self._ensure_indexes()
                self._indexes_ensured = True
        return self._collection
    
    def _ensure_indexes(self):
        """Create indexes."""
        try:
            self.collection.create_index("name")
            self.collection.create_index("category")
            logger.info("Product collection indexes ensured")
        except PyMongoError as e:
            logger.error(f"Failed to create indexes: {e}", exc_info=True)
    
    async def create_product(
        self,
        name: str,
        description: str,
        price: float,
        category: str
    ) -> Optional[ProductInDB]:
        """Create a new product."""
        try:
            product = Product(
                name=name,
                description=description,
                price=price,
                category=category
            )
            
            product_dict = product.to_dict()
            result = self.collection.insert_one(product_dict)
            
            product_dict["_id"] = str(result.inserted_id)
            return ProductInDB(**product_dict)
            
        except Exception as e:
            logger.error(f"Error creating product: {e}", exc_info=True)
            raise
    
    async def get_product_by_id(self, product_id: str) -> Optional[ProductInDB]:
        """Get product by ID."""
        try:
            from bson import ObjectId
            product_dict = self.collection.find_one({"_id": ObjectId(product_id)})
            
            if product_dict:
                product_dict["_id"] = str(product_dict["_id"])
                return ProductInDB(**product_dict)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving product: {e}", exc_info=True)
            raise
    
    async def list_products(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[ProductInDB]:
        """List products with optional filtering."""
        try:
            query = {}
            if category:
                query["category"] = category
            
            cursor = self.collection.find(query).limit(limit)
            products = []
            
            for product_dict in cursor:
                product_dict["_id"] = str(product_dict["_id"])
                products.append(ProductInDB(**product_dict))
            
            return products
            
        except Exception as e:
            logger.error(f"Error listing products: {e}", exc_info=True)
            raise
```

#### 3. Use Repository

```python
from src.app.db.repositories.product_repository import ProductRepository

# Initialize
repo = ProductRepository()

# Create product
product = await repo.create_product(
    name="Laptop",
    description="High-performance laptop",
    price=1299.99,
    category="Electronics"
)

# Get product
product = await repo.get_product_by_id(product._id)

# List products
products = await repo.list_products(category="Electronics", limit=50)
```

---

## Best Practices

### 1. Use Auto-Connection

```python
# GOOD - Auto-connects if needed
repo = UserRepository()
user = await repo.get_user_by_email("john@example.com")

# BAD - Unnecessary manual connection management
manager = ConnectionFactory.get_connection_manager(ConnectionType.MONGODB)
manager.connect()
db = manager.get_database()
repo = UserRepository(db=db)
```

### 2. Handle Duplicates Gracefully

```python
# GOOD - Check before insert
if await repo.check_email_exists(email):
    raise ValueError("Email already exists")

user = await repo.create_user(...)

# BAD - Rely on exception
try:
    user = await repo.create_user(...)
except DuplicateKeyError:
    raise ValueError("Email already exists")
```

### 3. Use Type Hints

```python
# GOOD
async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
    pass

# BAD
async def get_user_by_email(self, email):
    pass
```

### 4. Log Important Operations

```python
# GOOD
logger.info(f"Creating user with email: {email}")
result = await repo.create_user(...)
logger.info(f"User created with ID: {result._id}")

# BAD - Silent operations
result = await repo.create_user(...)
```

### 5. Validate Before Storage

```python
# GOOD - Validate in Pydantic model
class User(BaseModel):
    email: EmailStr  # Automatic validation
    username: str = Field(..., min_length=3, max_length=30)

# BAD - No validation
user_dict = {"email": email, "username": username}
collection.insert_one(user_dict)
```

---

## API Reference

### UserRepository

```python
class UserRepository:
    COLLECTION_NAME = "users"
    
    async def create_user(...) -> Optional[UserInDB]
    async def get_user_by_email(email: str) -> Optional[UserInDB]
    async def get_user_by_username(username: str) -> Optional[UserInDB]
    async def get_user_by_id(user_id: str) -> Optional[UserInDB]
    async def update_user(user_id: str, update_data: Dict) -> bool
    async def check_email_exists(email: str) -> bool
    async def check_username_exists(username: str) -> bool
```

### SignupSessionRepository

```python
class SignupSessionRepository:
    KEY_PREFIX = "signup"
    SESSION_TTL = 300  # seconds
    
    async def create_session(session_id: str, initial_data: Dict) -> bool
    async def get_session(session_id: str) -> Optional[Dict]
    async def update_session(session_id: str, update_data: Dict) -> bool
    async def update_field(session_id: str, field: str, value: Any) -> bool
    async def delete_session(session_id: str) -> bool
    async def session_exists(session_id: str) -> bool
    async def increment_attempt(session_id: str) -> int
    async def refresh_ttl(session_id: str) -> bool
```

### VectorDB (Base)

```python
class VectorDB(ABC):
    @abstractmethod
    def get_vector_db_config() -> Dict[str, Any]
    
    @abstractmethod
    async def save_and_embed(
        embedding_type: EmbeddingType, 
        docs: List[Document]
    ) -> List[str]
    
    @abstractmethod
    async def update_document(
        document_id: str, 
        updated_doc: Document,
        embedding_type: EmbeddingType
    ) -> bool
    
    @abstractmethod
    async def delete_by_document_id(document_id: str) -> bool
    
    @abstractmethod
    async def get_document_metadata(document_id: str) -> Optional[DocumentMetadata]
```

### EmbeddingFactory

```python
class EmbeddingFactory:
    @classmethod
    def register(cls, name: EmbeddingType)
    
    @classmethod
    def get_embedding_model(
        cls,
        embedding_type: EmbeddingType,
        embedding_config: Optional[Dict] = None
    )
```

---

## Future Improvements

The database layer is functional but has areas for enhancement:

### 1. PostgreSQL Repository

**Current**: No dedicated PostgreSQL repository

**Future**: Add repositories for relational data
```python
class PostgresRepository:
    """Base repository for PostgreSQL operations."""
    
    def __init__(self, connection_manager=None):
        self._connection_manager = connection_manager or \
            ConnectionFactory.get_connection_manager(ConnectionType.POSTGRES)
```

### 2. Repository Registry

**Current**: Repositories instantiated directly

**Future**: Registry pattern for repositories
```python
@RepositoryRegistry.register("user")
class UserRepository:
    pass

# Usage
repo = RepositoryRegistry.get("user")
```

### 3. Transaction Support

**Current**: Single-operation transactions

**Future**: Multi-operation transactions
```python
async with repo.transaction() as tx:
    await tx.create_user(...)
    await tx.create_profile(...)
    await tx.commit()
```

### 4. Query Builder

**Current**: Raw MongoDB queries

**Future**: Fluent query builder
```python
users = await repo.query() \
    .where("age", ">", 25) \
    .where("is_active", "=", True) \
    .order_by("created_at", "desc") \
    .limit(10) \
    .execute()
```

### 5. Migration System

**Current**: Manual index creation

**Future**: Versioned migrations
```python
# migrations/001_create_users_table.py
class CreateUsersTable(Migration):
    def up(self):
        self.create_collection("users")
        self.create_index("users", "email", unique=True)
    
    def down(self):
        self.drop_collection("users")
```

### 6. Caching Layer

**Current**: No caching

**Future**: Redis caching for frequent queries
```python
@cached(ttl=300)  # Cache for 5 minutes
async def get_user_by_id(self, user_id: str):
    return await self.collection.find_one({"_id": ObjectId(user_id)})
```

### 7. Soft Deletes

**Current**: Hard deletes

**Future**: Soft delete support
```python
async def delete_user(self, user_id: str, soft: bool = True):
    if soft:
        await self.update_user(user_id, {"deleted_at": datetime.utcnow()})
    else:
        await self.collection.delete_one({"_id": ObjectId(user_id)})
```

### 8. Audit Logging

**Current**: Manual logging

**Future**: Automatic audit trails
```python
class AuditedRepository(BaseRepository):
    """Repository with automatic audit logging."""
    
    async def create(self, data: dict):
        result = await super().create(data)
        await self._log_audit("CREATE", result)
        return result
```

### 9. Vector Store Unification

**Current**: Separate implementations for each vector DB

**Future**: Unified interface with adapters
```python
class UnifiedVectorStore:
    """Unified interface for all vector databases."""
    
    def __init__(self, backend: VectorDBType):
        self._backend = VectorDBRegistry.get(backend)
    
    async def add(self, documents: List[Document]):
        return await self._backend.add_documents(documents)
```

### 10. Connection Pooling Improvements

**Current**: Basic connection management

**Future**: Advanced pooling strategies
```python
class RepositoryPool:
    """Connection pool for repositories."""
    
    async def __aenter__(self):
        self._connection = await self._pool.acquire()
        return self
    
    async def __aexit__(self, *args):
        await self._pool.release(self._connection)
```

---

## Related Documentation

- **[Connection Management](../connections/README.md)** - Database connection details
- **[Configuration Guide](../configuration/README.md)** - Database configuration
- **[API Documentation](../../api/README.md)** - REST API endpoints

---

**Last Updated**: January 10, 2026  
**Version**: 1.0  
**Related**: Database Layer, Repository Pattern, MongoDB, Redis, Vector Stores

---

## Contributing

Contributions to improve the database layer are welcome!

### Areas for Contribution

1. **New Repositories** - Add repositories for new data models
2. **Query Optimization** - Improve query performance
3. **Migration System** - Build database migration framework
4. **Testing** - Add integration tests for repositories
5. **Documentation** - Improve inline documentation

### Submission Process

1. Follow repository pattern template
2. Add comprehensive tests
3. Update this documentation
4. Submit pull request with clear description

---

Thank you for using AgentHub's database layer! 
