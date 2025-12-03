"""
Factory for creating session repository instances.
"""

from enum import Enum
from typing import Type
from app.sessions.repositories.base_session_repository import BaseSessionRepository


class SessionRepositoryType(str, Enum):
    """Supported session repository types."""
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    REDIS = "redis"


class SessionRepositoryFactory:
    """Factory for creating session repository instances."""
    
    _repositories = {}
    
    @classmethod
    def register_repository(cls, repo_type: SessionRepositoryType, repo_class: Type[BaseSessionRepository]):
        """Register a session repository class."""
        cls._repositories[repo_type] = repo_class
    
    @classmethod
    def create_repository(cls, repo_type: SessionRepositoryType = SessionRepositoryType.POSTGRES) -> BaseSessionRepository:
        """
        Create a session repository instance.
        
        Args:
            repo_type: Type of repository to create
            
        Returns:
            Session repository instance
            
        Raises:
            ValueError: If repository type is not registered
        """
        if repo_type not in cls._repositories:
            available = list(cls._repositories.keys())
            raise ValueError(f"Session repository '{repo_type}' not registered. Available: {available}")
        
        repo_class = cls._repositories[repo_type]
        return repo_class()
    
    @classmethod
    def get_default_repository(cls) -> BaseSessionRepository:
        """Get the default session repository."""
        # You can make this configurable via environment variables
        import os
        default_type = os.getenv('SESSION_REPOSITORY_TYPE', SessionRepositoryType.POSTGRES.value)
        return cls.create_repository(SessionRepositoryType(default_type))


# Register available repositories
def _register_repositories():
    """Register all available session repositories."""
    try:
        from .postgres_session_repository import PostgresSessionRepository
        SessionRepositoryFactory.register_repository(SessionRepositoryType.POSTGRES, PostgresSessionRepository)
    except ImportError:
        pass
    
    try:
        from .mongo_session_repository import MongoSessionRepository
        SessionRepositoryFactory.register_repository(SessionRepositoryType.MONGODB, MongoSessionRepository)
    except ImportError:
        pass

    # Register Redis repository when implemented
    # try:
    #     from .redis_session_repository import RedisSessionRepository
    #     SessionRepositoryFactory.register_repository(SessionRepositoryType.REDIS, RedisSessionRepository)
    # except ImportError:
    #     pass

# Auto-register on import
_register_repositories()
