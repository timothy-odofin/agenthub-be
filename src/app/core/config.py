import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv

from app.core.constants import AtlassianProperties

from .schemas.ingestion_config import IngestionConfig

class AppConfig:
    """Application configuration manager implemented as a singleton"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize the instance
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Only initialize once
        if self._initialized:
            return
            
        # Get the project root directory (two levels up from this file)
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # Define resource paths
        self.resources_path = self.project_root / 'resources'
        self.ingestion_config_path = self.resources_path / 'application-data-sources.yaml'
        
        # Load environment variables
        self._load_env()
        self._load_app_config()
        self._load_ingestion_config()

    def _load_env(self):
        """Load environment variables from .env file"""
        load_dotenv(self.project_root / '.env')
        self._initialized = True  # Mark initialization as complete

    def _load_app_config(self):
        """Load application configuration"""
        self.app_env = os.getenv('APP_ENV', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Qdrant configuration
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')
        self.qdrant_endpoint = os.getenv('QDRANT_ENDPOINT')
        self.qdrant_cluster_id = os.getenv('QDRANT_CLUSTER_ID')

    @property
    def postgres_config(self) -> dict:
        """PostgreSQL database configuration"""
        return {
            'user': os.getenv('POSTGRES_USER', 'admin'),
            'password': os.getenv('POSTGRES_PASSWORD', 'admin123'),
            'database': os.getenv('POSTGRES_DB', 'polyagent'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'connection_string': (
                f"postgresql://{os.getenv('POSTGRES_USER', 'admin')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'admin123')}@"
                f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
                f"{os.getenv('POSTGRES_PORT', '5432')}/"
                f"{os.getenv('POSTGRES_DB', 'polyagent')}"
            )
        }

    @property
    def pgvector_config(self) -> dict:
        """PgVector-specific configuration"""
        return {
            'connection_string': os.getenv(
                'PGVECTOR_CONNECTION_STRING', 
                self.postgres_config['connection_string']
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
    def redis_config(self) -> dict:
        """Redis configuration"""
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'password': os.getenv('REDIS_PASSWORD'),
            'db': int(os.getenv('REDIS_DB', '0')),
            'url': f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}"
        }

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
    def atlassian_config(self) -> dict:
        """Atlassian configuration for Confluence and Jira"""
        return {
            'api_key': os.getenv('ATLASSIAN_API_KEY'),
            'email': os.getenv('ATLASSIAN_EMAIL'),
            'confluence_base_url': os.getenv('ATLASSIAN_BASE_URL_CONFLUENCE'),
            'jira_base_url': os.getenv('ATLASSIAN_BASE_URL_JIRA')
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
    def chroma_config(self) -> dict:
        """ChromaDB configuration"""
        return {
            'host': os.getenv('CHROMA_HOST', 'localhost'),
            'port': int(os.getenv('CHROMA_PORT', '8000')),
            'collection_name': os.getenv('CHROMA_COLLECTION_NAME', 'documents'),
            'persist_directory': os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')
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
    def atlassian_config(self) -> dict:
        """Atlassian configuration for Confluence and Jira"""
        return {
            AtlassianProperties.API_KEY: os.getenv('ATLASSIAN_API_KEY'),
            AtlassianProperties.EMAIL: os.getenv('ATLASSIAN_EMAIL'),
            AtlassianProperties.CONFLUENCE_BASE_URL: os.getenv('ATLASSIAN_BASE_URL_CONFLUENCE'),
            AtlassianProperties.JIRA_BASE_URL: os.getenv('ATLASSIAN_BASE_URL_JIRA')
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
            'batch_size': int(os.getenv('EMBEDDING_BATCH_SIZE', '32'))
        }

    def _load_ingestion_config(self) -> None:
        """Load the ingestion configuration from YAML"""
        try:
            if not self.ingestion_config_path.exists():
                self.ingestion_config = None
                return

            with open(self.ingestion_config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
                self.ingestion_config = IngestionConfig.model_validate(config_dict)
                print(f"Ingestion config loaded successfully, total config: {len(self.ingestion_config.data_sources)} data sources")
        except Exception as e:
            print(f"Error loading ingestion config: {e}")
            self.ingestion_config = None

    def reload_ingestion_config(self) -> Optional[IngestionConfig]:
        """Reload the ingestion configuration from YAML"""
        self._load_ingestion_config()
        return self.ingestion_config



# Create a singleton instance
config = AppConfig()
