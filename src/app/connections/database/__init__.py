"""
Database connection managers.
"""

from app.core.utils.dynamic_import import import_providers

# Database connection modules configuration: (module_name, class_name)
DATABASE_CONNECTION_MODULES = [
    ('postgres_connection_manager', 'PostgresConnectionManager'),
    ('redis_connection_manager', 'RedisConnectionManager'),
    ('mongodb_connection_manager', 'MongoDBConnectionManager'),
]

# Import database connection managers using the generic utility
__all__ = import_providers(__name__, DATABASE_CONNECTION_MODULES, globals(), suppress_warnings=True)