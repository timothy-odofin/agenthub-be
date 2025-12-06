"""
Database configuration management with strict validation.

All database configurations require explicit environment variables.
No hardcoded defaults to ensure proper configuration in all environments.
"""

import os
from typing import Dict, Any, Optional

from app.core.config.config_source_registry import BaseConfigSource, register_connections


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or missing."""
    pass


@register_connections(['postgres', 'redis', 'mongodb'])
class DatabaseConfig(BaseConfigSource):
    """Database configuration for all database types with strict validation."""
    
    def _get_required_env(self, key: str, description: str = None) -> str:
        """Get required environment variable or raise error."""
        value = os.getenv(key)
        if not value:
            desc = description or f"environment variable {key}"
            raise DatabaseConfigError(f"Missing required {desc}. Please set {key} environment variable.")
        return value
    
    def _get_optional_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get optional environment variable."""
        return os.getenv(key, default)
    
    def _get_int_env(self, key: str, description: str = None) -> int:
        """Get required integer environment variable."""
        value = self._get_required_env(key, description)
        try:
            return int(value)
        except ValueError:
            desc = description or f"environment variable {key}"
            raise DatabaseConfigError(f"Invalid {desc}: '{value}' is not a valid integer.")
    
    @property
    def postgres_config(self) -> Dict[str, Any]:
        """
        PostgreSQL database configuration.
        
        Required environment variables:
        - POSTGRES_USER: Database username
        - POSTGRES_PASSWORD: Database password  
        - POSTGRES_HOST: Database host
        - POSTGRES_PORT: Database port
        - POSTGRES_DB: Database name
        """
        username = self._get_required_env('POSTGRES_USER', 'PostgreSQL username')
        password = self._get_required_env('POSTGRES_PASSWORD', 'PostgreSQL password')
        host = self._get_required_env('POSTGRES_HOST', 'PostgreSQL host')
        port = self._get_int_env('POSTGRES_PORT', 'PostgreSQL port')
        database = self._get_required_env('POSTGRES_DB', 'PostgreSQL database name')
        
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        return {
            'username': username,
            'password': password,
            'database': database,
            'host': host,
            'port': port,
            'connection_string': connection_string
        }
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """
        Redis configuration.
        
        Required environment variables:
        - REDIS_HOST: Redis host
        - REDIS_PORT: Redis port
        
        Optional environment variables:
        - REDIS_PASSWORD: Redis password (if auth enabled)
        - REDIS_DB: Redis database number (defaults to 0)
        """
        host = self._get_required_env('REDIS_HOST', 'Redis host')
        port = self._get_int_env('REDIS_PORT', 'Redis port')
        password = self._get_optional_env('REDIS_PASSWORD')
        db = int(self._get_optional_env('REDIS_DB', '0'))
        
        # Build URL with or without password
        if password:
            url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            url = f"redis://{host}:{port}/{db}"
        
        return {
            'host': host,
            'port': port,
            'password': password,
            'db': db,
            'url': url
        }
    
    @property
    def mongodb_config(self) -> Dict[str, Any]:
        """
        MongoDB configuration.
        
        Option 1 - Custom connection string (for Atlas, etc.):
        - MONGODB_CONNECTION_STRING: Full connection string
        - MONGODB_DATABASE: Database name
        
        Option 2 - Individual components (for local/Docker):
        - MONGODB_HOST: MongoDB host
        - MONGODB_PORT: MongoDB port
        - MONGODB_USERNAME: MongoDB username
        - MONGODB_PASSWORD: MongoDB password
        - MONGODB_DATABASE: Database name
        """
        # Check for custom connection string first (Atlas, cloud providers)
        custom_connection_string = self._get_optional_env('MONGODB_CONNECTION_STRING')
        database = self._get_required_env('MONGODB_DATABASE', 'MongoDB database name')
        
        if custom_connection_string:
            # Using custom connection string (Atlas, etc.)
            password = self._get_optional_env('MONGODB_PASSWORD')
            
            # Replace password placeholder if present
            if password and '<db_password>' in custom_connection_string:
                connection_string = custom_connection_string.replace('<db_password>', password)
            else:
                connection_string = custom_connection_string
            
            # Extract info from connection string for reference
            is_atlas = '+srv://' in connection_string
            
            return {
                'database': database,
                'connection_string': connection_string,
                'is_atlas': is_atlas,
                'is_local': not is_atlas,
                'host': 'atlas' if is_atlas else 'custom',
                'port': 27017,
                'username': None,
                'password': password
            }
        
        else:
            # Using individual components (local/Docker setup)
            host = self._get_required_env('MONGODB_HOST', 'MongoDB host')
            port = self._get_int_env('MONGODB_PORT', 'MongoDB port')
            username = self._get_required_env('MONGODB_USERNAME', 'MongoDB username')
            password = self._get_required_env('MONGODB_PASSWORD', 'MongoDB password')
            
            # Build connection string with auth
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource=admin"
            
            return {
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'password': password,
                'connection_string': connection_string,
                'is_atlas': False,
                'is_local': True
            }
    
    @property
    def elasticsearch_config(self) -> Dict[str, Any]:
        """
        Elasticsearch configuration.
        
        Required environment variables:
        - ELASTICSEARCH_HOST: Elasticsearch host
        - ELASTICSEARCH_PORT: Elasticsearch port
        
        Optional environment variables:
        - ELASTICSEARCH_USERNAME: Username (if auth enabled)
        - ELASTICSEARCH_PASSWORD: Password (if auth enabled)
        - ELASTICSEARCH_USE_SSL: Enable SSL (true/false, defaults to false)
        - ELASTICSEARCH_VERIFY_CERTS: Verify SSL certs (true/false, defaults to false)
        - ELASTICSEARCH_INDEX_PREFIX: Index prefix for application (defaults to 'agenthub')
        """
        # host = self._get_required_env('ELASTICSEARCH_HOST', 'Elasticsearch host')
        # port = self._get_int_env('ELASTICSEARCH_PORT', 'Elasticsearch port')
        
        # username = self._get_optional_env('ELASTICSEARCH_USERNAME')
        # password = self._get_optional_env('ELASTICSEARCH_PASSWORD')
        # use_ssl = self._get_optional_env('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true'
        # verify_certs = self._get_optional_env('ELASTICSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
        # index_prefix = self._get_optional_env('ELASTICSEARCH_INDEX_PREFIX', 'agenthub')
        
        return {
            'host': "host",
            'port': "port",
            'username': "username",
            'password': "password",
            'use_ssl': "use_ssl",
            'verify_certs': "verify_certs",
            'index_prefix': "index_prefix"
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
