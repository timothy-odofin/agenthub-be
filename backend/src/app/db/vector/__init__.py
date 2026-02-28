"""
Vector database module for AgentHub.

This module provides a unified interface for different vector database implementations,
supporting document embedding, storage, and retrieval operations.

Available implementations:
- PgVectorDB: PostgreSQL with pgvector extension
- ChromaDB: ChromaDB implementation
- QdrantDB: Qdrant implementation
"""

# Import vector database implementations to trigger registration decorators
from . import chromadb, pgvector, qdrant
from .base import DocumentMetadata, VectorDB
from .embeddings import EmbeddingFactory as EmbeddingFactoryAlias

# Import providers package - this will trigger all registrations
from .providers import EmbeddingFactory, VectorStoreFactory

# Public API - only these classes are exported
__all__ = [
    "VectorDB",  # Abstract base class for vector databases
    "DocumentMetadata",  # Document metadata and utilities
    "VectorStoreFactory",  # Factory for creating vector stores
    "EmbeddingFactory",  # Factory for creating embeddings
]

# Version info (optional)
__version__ = "1.0.0"
