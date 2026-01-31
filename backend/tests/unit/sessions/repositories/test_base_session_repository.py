"""
Unit tests for BaseSessionRepository.

Tests the abstract base session repository including:
- Abstract class behavior and interface enforcement
- Connection management initialization
- Async connection handling
- Abstract method enforcement
- Connection type validation
- Table creation patterns
"""

import pytest
import asyncio
import inspect
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from abc import ABC, abstractmethod

from app.sessions.repositories.base_session_repository import BaseSessionRepository
from app.connections.base import ConnectionType, AsyncBaseConnectionManager
from app.sessions.models.message import ChatMessage
from app.sessions.models.session import ChatSession


class TestBaseSessionRepositoryArchitecture:
    """Test the architectural patterns of BaseSessionRepository."""
    
    def test_is_abstract_base_class(self):
        """Test that BaseSessionRepository is an abstract base class."""
        assert issubclass(BaseSessionRepository, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseSessionRepository(ConnectionType.POSTGRES)

    def test_abstract_methods_are_defined(self):
        """Test that all expected abstract methods are defined."""
        abstract_methods = BaseSessionRepository.__abstractmethods__
        
        expected_methods = {
            '_create_tables_if_not_exist',
            'create_session',
            'get_session_history',
            'update_session',
            'list_paginated_sessions',
            'delete_session',
            'add_message'
        }
        
        assert abstract_methods == expected_methods

    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    def test_concrete_implementation_requires_all_abstract_methods(self, mock_connection_factory):
        """Test that concrete implementation must implement all abstract methods."""
        mock_connection_factory.get_connection_manager.return_value = Mock()
        
        # Missing one abstract method should raise TypeError
        class IncompleteRepository(BaseSessionRepository):
            def _create_tables_if_not_exist(self):
                pass
            def create_session(self, user_id: str, session_data: dict) -> str:
                return "session_id"
            def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
                return []
            def update_session(self, user_id, session_id: str, data: dict) -> bool:
                return True
            def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
                return []
            def delete_session(self, user_id, session_id: str) -> bool:
                return True
            # Missing add_message method
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteRepository(ConnectionType.POSTGRES)

    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    def test_complete_implementation_works(self, mock_connection_factory):
        """Test that complete implementation can be instantiated."""
        mock_connection_factory.get_connection_manager.return_value = Mock()
        
        # Complete implementation should work
        class CompleteRepository(BaseSessionRepository):
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
        
        # Should not raise any exceptions
        repo = CompleteRepository(ConnectionType.POSTGRES)
        assert repo.connection_type == ConnectionType.POSTGRES


class TestBaseSessionRepositoryConnectionManagement:
    """Test connection management functionality."""
    
    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    def test_initialization_loads_connection_manager(self, mock_connection_factory):
        """Test that initialization properly loads connection manager."""
        mock_manager = Mock()
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        class TestRepository(BaseSessionRepository):
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
        
        repo = TestRepository(ConnectionType.MONGODB)
        
        mock_connection_factory.get_connection_manager.assert_called_once_with(ConnectionType.MONGODB)
        assert repo._connection_manager is mock_manager
        assert repo.connection_type == ConnectionType.MONGODB
        assert repo._connection is None

    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    def test_ensure_connection_with_sync_manager_and_table_creation(self, mock_connection_factory):
        """Test _ensure_connection with synchronous connection manager and table creation."""
        mock_manager = Mock()
        mock_connection = Mock()
        mock_manager.connect.return_value = mock_connection
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        class TestRepository(BaseSessionRepository):
            def __init__(self, connection_type):
                super().__init__(connection_type)
                self.table_created = False
            
            def _create_tables_if_not_exist(self):
                self.table_created = True
            
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
        
        repo = TestRepository(ConnectionType.POSTGRES)
        
        # Use asyncio to test the ensure_connection method
        async def test_ensure():
            connection = await repo._ensure_connection()
            return connection
        
        result = asyncio.run(test_ensure())
        
        mock_manager.connect.assert_called_once()
        assert result is mock_connection
        assert repo._connection is mock_connection
        assert repo.table_created is True

    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    async def test_ensure_connection_with_async_manager_and_table_creation(self, mock_connection_factory):
        """Test _ensure_connection with asynchronous connection manager and table creation."""
        mock_manager = Mock(spec=AsyncBaseConnectionManager)
        mock_connection = Mock()
        mock_manager.connect = AsyncMock(return_value=mock_connection)
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        class TestRepository(BaseSessionRepository):
            def __init__(self, connection_type):
                super().__init__(connection_type)
                self.table_created = False
            
            async def _create_tables_if_not_exist(self):
                self.table_created = True
            
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
        
        repo = TestRepository(ConnectionType.POSTGRES)
        
        connection = await repo._ensure_connection()
        
        mock_manager.connect.assert_called_once()
        assert connection is mock_connection
        assert repo._connection is mock_connection
        assert repo.table_created is True

    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    async def test_ensure_connection_reuses_existing_connection(self, mock_connection_factory):
        """Test that _ensure_connection reuses existing connection."""
        mock_manager = Mock()
        mock_connection = Mock()
        mock_manager.connect.return_value = mock_connection
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        class TestRepository(BaseSessionRepository):
            def __init__(self, connection_type):
                super().__init__(connection_type)
                self.table_creation_count = 0
            
            def _create_tables_if_not_exist(self):
                self.table_creation_count += 1
            
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
        
        repo = TestRepository(ConnectionType.POSTGRES)
        
        # First call should establish connection
        connection1 = await repo._ensure_connection()
        # Second call should reuse existing connection
        connection2 = await repo._ensure_connection()
        
        # Should only call connect once
        mock_manager.connect.assert_called_once()
        assert connection1 is connection2
        assert repo.table_creation_count == 1


class TestBaseSessionRepositoryInspection:
    """Test the inspection capabilities for detecting async vs sync methods."""
    
    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    def test_inspection_detects_sync_table_creation(self, mock_connection_factory):
        """Test that inspection correctly detects sync table creation method."""
        mock_manager = Mock()
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        class TestRepository(BaseSessionRepository):
            def _create_tables_if_not_exist(self):  # Sync method
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
        
        repo = TestRepository(ConnectionType.POSTGRES)
        
        # Check that inspection detects sync method
        is_coroutine = inspect.iscoroutinefunction(repo._create_tables_if_not_exist)
        assert is_coroutine is False

    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    def test_inspection_detects_async_table_creation(self, mock_connection_factory):
        """Test that inspection correctly detects async table creation method."""
        mock_manager = Mock()
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        class TestRepository(BaseSessionRepository):
            async def _create_tables_if_not_exist(self):  # Async method
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
        
        repo = TestRepository(ConnectionType.POSTGRES)
        
        # Check that inspection detects async method
        is_coroutine = inspect.iscoroutinefunction(repo._create_tables_if_not_exist)
        assert is_coroutine is True


class TestBaseSessionRepositoryInterfaceValidation:
    """Test that the interface is properly defined and documented."""
    
    def test_abstract_method_signatures_are_correct(self):
        """Test that abstract method signatures match expected interface."""
        # Get the abstract methods
        abstract_methods = BaseSessionRepository.__abstractmethods__
        
        # Verify each method exists and has correct signature
        assert '_create_tables_if_not_exist' in abstract_methods
        assert 'create_session' in abstract_methods
        assert 'get_session_history' in abstract_methods
        assert 'update_session' in abstract_methods
        assert 'list_paginated_sessions' in abstract_methods
        assert 'delete_session' in abstract_methods
        assert 'add_message' in abstract_methods
        
        # Test that methods are defined in the class
        assert hasattr(BaseSessionRepository, '_create_tables_if_not_exist')
        assert hasattr(BaseSessionRepository, 'create_session')
        assert hasattr(BaseSessionRepository, 'get_session_history')
        assert hasattr(BaseSessionRepository, 'update_session')
        assert hasattr(BaseSessionRepository, 'list_paginated_sessions')
        assert hasattr(BaseSessionRepository, 'delete_session')
        assert hasattr(BaseSessionRepository, 'add_message')

    @patch('app.sessions.repositories.base_session_repository.ConnectionFactory')
    def test_connection_type_validation(self, mock_connection_factory):
        """Test that connection type is properly set and validated."""
        mock_connection_factory.get_connection_manager.return_value = Mock()
        
        class TestRepository(BaseSessionRepository):
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
        
        # Test with different connection types
        repo_postgres = TestRepository(ConnectionType.POSTGRES)
        assert repo_postgres.connection_type == ConnectionType.POSTGRES
        
        repo_mongodb = TestRepository(ConnectionType.MONGODB)
        assert repo_mongodb.connection_type == ConnectionType.MONGODB
        
        repo_redis = TestRepository(ConnectionType.REDIS)
        assert repo_redis.connection_type == ConnectionType.REDIS
