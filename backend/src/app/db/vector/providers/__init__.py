"""
Vector database providers package.

This module automatically imports all vector database implementations
to ensure they are registered with the VectorDBRegistry.
"""

from app.core.utils.dynamic_import import import_providers

# Import the registry and factory first
from .db_provider import VectorDBRegistry, VectorStoreFactory
from .embedding_provider import EmbeddingFactory

# Vector database modules configuration: (module_path, class_name)
VECTOR_DB_MODULES = [
    ('..pgvector', 'PgVectorDB'),    # Relative path to parent directory
    ('..chromadb', 'ChromaDB'),
    ('..qdrant', 'QdrantDB'),
]

# Import vector database implementations using the generic utility
vector_db_classes = import_providers(__name__, VECTOR_DB_MODULES, globals(), suppress_warnings=True)

__all__ = [
    'VectorDBRegistry',
    'VectorStoreFactory', 
    'EmbeddingFactory',
] + vector_db_classes