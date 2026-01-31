"""
Unit tests for SessionRepositoryFactory and related components.

Tests the session repository factory system including:
- Repository type enumeration
- Registry decorator pattern
- Factory creation methods
- Error handling and validation
- Default repository selection
- Dynamic import and registration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Type, Dict
from enum import Enum

from app.sessions.repositories.session_repository_factory import (
    SessionRepositoryType,
    SessionRepositoryRegistry,
    SessionRepositoryFactory,
    register_repository
)
from app.sessions.repositories.base_session_repository import BaseSessionRepository
from app.sessions.models.message import ChatMessage
from app.sessions.models.session import ChatSession


class TestSessionRepositoryType:
    """Test the SessionRepositoryType enumeration."""
    
    def test_enum_values_are_correct(self):
        """Test that enum values match expected repository types."""
        assert SessionRepositoryType.POSTGRES == "postgres"
        assert SessionRepositoryType.MONGODB == "mongodb" 
        assert SessionRepositoryType.REDIS == "redis"
    
    def test_enum_is_string_subclass(self):
        """Test that SessionRepositoryType is a string enum."""
        assert issubclass(SessionRepositoryType, str)
        assert issubclass(SessionRepositoryType, Enum)
    
    def test_enum_membership(self):
        """Test enum membership and iteration."""
        repo_types = list(SessionRepositoryType)
        assert len(repo_types) == 3
        assert SessionRepositoryType.POSTGRES in repo_types
        assert SessionRepositoryType.MONGODB in repo_types
        assert SessionRepositoryType.REDIS in repo_types


class TestSessionRepositoryRegistry:
    """Test the SessionRepositoryRegistry class and decorator system."""
    
    def setup_method(self):
        """Reset registry state before each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    def teardown_method(self):
        """Clean up registry state after each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    def test_registry_initial_state(self):
        """Test that registry starts in clean state."""
        assert SessionRepositoryRegistry._repositories == {}
        assert SessionRepositoryRegistry._repositories_imported is False
    
    def test_register_repository_decorator(self):
        """Test the register_repository decorator functionality."""
        # Create a mock repository class
        class MockRepository(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "message_id"
        
        # Apply the decorator
        decorated_class = SessionRepositoryRegistry.register_repository(SessionRepositoryType.POSTGRES)(MockRepository)
        
        # Verify registration
        assert SessionRepositoryType.POSTGRES in SessionRepositoryRegistry._repositories
        assert SessionRepositoryRegistry._repositories[SessionRepositoryType.POSTGRES] is MockRepository
        assert decorated_class is MockRepository  # Decorator should return the original class
    
    def test_register_multiple_repositories(self):
        """Test registering multiple repository types."""
        class PostgresRepo(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "pg_session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "pg_message_id"
        
        class MongoRepo(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "mongo_session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "mongo_message_id"
        
        # Register both repositories
        SessionRepositoryRegistry.register_repository(SessionRepositoryType.POSTGRES)(PostgresRepo)
        SessionRepositoryRegistry.register_repository(SessionRepositoryType.MONGODB)(MongoRepo)
        
        # Verify both are registered
        assert len(SessionRepositoryRegistry._repositories) == 2
        assert SessionRepositoryRegistry._repositories[SessionRepositoryType.POSTGRES] is PostgresRepo
        assert SessionRepositoryRegistry._repositories[SessionRepositoryType.MONGODB] is MongoRepo
    
    @patch('importlib.import_module')
    def test_ensure_repositories_imported(self, mock_import):
        """Test that _ensure_repositories_imported triggers import."""
        # First call should trigger import
        SessionRepositoryRegistry._ensure_repositories_imported()
        
        assert SessionRepositoryRegistry._repositories_imported is True
        
        # Second call should not trigger import again
        mock_import.reset_mock()
        SessionRepositoryRegistry._ensure_repositories_imported()
        mock_import.assert_not_called()
    
    def test_get_repository_class_success(self):
        """Test successful repository class retrieval."""
        class TestRepo(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "test_session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "test_message_id"
        
        # Register repository
        SessionRepositoryRegistry.register_repository(SessionRepositoryType.POSTGRES)(TestRepo)
        
        # Get repository class
        retrieved_class = SessionRepositoryRegistry.get_repository_class(SessionRepositoryType.POSTGRES)
        assert retrieved_class is TestRepo
    
    def test_get_repository_class_not_found(self):
        """Test error handling when repository type is not found."""
        # Ensure no repositories are registered
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = True
        
        with pytest.raises(ValueError) as exc_info:
            SessionRepositoryRegistry.get_repository_class(SessionRepositoryType.POSTGRES)
        
        assert "Session repository 'SessionRepositoryType.POSTGRES' not found" in str(exc_info.value)
        assert "Available: []" in str(exc_info.value)
    
    def test_list_repositories(self):
        """Test listing all registered repository types."""
        class PostgresRepo(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "message_id"
        
        class RedisRepo(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "message_id"
        
        # Register repositories
        SessionRepositoryRegistry.register_repository(SessionRepositoryType.POSTGRES)(PostgresRepo)
        SessionRepositoryRegistry.register_repository(SessionRepositoryType.REDIS)(RedisRepo)
        
        # List repositories
        repo_types = SessionRepositoryRegistry.list_repositories()
        assert len(repo_types) == 2
        assert SessionRepositoryType.POSTGRES in repo_types
        assert SessionRepositoryType.REDIS in repo_types


class TestSessionRepositoryFactory:
    """Test the SessionRepositoryFactory class."""
    
    def setup_method(self):
        """Reset registry state before each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    def teardown_method(self):
        """Clean up registry state after each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    @patch('app.sessions.repositories.session_repository_factory.SessionRepositoryRegistry.get_repository_class')
    def test_create_repository_success(self, mock_get_class):
        """Test successful repository creation."""
        # Mock repository class
        mock_repo_class = Mock()
        mock_repo_instance = Mock()
        mock_repo_class.return_value = mock_repo_instance
        mock_get_class.return_value = mock_repo_class
        
        # Create repository
        result = SessionRepositoryFactory.create_repository(SessionRepositoryType.POSTGRES, test_param="test_value")
        
        # Verify calls
        mock_get_class.assert_called_once_with(SessionRepositoryType.POSTGRES)
        mock_repo_class.assert_called_once_with(test_param="test_value")
        assert result is mock_repo_instance
    
    @patch('app.sessions.repositories.session_repository_factory.SessionRepositoryRegistry.get_repository_class')
    def test_create_repository_with_kwargs(self, mock_get_class):
        """Test repository creation with keyword arguments."""
        # Mock repository class
        mock_repo_class = Mock()
        mock_repo_instance = Mock()
        mock_repo_class.return_value = mock_repo_instance
        mock_get_class.return_value = mock_repo_class
        
        # Create repository with kwargs
        kwargs = {"config": {"host": "localhost"}, "timeout": 30}
        result = SessionRepositoryFactory.create_repository(SessionRepositoryType.MONGODB, **kwargs)
        
        # Verify kwargs are passed through
        mock_get_class.assert_called_once_with(SessionRepositoryType.MONGODB)
        mock_repo_class.assert_called_once_with(**kwargs)
        assert result is mock_repo_instance
    
    @patch('app.sessions.repositories.session_repository_factory.SessionRepositoryFactory.create_repository')
    def test_get_default_repository(self, mock_create):
        """Test that default repository returns MongoDB repository."""
        mock_repository = Mock()
        mock_create.return_value = mock_repository
        
        result = SessionRepositoryFactory.get_default_repository()
        
        mock_create.assert_called_once_with(SessionRepositoryType.MONGODB)
        assert result is mock_repository
    
    def test_create_repository_integration(self):
        """Test end-to-end repository creation with real registration."""
        class TestRepo(BaseSessionRepository):
            def __init__(self, test_param=None):
                self.test_param = test_param
                # Don't call super().__init__ to avoid connection setup in test
                self.connection_type = None
                self._connection_manager = None
                self._connection = None
            
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "test_session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "test_message_id"
        
        # Register repository
        SessionRepositoryRegistry.register_repository(SessionRepositoryType.POSTGRES)(TestRepo)
        
        # Create repository instance
        repo = SessionRepositoryFactory.create_repository(SessionRepositoryType.POSTGRES, test_param="integration_test")
        
        # Verify instance
        assert isinstance(repo, TestRepo)
        assert repo.test_param == "integration_test"


class TestConvenienceDecorator:
    """Test the convenience decorator function."""
    
    def setup_method(self):
        """Reset registry state before each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    def teardown_method(self):
        """Clean up registry state after each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    def test_register_repository_convenience_decorator(self):
        """Test that the convenience decorator works the same as the registry method."""
        class TestRepo(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "session_id"
            async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            async def add_message(self, session_id: str, role: str, content: str) -> str:
                return "message_id"
        
        # Use convenience decorator
        decorated_class = register_repository(SessionRepositoryType.MONGODB)(TestRepo)
        
        # Verify it works the same way
        assert decorated_class is TestRepo
        assert SessionRepositoryType.MONGODB in SessionRepositoryRegistry._repositories
        assert SessionRepositoryRegistry._repositories[SessionRepositoryType.MONGODB] is TestRepo
    
    def test_decorator_import_alias(self):
        """Test that the convenience decorator is properly aliased."""
        # Verify the alias points to the correct method (they are the same function reference)
        assert register_repository == SessionRepositoryRegistry.register_repository


class TestSessionRepositoryFactoryErrorHandling:
    """Test error handling scenarios in the factory system."""
    
    def setup_method(self):
        """Reset registry state before each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    def teardown_method(self):
        """Clean up registry state after each test."""
        SessionRepositoryRegistry._repositories = {}
        SessionRepositoryRegistry._repositories_imported = False
    
    def test_factory_creation_with_unregistered_type(self):
        """Test that creating unregistered repository type raises appropriate error."""
        # Ensure registry is empty
        SessionRepositoryRegistry._repositories_imported = True
        
        with pytest.raises(ValueError) as exc_info:
            SessionRepositoryFactory.create_repository(SessionRepositoryType.POSTGRES)
        
        assert "Session repository 'SessionRepositoryType.POSTGRES' not found" in str(exc_info.value)
    
    @patch('app.sessions.repositories.session_repository_factory.SessionRepositoryRegistry.get_repository_class')
    def test_factory_creation_with_initialization_error(self, mock_get_class):
        """Test handling of repository initialization errors."""
        # Mock repository class that raises exception during init
        mock_repo_class = Mock()
        mock_repo_class.side_effect = Exception("Repository initialization failed")
        mock_get_class.return_value = mock_repo_class
        
        with pytest.raises(Exception, match="Repository initialization failed"):
            SessionRepositoryFactory.create_repository(SessionRepositoryType.POSTGRES)
        
        mock_get_class.assert_called_once_with(SessionRepositoryType.POSTGRES)
        mock_repo_class.assert_called_once()
    
    def test_registry_with_invalid_repository_class(self):
        """Test registering invalid repository class."""
        # Try to register a class that doesn't inherit from BaseSessionRepository
        class InvalidRepo:
            pass
        
        # This should work (registration happens at runtime)
        # The error would occur when trying to use the repository
        decorator = SessionRepositoryRegistry.register_repository(SessionRepositoryType.POSTGRES)
        decorated_class = decorator(InvalidRepo)
        
        assert decorated_class is InvalidRepo
        assert SessionRepositoryRegistry._repositories[SessionRepositoryType.POSTGRES] is InvalidRepo
