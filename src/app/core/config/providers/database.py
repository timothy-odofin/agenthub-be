"""
Database configuration management using Settings system.
"""

from typing import Dict, Any

from ..framework.registry import BaseConfigSource, register_config
from ..framework.settings import settings


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or missing."""
    pass


@register_config(['postgres', 'redis', 'mongodb'])
class DatabaseConfig(BaseConfigSource):
    """Database configuration for all database types using Settings system."""
    
    @property
    def postgres_config(self) -> Dict[str, Any]:
        """
        PostgreSQL database configuration using Settings system.
        """
        if not hasattr(settings, 'db') or not hasattr(settings.db, 'postgres'):
            return {}
            
        postgres = settings.db.postgres
        
        # Build connection string
        connection_string = f"postgresql://{postgres.username}:{postgres.password}@{postgres.host}:{postgres.port}/{postgres.database}"
        
        return {
            'username': postgres.username,
            'password': postgres.password,
            'database': postgres.database,
            'host': postgres.host,
            'port': postgres.port,
            'connection_string': connection_string
        }
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """
        Redis configuration using Settings system.
        """
        if not hasattr(settings, 'db') or not hasattr(settings.db, 'redis'):
            return {}
            
        redis = settings.db.redis
        
        # Get database number (use 'db' field)
        db_num = redis.db if hasattr(redis, 'db') else 0
        
        # Get SSL setting
        ssl_enabled = redis.ssl if hasattr(redis, 'ssl') else False
        
        # Build URL with or without password
        if redis.password:
            url = f"redis://:{redis.password}@{redis.host}:{redis.port}/{db_num}"
        else:
            url = f"redis://{redis.host}:{redis.port}/{db_num}"
        
        return {
            'host': redis.host,
            'port': redis.port,
            'password': redis.password,
            'db': db_num,
            'ssl': ssl_enabled,
            'url': url
        }
    
    @property
    def mongodb_config(self) -> Dict[str, Any]:
        """
        MongoDB configuration using Settings system.
        
        Supports both custom connection string (Atlas) and individual components (local/Docker).
        """
        if not hasattr(settings, 'db') or not hasattr(settings.db, 'mongodb'):
            return {}
            
        mongodb = settings.db.mongodb
        
        # Check for custom connection string first (Atlas, cloud providers)
        if hasattr(mongodb, 'connection_string') and mongodb.connection_string:
            connection_string = mongodb.connection_string
            
            # Replace password placeholder if present
            if hasattr(mongodb, 'password') and mongodb.password and '<db_password>' in connection_string:
                connection_string = connection_string.replace('<db_password>', mongodb.password)
            
            # Extract info from connection string for reference
            is_atlas = '+srv://' in connection_string
            
            return {
                'database': mongodb.database,
                'connection_string': connection_string,
                'is_atlas': is_atlas,
                'is_local': not is_atlas,
                'host': 'atlas' if is_atlas else 'custom',
                'port': getattr(mongodb, 'port', 27017),
                'username': getattr(mongodb, 'username', None),
                'password': getattr(mongodb, 'password', None)
            }
        
        else:
            # Using individual components (local/Docker setup)
            connection_string = f"mongodb://{mongodb.username}:{mongodb.password}@{mongodb.host}:{mongodb.port}/{mongodb.database}?authSource=admin"
            
            return {
                'host': mongodb.host,
                'port': mongodb.port,
                'database': mongodb.database,
                'username': mongodb.username,
                'password': mongodb.password,
                'connection_string': connection_string,
                'is_atlas': False,
                'is_local': True
            }
    
    @property
    def elasticsearch_config(self) -> Dict[str, Any]:
        """
        Elasticsearch configuration using Settings system.
        """
        if not hasattr(settings, 'db') or not hasattr(settings.db, 'elasticsearch'):
            return {}
            
        elasticsearch = settings.db.elasticsearch
        
        return {
            'host': elasticsearch.host,
            'port': elasticsearch.port,
            'username': getattr(elasticsearch, 'username', None),
            'password': getattr(elasticsearch, 'password', None),
            'use_ssl': getattr(elasticsearch, 'use_ssl', False),
            'verify_certs': getattr(elasticsearch, 'verify_certs', False),
            'index_prefix': getattr(elasticsearch, 'index_prefix', 'agenthub')
        }
    
    def get_connection_config(self, connection_name: str) -> dict:
        """
        Get configuration for a specific database connection.
        
        Args:
            connection_name: Name of the database connection
            
        Returns:
            Dict with database configuration or empty dict if not found
        """
        config_map = {
            'postgres': self.postgres_config,
            'redis': self.redis_config,
            'mongodb': self.mongodb_config,
            'elasticsearch': self.elasticsearch_config
        }
        
        return config_map.get(connection_name, {})


# Create singleton instance
database_config = DatabaseConfig()
