"""
Vector database module for AgentHub.

This module provides a unified interface for different vector database implementations,
supporting document embedding, storage, and retrieval operations.

Available implementations:
- PgVectorDB: PostgreSQL with pgvector extension
- Future: Qdrant, Pinecone, Chroma, etc.
"""

from .base import VectorDB, DocumentMetadata
from .pgvector import PgVectorDB
from .chromadb import ChromaDB
from .embedding import EmbeddingFactory
from .factory import VectorStoreFactory

# Public API - only these classes are exported
__all__ = [
    'VectorDB',           # Abstract base class for vector databases
    'DocumentMetadata',   # Document metadata and utilities
    'PgVectorDB',        # PostgreSQL implementation
    'ChromaDB',          # ChromaDB implementation
    'EmbeddingFactory',  # Embedding model factory
    'VectorStoreFactory', # Vector store factory
]

# Version info (optional)
__version__ = "1.0.0"
