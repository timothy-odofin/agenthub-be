"""
Vector database configuration management.
"""

import os
from pathlib import Path
from app.core.utils.single_ton import SingletonMeta


class VectorConfig(metaclass=SingletonMeta):
    """Vector database configuration for all vector database types."""
    
    def __init__(self):
        # Get project root for path-based configurations
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
    
    @property
    def qdrant_config(self) -> dict:
        """Qdrant vector database configuration"""
        return {
            'url': os.getenv('QDRANT_ENDPOINT'),
            'api_key': os.getenv('QDRANT_API_KEY'),
            'collection_name': os.getenv('QDRANT_COLLECTION_NAME', 'agent_hub_collection'),
            'embedding_dimension': int(os.getenv('QDRANT_EMBEDDING_DIMENSION', '1536')),
            'distance': os.getenv('QDRANT_DISTANCE', 'Cosine')
        }
    
    @property
    def pgvector_config(self) -> dict:
        """PgVector-specific configuration"""
        # Import here to avoid circular import
        from .database_config import database_config
        
        return {
            'connection_string': os.getenv(
                'PGVECTOR_CONNECTION_STRING', 
                database_config.postgres_config['connection_string']
            ),
            'collection_name': os.getenv('PGVECTOR_COLLECTION_NAME', 'documents'),
            'embedding_dimension': int(os.getenv('PGVECTOR_EMBEDDING_DIMENSION', '1536')),
            'distance_strategy': os.getenv('PGVECTOR_DISTANCE_STRATEGY', 'cosine'),
            'pre_delete_collection': os.getenv('PGVECTOR_PRE_DELETE_COLLECTION', 'false').lower() == 'true'
        }
    
    @property
    def chromadb_config(self) -> dict:
        """ChromaDB-specific configuration"""
        return {
            'collection_name': os.getenv('CHROMADB_COLLECTION_NAME', 'documents'),
            'persist_directory': os.getenv('CHROMADB_PERSIST_DIRECTORY', str(self.project_root / 'volumes' / 'chromadb')),
            'embedding_type': os.getenv('CHROMADB_EMBEDDING_TYPE', 'openai'),
            'distance_metric': os.getenv('CHROMADB_DISTANCE_METRIC', 'cosine')
        }
    
    @property
    def chroma_config(self) -> dict:
        """ChromaDB configuration"""
        return {
            'host': os.getenv('CHROMA_HOST', 'localhost'),
            'port': int(os.getenv('CHROMA_PORT', '8000')),
            'collection_name': os.getenv('CHROMA_COLLECTION_NAME', 'documents'),
            'persist_directory': os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')
        }
    
    @property
    def pinecone_config(self) -> dict:
        """Pinecone vector database configuration"""
        return {
            'api_key': os.getenv('PINECONE_API_KEY'),
            'environment': os.getenv('PINECONE_ENVIRONMENT'),
            'index_name': os.getenv('PINECONE_INDEX_NAME', 'documents'),
            'dimension': int(os.getenv('PINECONE_DIMENSION', '1536')),
            'metric': os.getenv('PINECONE_METRIC', 'cosine')
        }
    
    @property
    def weaviate_config(self) -> dict:
        """Weaviate vector database configuration"""
        return {
            'url': os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
            'api_key': os.getenv('WEAVIATE_API_KEY'),
            'class_name': os.getenv('WEAVIATE_CLASS_NAME', 'Document'),
            'text_key': os.getenv('WEAVIATE_TEXT_KEY', 'content')
        }
    
    @property
    def milvus_config(self) -> dict:
        """Milvus vector database configuration"""
        return {
            'host': os.getenv('MILVUS_HOST', 'localhost'),
            'port': int(os.getenv('MILVUS_PORT', '19530')),
            'collection_name': os.getenv('MILVUS_COLLECTION_NAME', 'documents'),
            'dimension': int(os.getenv('MILVUS_DIMENSION', '1536')),
            'index_type': os.getenv('MILVUS_INDEX_TYPE', 'IVF_FLAT'),
            'metric_type': os.getenv('MILVUS_METRIC_TYPE', 'L2')
        }
    
    @property
    def opensearch_config(self) -> dict:
        """OpenSearch vector database configuration"""
        return {
            'host': os.getenv('OPENSEARCH_HOST', 'localhost'),
            'port': int(os.getenv('OPENSEARCH_PORT', '9200')),
            'username': os.getenv('OPENSEARCH_USERNAME'),
            'password': os.getenv('OPENSEARCH_PASSWORD'),
            'index_name': os.getenv('OPENSEARCH_INDEX_NAME', 'documents'),
            'use_ssl': os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true',
            'verify_certs': os.getenv('OPENSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
        }
    
    @property
    def embedding_config(self) -> dict:
        """Embedding models configuration"""
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'openai_model': os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002'),
            'huggingface_model': os.getenv('HUGGINGFACE_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
            'instructor_model': os.getenv('INSTRUCTOR_EMBEDDING_MODEL', 'hkunlp/instructor-xl'),
            'device': os.getenv('EMBEDDING_DEVICE', 'cpu'),
            'batch_size': int(os.getenv('EMBEDDING_BATCH_SIZE', '32')),
            'cohere_api_key': os.getenv('COHERE_API_KEY')
        }
    
    def get_connection_config(self, connection_name: str) -> dict:
        """
        Get configuration for a specific vector database connection.
        
        Args:
            connection_name: Name of the vector database connection
            
        Returns:
            Dict with vector database configuration
            
        Raises:
            KeyError: If connection name not found
        """
        config_map = {
            'qdrant': self.qdrant_config,
            'pgvector': self.pgvector_config,
            'chromadb': self.chromadb_config,
            'chroma': self.chroma_config,
            'pinecone': self.pinecone_config,
            'weaviate': self.weaviate_config,
            'milvus': self.milvus_config,
            'opensearch': self.opensearch_config
        }
        
        if connection_name not in config_map:
            available = list(config_map.keys())
            raise KeyError(f"Vector database connection '{connection_name}' not found. Available: {available}")
        
        return config_map[connection_name]


# Create singleton instance
vector_config = VectorConfig()
