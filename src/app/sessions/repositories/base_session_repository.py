from abc import abstractmethod, ABC

from app.sessions.models.message import ChatMessage
from app.sessions.models.session import ChatSession


class BaseSessionRepository(ABC):
    """Base class for session repositories"""
    def __init__(self):
     self.connection = None
     self.load_and_validate_connection()
    @abstractmethod
    def load_and_validate_connection(self):
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
