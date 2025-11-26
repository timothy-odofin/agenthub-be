"""
Vector database connection managers.
"""

from app.core.utils.dynamic_import import import_providers

# Vector database connection modules configuration: (module_name, class_name)
VECTOR_CONNECTION_MODULES = [
    ('qdrant_connection_manager', 'QdrantConnectionManager'),
    ('chromadb_connection_manager', 'ChromaDBConnectionManager'),
    ('pgvector_connection_manager', 'PgVectorConnectionManager'),
]

# Import vector database connection managers using the generic utility
__all__ = import_providers(__name__, VECTOR_CONNECTION_MODULES, globals(), suppress_warnings=True)
