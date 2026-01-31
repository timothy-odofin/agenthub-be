"""
Factory for creating session repository instances using decorator-based registration.
"""

from enum import Enum
from typing import Type, Dict, Any, List
from app.sessions.repositories.base_session_repository import BaseSessionRepository


class SessionRepositoryType(str, Enum):
    """Supported session repository types."""
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    REDIS = "redis"


class SessionRepositoryRegistry:
    """Registry that maps session repository types to their implementations using decorators."""
    
    _repositories: Dict[SessionRepositoryType, Type[BaseSessionRepository]] = {}
    _repositories_imported: bool = False
    
    @classmethod
    def register_repository(cls, repo_type: SessionRepositoryType):
        """
        Decorator to register a session repository class.
        
        Usage:
            @SessionRepositoryRegistry.register_repository(SessionRepositoryType.POSTGRES)
            class PostgresSessionRepository(BaseSessionRepository):
                # Implementation
        
        Args:
            repo_type: The repository type this class handles
            
        Returns:
            Decorator function
        """
        def decorator(repo_class):
            # Register the repository class
            cls._repositories[repo_type] = repo_class
            return repo_class
        
        return decorator
    
    @classmethod
    def _ensure_repositories_imported(cls):
        """Ensure all repositories are imported for registration."""
        if cls._repositories_imported:
            return
            
        # Import repositories module to trigger registration
        import app.sessions.repositories
        cls._repositories_imported = True
    
    @classmethod
    def get_repository_class(cls, repo_type: SessionRepositoryType) -> Type[BaseSessionRepository]:
        """Get a repository class by type."""
        # Import repositories to ensure registration
        cls._ensure_repositories_imported()
        
        if repo_type not in cls._repositories:
            available = list(cls._repositories.keys())
            raise ValueError(f"Session repository '{repo_type}' not found. Available: {available}")
            
        return cls._repositories[repo_type]
    
    @classmethod
    def list_repositories(cls) -> List[SessionRepositoryType]:
        """List all registered repository types."""
        # Import repositories to ensure registration
        cls._ensure_repositories_imported()
        return list(cls._repositories.keys())


class SessionRepositoryFactory:
    """Factory for creating session repository instances."""
    
    @staticmethod
    def create_repository(repo_type: SessionRepositoryType, **kwargs) -> BaseSessionRepository:
        """
        Create a session repository instance.
        
        Args:
            repo_type: Type of repository to create
            **kwargs: Additional parameters for repository initialization
            
        Returns:
            Session repository instance
        """
        repository_class = SessionRepositoryRegistry.get_repository_class(repo_type)
        return repository_class(**kwargs)
    
    @staticmethod
    def get_default_repository() -> BaseSessionRepository:
        """
        Get the default session repository (currently PostgreSQL).
        
        Returns:
            Default session repository instance
        """
        return SessionRepositoryFactory.create_repository(SessionRepositoryType.MONGODB)


# Create convenience decorator for cleaner imports
register_repository = SessionRepositoryRegistry.register_repository
