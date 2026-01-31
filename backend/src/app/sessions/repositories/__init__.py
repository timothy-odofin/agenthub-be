"""
Session repositories package initialization.
"""

from app.core.utils.dynamic_import import import_providers

# Repository modules configuration: (module_name, class_name)
REPOSITORY_MODULES = [
    ('postgres_session_repository', 'PostgresSessionRepository'),
    ('mongo_session_repository', 'MongoSessionRepository'),
    ('redis_session_repository', 'RedisSessionRepository'),
]

# Import repositories using the generic utility
__all__ = import_providers(__name__, REPOSITORY_MODULES, globals())