"""
Vector database providers package.

This module automatically imports all vector database implementations
to ensure they are registered with the VectorDBRegistry.
"""

# Import the registry and factory first
from .db_provider import VectorDBRegistry, VectorStoreFactory
from .embedding_provider import EmbeddingFactory

# Import all vector database implementations to trigger registration
# These imports will cause each vector DB to register itself via decorators

try:
    from ..pgvector import PgVectorDB
except ImportError:
    # PgVector requires asyncpg and other PostgreSQL dependencies
    pass

try:
    from ..chromadb import ChromaDB
except ImportError:
    # ChromaDB may not be installed
    pass

try:
    from ..qdrant import QdrantDB
except ImportError:
    # Qdrant may not be installed
    pass

__all__ = [
    'VectorDBRegistry',
    'VectorStoreFactory', 
    'EmbeddingFactory',
]