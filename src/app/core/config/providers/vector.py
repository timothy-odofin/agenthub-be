"""
Vector database configuration management using Settings system.
"""

from pathlib import Path
from ..framework.registry import BaseConfigSource, register_connections
from ..framework.settings import settings


@register_connections(['qdrant', 'pgvector', 'chromadb', 'pinecone', 'weaviate', 'milvus', 'opensearch'])
class VectorConfig(BaseConfigSource):
    """Vector database configuration for all vector database types using Settings system."""
    
    def __init__(self):
        # Get project root for path-based configurations
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
    
    @property
    def qdrant_config(self) -> dict:
        """Qdrant vector database configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'qdrant'):
            return {}
            
        qdrant = settings.vector.qdrant
        return {
            'url': qdrant.endpoint,
            'api_key': getattr(qdrant, 'api_key', None),
            'collection_name': getattr(qdrant, 'collection_name', 'agent_hub_collection'),
            'embedding_dimension': getattr(qdrant, 'embedding_dimension', 1536),
            'distance': getattr(qdrant, 'distance', 'Cosine')
        }
    
    @property
    def pgvector_config(self) -> dict:
        """PgVector-specific configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'pgvector'):
            return {}
            
        pgvector = settings.vector.pgvector
        
        # For connection string, try pgvector config first, then fall back to database config
        connection_string = getattr(pgvector, 'connection_string', None)
        if not connection_string:
            # Import here to avoid circular import
            from .database import database_config
            connection_string = database_config.postgres_config.get('connection_string')
        
        return {
            'connection_string': connection_string,
            'collection_name': getattr(pgvector, 'collection_name', 'documents'),
            'embedding_dimension': getattr(pgvector, 'embedding_dimension', 1536),
            'distance_strategy': getattr(pgvector, 'distance_strategy', 'cosine'),
            'pre_delete_collection': getattr(pgvector, 'pre_delete_collection', False)
        }
    
    @property
    def chromadb_config(self) -> dict:
        """ChromaDB-specific configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'chromadb'):
            return {}
            
        chromadb = settings.vector.chromadb
        return {
            'collection_name': getattr(chromadb, 'collection_name', 'documents'),
            'persist_directory': getattr(chromadb, 'persist_directory', str(self.project_root / 'volumes' / 'chromadb')),
            'embedding_type': getattr(chromadb, 'embedding_type', 'openai'),
            'distance_metric': getattr(chromadb, 'distance_metric', 'cosine')
        }
    
    @property
    def chroma_config(self) -> dict:
        """ChromaDB configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'chroma'):
            return {}
            
        chroma = settings.vector.chroma
        return {
            'host': getattr(chroma, 'host', 'localhost'),
            'port': getattr(chroma, 'port', 8000),
            'collection_name': getattr(chroma, 'collection_name', 'documents'),
            'persist_directory': getattr(chroma, 'persist_directory', './chroma_db')
        }
    
    @property
    def pinecone_config(self) -> dict:
        """Pinecone vector database configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'pinecone'):
            return {}
            
        pinecone = settings.vector.pinecone
        return {
            'api_key': getattr(pinecone, 'api_key', None),
            'environment': getattr(pinecone, 'environment', None),
            'index_name': getattr(pinecone, 'index_name', 'documents'),
            'dimension': getattr(pinecone, 'dimension', 1536),
            'metric': getattr(pinecone, 'metric', 'cosine')
        }
    
    @property
    def weaviate_config(self) -> dict:
        """Weaviate vector database configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'weaviate'):
            return {}
            
        weaviate = settings.vector.weaviate
        return {
            'url': getattr(weaviate, 'url', 'http://localhost:8080'),
            'api_key': getattr(weaviate, 'api_key', None),
            'class_name': getattr(weaviate, 'class_name', 'Document'),
            'text_key': getattr(weaviate, 'text_key', 'content')
        }
    
    @property
    def milvus_config(self) -> dict:
        """Milvus vector database configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'milvus'):
            return {}
            
        milvus = settings.vector.milvus
        return {
            'host': getattr(milvus, 'host', 'localhost'),
            'port': getattr(milvus, 'port', 19530),
            'collection_name': getattr(milvus, 'collection_name', 'documents'),
            'dimension': getattr(milvus, 'dimension', 1536),
            'index_type': getattr(milvus, 'index_type', 'IVF_FLAT'),
            'metric_type': getattr(milvus, 'metric_type', 'L2')
        }
    
    @property
    def opensearch_config(self) -> dict:
        """OpenSearch vector database configuration using Settings system"""
        if not hasattr(settings, 'vector') or not hasattr(settings.vector, 'opensearch'):
            return {}
            
        opensearch = settings.vector.opensearch
        return {
            'host': getattr(opensearch, 'host', 'localhost'),
            'port': getattr(opensearch, 'port', 9200),
            'username': getattr(opensearch, 'username', None),
            'password': getattr(opensearch, 'password', None),
            'index_name': getattr(opensearch, 'index_name', 'documents'),
            'use_ssl': getattr(opensearch, 'use_ssl', False),
            'verify_certs': getattr(opensearch, 'verify_certs', False)
        }
    
    @property
    def embedding_config(self) -> dict:
        """Embedding models configuration using Settings system"""
        if not hasattr(settings, 'embeddings'):
            return {}
            
        embeddings = settings.embeddings
        return {
            'openai_api_key': getattr(embeddings, 'openai_api_key', None),
            'openai_model': getattr(embeddings, 'openai_model', 'text-embedding-ada-002'),
            'huggingface_model': getattr(embeddings, 'huggingface_model', 'sentence-transformers/all-MiniLM-L6-v2'),
            'instructor_model': getattr(embeddings, 'instructor_model', 'hkunlp/instructor-xl'),
            'device': getattr(embeddings, 'device', 'cpu'),
            'batch_size': getattr(embeddings, 'batch_size', 32),
            'cohere_api_key': getattr(embeddings, 'cohere_api_key', None)
        }
    
    def get_connection_config(self, connection_name: str) -> dict:
        """
        Get configuration for a specific vector database connection.
        
        Args:
            connection_name: Name of the vector database connection
            
        Returns:
            Dict with vector database configuration
        """
        config_map = {
            'qdrant': self.qdrant_config,
            'pgvector': self.pgvector_config,
            'chromadb': self.chromadb_config,
            'chroma': self.chroma_config,
            'pinecone': self.pinecone_config,
            'weaviate': self.weaviate_config,
            'milvus': self.milvus_config,
            'opensearch': self.opensearch_config,
            'embedding': self.embedding_config
        }
        
        config = config_map.get(connection_name, {})
        if not config:
            # Return empty dict instead of raising exception for graceful degradation
            return {}
        return config


# Create singleton instance
vector_config = VectorConfig()
