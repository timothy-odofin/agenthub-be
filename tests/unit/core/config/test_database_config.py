"""
Unit tests for DatabaseConfig class.
"""

import unittest
from unittest.mock import Mock, patch

from app.core.config.providers.database import DatabaseConfig


class TestDatabaseConfig(unittest.TestCase):
    """Test cases for DatabaseConfig class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a fresh instance for each test
        # Note: Since it's a singleton, we need to clear the registry
        DatabaseConfig._instances = {}
        self.config = DatabaseConfig()
    
    @patch('app.core.config.providers.database.settings')
    def test_postgres_config_with_settings(self, mock_settings):
        """Test postgres configuration with valid settings."""
        # Mock postgres settings
        mock_postgres = Mock()
        mock_postgres.username = 'test_user'
        mock_postgres.password = 'test_pass'
        mock_postgres.host = 'localhost'
        mock_postgres.port = 5432
        mock_postgres.database = 'test_db'
        
        mock_settings.db.postgres = mock_postgres
        
        result = self.config.postgres_config
        
        expected = {
            'username': 'test_user',
            'password': 'test_pass',
            'database': 'test_db',
            'host': 'localhost',
            'port': 5432,
            'connection_string': 'postgresql://test_user:test_pass@localhost:5432/test_db'
        }
        
        self.assertEqual(result, expected)
    
    @patch('app.core.config.providers.database.settings')
    def test_postgres_config_missing_settings(self, mock_settings):
        """Test postgres configuration when settings are missing."""
        # Mock missing settings
        del mock_settings.db
        
        result = self.config.postgres_config
        
        self.assertEqual(result, {})
    
    @patch('app.core.config.providers.database.settings')
    def test_redis_config_with_password(self, mock_settings):
        """Test redis configuration with password."""
        # Mock redis settings with password
        mock_redis = Mock()
        mock_redis.host = 'redis-host'
        mock_redis.port = 6379
        mock_redis.password = 'redis_pass'
        mock_redis.database = 1
        
        mock_settings.db.redis = mock_redis
        
        result = self.config.redis_config
        
        expected = {
            'host': 'redis-host',
            'port': 6379,
            'password': 'redis_pass',
            'db': 1,
            'url': 'redis://:redis_pass@redis-host:6379/1'
        }
        
        self.assertEqual(result, expected)
    
    @patch('app.core.config.providers.database.settings')
    def test_redis_config_without_password(self, mock_settings):
        """Test redis configuration without password."""
        # Mock redis settings without password
        mock_redis = Mock()
        mock_redis.host = 'redis-host'
        mock_redis.port = 6379
        mock_redis.password = None
        mock_redis.database = 0
        
        mock_settings.db.redis = mock_redis
        
        result = self.config.redis_config
        
        expected = {
            'host': 'redis-host',
            'port': 6379,
            'password': None,
            'db': 0,
            'url': 'redis://redis-host:6379/0'
        }
        
        self.assertEqual(result, expected)
    
    @patch('app.core.config.providers.database.settings')
    def test_mongodb_config_with_connection_string(self, mock_settings):
        """Test mongodb configuration with custom connection string (Atlas)."""
        # Mock mongodb settings with connection string
        mock_mongodb = Mock()
        mock_mongodb.database = 'test_db'
        mock_mongodb.connection_string = 'mongodb+srv://user:<db_password>@cluster.mongodb.net/test_db'
        mock_mongodb.password = 'atlas_pass'
        
        # For connection string mode, set specific attributes
        # Mock getattr to return proper values for optional fields
        original_getattr = getattr
        def mock_getattr_func(obj, attr, default=None):
            if obj is mock_mongodb:
                if attr == 'port':
                    return 27017
                elif attr == 'username':
                    return None
                elif attr == 'password':
                    return 'atlas_pass'  # This should be the actual password
            return original_getattr(obj, attr, default)
        
        mock_settings.db.mongodb = mock_mongodb
        
        with patch('app.core.config.providers.database.getattr', side_effect=mock_getattr_func):
            result = self.config.mongodb_config
        
        expected = {
            'database': 'test_db',
            'connection_string': 'mongodb+srv://user:atlas_pass@cluster.mongodb.net/test_db',
            'is_atlas': True,
            'is_local': False,
            'host': 'atlas',
            'port': 27017,
            'username': None,
            'password': 'atlas_pass'
        }
        
        self.assertEqual(result, expected)
    
    @patch('app.core.config.providers.database.settings')
    def test_mongodb_config_with_individual_components(self, mock_settings):
        """Test mongodb configuration with individual components (local)."""
        # Mock mongodb settings with individual components
        mock_mongodb = Mock()
        mock_mongodb.host = 'localhost'
        mock_mongodb.port = 27017
        mock_mongodb.database = 'test_db'
        mock_mongodb.username = 'mongo_user'
        mock_mongodb.password = 'mongo_pass'
        # No connection_string attribute
        delattr(mock_mongodb, 'connection_string')
        
        mock_settings.db.mongodb = mock_mongodb
        
        result = self.config.mongodb_config
        
        expected = {
            'host': 'localhost',
            'port': 27017,
            'database': 'test_db',
            'username': 'mongo_user',
            'password': 'mongo_pass',
            'connection_string': 'mongodb://mongo_user:mongo_pass@localhost:27017/test_db?authSource=admin',
            'is_atlas': False,
            'is_local': True
        }
        
        self.assertEqual(result, expected)
    
    @patch('app.core.config.providers.database.settings')
    def test_elasticsearch_config_with_settings(self, mock_settings):
        """Test elasticsearch configuration with settings."""
        # Mock elasticsearch settings
        mock_elasticsearch = Mock()
        mock_elasticsearch.host = 'elastic-host'
        mock_elasticsearch.port = 9200
        mock_elasticsearch.username = 'elastic_user'
        mock_elasticsearch.password = 'elastic_pass'
        mock_elasticsearch.use_ssl = True
        mock_elasticsearch.verify_certs = False
        mock_elasticsearch.index_prefix = 'myapp'
        
        mock_settings.db.elasticsearch = mock_elasticsearch
        
        result = self.config.elasticsearch_config
        
        expected = {
            'host': 'elastic-host',
            'port': 9200,
            'username': 'elastic_user',
            'password': 'elastic_pass',
            'use_ssl': True,
            'verify_certs': False,
            'index_prefix': 'myapp'
        }
        
        self.assertEqual(result, expected)
    
    @patch('app.core.config.providers.database.settings')
    def test_elasticsearch_config_with_defaults(self, mock_settings):
        """Test elasticsearch configuration with default values."""
        # Mock elasticsearch settings with minimal config
        mock_elasticsearch = Mock()
        mock_elasticsearch.host = 'elastic-host'
        mock_elasticsearch.port = 9200
        # Remove optional attributes to test defaults
        delattr(mock_elasticsearch, 'username')
        delattr(mock_elasticsearch, 'password')
        delattr(mock_elasticsearch, 'use_ssl')
        delattr(mock_elasticsearch, 'verify_certs')
        delattr(mock_elasticsearch, 'index_prefix')
        
        mock_settings.db.elasticsearch = mock_elasticsearch
        
        result = self.config.elasticsearch_config
        
        expected = {
            'host': 'elastic-host',
            'port': 9200,
            'username': None,
            'password': None,
            'use_ssl': False,
            'verify_certs': False,
            'index_prefix': 'agenthub'
        }
        
        self.assertEqual(result, expected)
    
    @patch('app.core.config.providers.database.settings')
    def test_get_connection_config_postgres(self, mock_settings):
        """Test get_connection_config method for postgres."""
        # Mock postgres settings
        mock_postgres = Mock()
        mock_postgres.username = 'test_user'
        mock_postgres.password = 'test_pass'
        mock_postgres.host = 'localhost'
        mock_postgres.port = 5432
        mock_postgres.database = 'test_db'
        
        mock_settings.db.postgres = mock_postgres
        
        result = self.config.get_connection_config('postgres')
        
        self.assertEqual(result['username'], 'test_user')
        self.assertEqual(result['database'], 'test_db')
    
    @patch('app.core.config.providers.database.settings')
    def test_get_connection_config_unknown(self, mock_settings):
        """Test get_connection_config method for unknown connection."""
        result = self.config.get_connection_config('unknown')
        
        self.assertEqual(result, {})
    
    @patch('app.core.config.providers.database.settings')
    def test_all_configs_missing_settings(self, mock_settings):
        """Test all config methods when settings are missing."""
        # Mock missing settings
        del mock_settings.db
        
        self.assertEqual(self.config.postgres_config, {})
        self.assertEqual(self.config.redis_config, {})
        self.assertEqual(self.config.mongodb_config, {})
        self.assertEqual(self.config.elasticsearch_config, {})
    
    @patch('app.core.config.providers.database.settings')
    def test_singleton_behavior(self, mock_settings):
        """Test that DatabaseConfig behaves as a singleton."""
        # Create two instances
        config1 = DatabaseConfig()
        config2 = DatabaseConfig()
        
        # They should be the same instance
        self.assertIs(config1, config2)
    
    @patch('app.core.config.providers.database.settings')
    def test_registry_integration(self, mock_settings):
        """Test that the class is properly registered in the config source registry."""
        # Import both modules to ensure registration happens
        from app.core.config.framework.registry import ConfigSourceRegistry
        from app.core.config.providers.database import DatabaseConfig, database_config
        
        # Ensure the singleton is initialized
        instance = database_config
        self.assertIsInstance(instance, DatabaseConfig)
        
        # Test that we can get connection configs for registered databases
        # This indirectly tests the registry integration
        
        # Test postgres config retrieval
        postgres_config = instance.get_connection_config('postgres')
        self.assertIsInstance(postgres_config, dict)
        
        # Test redis config retrieval  
        redis_config = instance.get_connection_config('redis')
        self.assertIsInstance(redis_config, dict)
        
        # Test mongodb config retrieval
        mongodb_config = instance.get_connection_config('mongodb')
        self.assertIsInstance(mongodb_config, dict)
        
        # Test unknown connection returns empty dict
        unknown_config = instance.get_connection_config('unknown')
        self.assertEqual(unknown_config, {})


if __name__ == '__main__':
    unittest.main()
