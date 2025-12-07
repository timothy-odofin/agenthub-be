"""
Unit tests for vector configuration module
"""

import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from src.app.core.config.providers.vector import VectorConfig


class TestVectorConfig:
    """Test vector configuration functionality"""

    @pytest.fixture
    def vector_config(self):
        """Fixture to create VectorConfig instance"""
        return VectorConfig()

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_qdrant_config_with_settings(self, mock_settings, vector_config):
        """Test Qdrant configuration with Settings system"""
        # Setup mock
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.qdrant = SimpleNamespace(
            endpoint='http://qdrant-host:6333',
            api_key='test-api-key',
            collection_name='test_collection',
            embedding_dimension=1536,
            distance='Cosine'
        )

        config = vector_config.qdrant_config

        expected = {
            'url': 'http://qdrant-host:6333',
            'api_key': 'test-api-key',
            'collection_name': 'test_collection',
            'embedding_dimension': 1536,
            'distance': 'Cosine'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_qdrant_config_without_settings(self, mock_settings, vector_config):
        """Test Qdrant configuration when no settings configured"""
        # Mock settings without vector section
        mock_settings.vector = None
        del mock_settings.vector

        config = vector_config.qdrant_config
        assert config == {}

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_pgvector_config_with_settings(self, mock_settings, vector_config):
        """Test PgVector configuration with Settings system"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.pgvector = SimpleNamespace(
            connection_string='postgresql://user:pass@localhost:5432/vector_db',
            collection_name='documents',
            embedding_dimension=1536,
            distance_strategy='cosine',
            pre_delete_collection=False
        )

        config = vector_config.pgvector_config

        expected = {
            'connection_string': 'postgresql://user:pass@localhost:5432/vector_db',
            'collection_name': 'documents',
            'embedding_dimension': 1536,
            'distance_strategy': 'cosine',
            'pre_delete_collection': False
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_chromadb_config_with_settings(self, mock_settings, vector_config):
        """Test ChromaDB configuration with Settings system"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.chromadb = SimpleNamespace(
            collection_name='documents',
            persist_directory='./chroma_data',
            embedding_type='openai',
            distance_metric='cosine'
        )

        config = vector_config.chromadb_config

        expected = {
            'collection_name': 'documents',
            'persist_directory': './chroma_data',
            'embedding_type': 'openai',
            'distance_metric': 'cosine'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_chroma_config_with_settings(self, mock_settings, vector_config):
        """Test Chroma configuration with Settings system"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.chroma = SimpleNamespace(
            host='chroma-host',
            port=8000,
            collection_name='documents'
        )

        config = vector_config.chroma_config

        expected = {
            'host': 'chroma-host',
            'port': 8000,
            'collection_name': 'documents',
            'persist_directory': './chroma_db'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_pinecone_config_with_settings(self, mock_settings, vector_config):
        """Test Pinecone configuration with Settings system"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.pinecone = SimpleNamespace(
            api_key='test-api-key',
            environment='us-west1-gcp',
            index_name='documents',
            dimension=1536,
            metric='cosine'
        )

        config = vector_config.pinecone_config

        expected = {
            'api_key': 'test-api-key',
            'environment': 'us-west1-gcp',
            'index_name': 'documents',
            'dimension': 1536,
            'metric': 'cosine'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_weaviate_config_with_settings(self, mock_settings, vector_config):
        """Test Weaviate configuration with Settings system"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.weaviate = SimpleNamespace(
            url='http://weaviate-host:8080',
            api_key='test-api-key',
            class_name='Documents'
        )

        config = vector_config.weaviate_config

        expected = {
            'url': 'http://weaviate-host:8080',
            'api_key': 'test-api-key',
            'class_name': 'Documents',
            'text_key': 'content'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_milvus_config_with_settings(self, mock_settings, vector_config):
        """Test Milvus configuration with Settings system"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.milvus = SimpleNamespace(
            host='milvus-host',
            port=19530,
            collection_name='documents',
            dimension=1536,
            index_type='IVF_FLAT',
            metric_type='L2'
        )

        config = vector_config.milvus_config

        expected = {
            'host': 'milvus-host',
            'port': 19530,
            'collection_name': 'documents',
            'dimension': 1536,
            'index_type': 'IVF_FLAT',
            'metric_type': 'L2'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_opensearch_config_with_settings(self, mock_settings, vector_config):
        """Test OpenSearch configuration with Settings system"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.opensearch = SimpleNamespace(
            host='opensearch-host',
            port=9200,
            username='user',
            password='pass',
            index_name='documents',
            use_ssl=True,
            verify_certs=False
        )

        config = vector_config.opensearch_config

        expected = {
            'host': 'opensearch-host',
            'port': 9200,
            'username': 'user',
            'password': 'pass',
            'index_name': 'documents',
            'use_ssl': True,
            'verify_certs': False
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_embedding_config_with_settings(self, mock_settings, vector_config):
        """Test embedding configuration with Settings system"""
        mock_settings.embeddings = SimpleNamespace(
            openai_api_key='openai-key',
            openai_model='text-embedding-ada-002',
            huggingface_model='sentence-transformers/all-MiniLM-L6-v2',
            instructor_model='hkunlp/instructor-xl',
            device='cuda',
            batch_size=64,
            cohere_api_key='cohere-key'
        )

        config = vector_config.embedding_config

        expected = {
            'openai_api_key': 'openai-key',
            'openai_model': 'text-embedding-ada-002',
            'huggingface_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'instructor_model': 'hkunlp/instructor-xl',
            'device': 'cuda',
            'batch_size': 64,
            'cohere_api_key': 'cohere-key'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_embedding_config_without_settings(self, mock_settings, vector_config):
        """Test embedding configuration when no settings configured"""
        # Mock settings without embeddings section
        mock_settings.embeddings = None
        del mock_settings.embeddings

        config = vector_config.embedding_config
        assert config == {}

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_get_connection_config_existing(self, mock_settings, vector_config):
        """Test get_connection_config for existing connection"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.qdrant = SimpleNamespace(
            endpoint='http://qdrant-host:6333',
            api_key='test-api-key',
            collection_name='test_collection',
            embedding_dimension=1536,
            distance='Cosine'
        )

        config = vector_config.get_connection_config('qdrant')

        expected = {
            'url': 'http://qdrant-host:6333',
            'api_key': 'test-api-key',
            'collection_name': 'test_collection',
            'embedding_dimension': 1536,
            'distance': 'Cosine'
        }
        assert config == expected

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_get_connection_config_unknown_connection(self, mock_settings, vector_config):
        """Test get_connection_config for unknown connection returns empty dict"""
        mock_settings.vector = None
        del mock_settings.vector

        config = vector_config.get_connection_config('unknown')
        assert config == {}

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_get_connection_config_empty_config(self, mock_settings, vector_config):
        """Test get_connection_config when config is empty"""
        mock_settings.vector = None
        del mock_settings.vector

        config = vector_config.get_connection_config('qdrant')
        assert config == {}

    @patch('src.app.core.config.providers.vector.settings', create=True)
    def test_config_with_defaults(self, mock_settings, vector_config):
        """Test configuration uses defaults when attributes missing"""
        mock_settings.vector = SimpleNamespace()
        mock_settings.vector.qdrant = SimpleNamespace(
            endpoint='http://localhost:6333'
        )

        config = vector_config.qdrant_config

        expected = {
            'url': 'http://localhost:6333',
            'api_key': None,
            'collection_name': 'agent_hub_collection',
            'embedding_dimension': 1536,
            'distance': 'Cosine'
        }
        assert config == expected

    def test_vector_config_singleton(self):
        """Test vector config singleton instance"""
        from src.app.core.config.providers.vector import vector_config as singleton_instance
        
        assert isinstance(singleton_instance, VectorConfig)
        assert singleton_instance is not None
