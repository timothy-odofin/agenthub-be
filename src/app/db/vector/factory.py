"""
Vector store factory for creating vector database instances.
"""
from typing import Optional

from ...core.constants import VectorDBType
from ...core.config import config
from .base import VectorDB
from .pgvector import PgVectorDB
from .chromadb import ChromaDB


class VectorStoreFactory:
    """Factory class for creating vector store instances."""
    
    _instance: Optional['VectorStoreFactory'] = None
    _vector_stores = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_vector_store(cls, vector_db_type: VectorDBType = VectorDBType.PGVECTOR) -> VectorDB:
        """
        Get or create a vector store instance.
        
        Args:
            vector_db_type: Type of vector database to create
            
        Returns:
            VectorDB instance
        """
        if vector_db_type in cls._vector_stores:
            return cls._vector_stores[vector_db_type]
        
        if vector_db_type == VectorDBType.PGVECTOR:
            vector_store = PgVectorDB()
        elif vector_db_type == VectorDBType.CHROMA:
            vector_store = ChromaDB()
        else:
            raise ValueError(f"Unsupported vector database type: {vector_db_type}")
        
        cls._vector_stores[vector_db_type] = vector_store
        return vector_store
    
    @classmethod
    def get_default_vector_store(cls) -> VectorDB:
        """Get the default vector store (PgVector)."""
        return cls.get_vector_store(VectorDBType.PGVECTOR)
    
    @classmethod
    def clear_cache(cls):
        """Clear the vector store cache."""
        cls._vector_stores.clear()
