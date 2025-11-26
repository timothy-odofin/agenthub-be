"""
Database configuration management.
"""

import os
from app.core.utils.single_ton import SingletonMeta
from app.core.config.config_source_registry import BaseConfigSource, register_connections


@register_connections(['postgres', 'redis', 'mongodb', 'elasticsearch'])
class DatabaseConfig(BaseConfigSource):
    """Database configuration for all database types."""
    
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
    def mongodb_config(self) -> dict:
        """MongoDB configuration"""
        return {
            'host': os.getenv('MONGODB_HOST', 'localhost'),
            'port': int(os.getenv('MONGODB_PORT', '27017')),
            'database': os.getenv('MONGODB_DATABASE', 'agenthub'),
            'username': os.getenv('MONGODB_USERNAME'),
            'password': os.getenv('MONGODB_PASSWORD'),
            'connection_string': os.getenv('MONGODB_CONNECTION_STRING', 
                f"mongodb://{os.getenv('MONGODB_HOST', 'localhost')}:{os.getenv('MONGODB_PORT', '27017')}")
        }
    
    @property
    def elasticsearch_config(self) -> dict:
        """Elasticsearch configuration"""
        return {
            'host': os.getenv('ELASTICSEARCH_HOST', 'localhost'),
            'port': int(os.getenv('ELASTICSEARCH_PORT', '9200')),
            'username': os.getenv('ELASTICSEARCH_USERNAME'),
            'password': os.getenv('ELASTICSEARCH_PASSWORD'),
            'use_ssl': os.getenv('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true',
            'verify_certs': os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'false').lower() == 'true',
            'index_prefix': os.getenv('ELASTICSEARCH_INDEX_PREFIX', 'agenthub')
        }
    
    def get_connection_config(self, connection_name: str) -> dict:
        """
        Get configuration for a specific database connection.
        
        Args:
            connection_name: Name of the database connection
            
        Returns:
            Dict with database configuration
            
        Raises:
            KeyError: If connection name not found
        """
        config_map = {
            'postgres': self.postgres_config,
            'redis': self.redis_config,
            'mongodb': self.mongodb_config,
            'elasticsearch': self.elasticsearch_config
        }
        
        if connection_name not in config_map:
            available = list(config_map.keys())
            raise KeyError(f"Database connection '{connection_name}' not found. Available: {available}")
        
        return config_map[connection_name]


# Create singleton instance
database_config = DatabaseConfig()
