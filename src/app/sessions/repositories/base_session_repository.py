from abc import abstractmethod, ABC
from typing import Optional

from app.sessions.models.message import ChatMessage
from app.sessions.models.session import ChatSession
from app.connections.factory.connection_factory import ConnectionFactory
from app.connections.base import ConnectionType


class BaseSessionRepository(ABC):
    """Base class for session repositories with centralized connection management"""
    
    def __init__(self, connection_type: ConnectionType):
        self.connection_type = connection_type
        self._connection_manager = None
        self._connection = None
        self.load_and_validate_connection()
    
    def load_and_validate_connection(self):
        """Load and validate connection based on connection type."""
        self._connection_manager = ConnectionFactory.get_connection_manager(self.connection_type)
    
    async def _ensure_connection(self):
        """Ensure database connection and create tables if needed."""
        if self._connection is None:
            self._connection = await self._connection_manager.connect()
            await self._create_tables_if_not_exist()
        return self._connection
    
    @abstractmethod
    async def _create_tables_if_not_exist(self):
        """Create tables/collections specific to the database type."""
        pass
    @abstractmethod
    async def _create_tables_if_not_exist(self):
        """Create tables/collections specific to the database type."""
        pass
    
    @abstractmethod
    def create_session(self, user_id: str, session_data: dict) -> str:
        """Create a new session for the given user and return the session ID"""
        pass

    @abstractmethod
    async def get_session_history(self, user_id: str, session_id: str) -> list[ChatMessage]:
        """Retrieve the chat history for a given session ID"""
        pass

    @abstractmethod
    def update_session(self, user_id, session_id: str, data: dict) -> bool:
        """Update session data for the given session ID"""
        pass
    
    @abstractmethod
    def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> list[ChatSession]:
        """List sessions for the given user with pagination"""
        pass
    
    @abstractmethod
    def delete_session(self, user_id, session_id: str) -> bool:
        """Delete the session with the given session ID"""
        pass
    
    @abstractmethod
    async def add_message(self, session_id: str, role: str, content: str) -> str:
        """Add a message to a session."""
        pass
