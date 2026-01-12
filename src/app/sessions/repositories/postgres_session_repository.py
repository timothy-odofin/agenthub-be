"""
PostgreSQL session repository implementation.
"""

import uuid
from typing import List
from app.sessions.repositories.base_session_repository import BaseSessionRepository
from app.sessions.models.session import ChatSession
from app.sessions.models.message import ChatMessage
from app.connections.base import ConnectionType
from app.sessions.repositories.session_repository_factory import register_repository, SessionRepositoryType


@register_repository(SessionRepositoryType.POSTGRES)
class PostgresSessionRepository(BaseSessionRepository):
    """PostgreSQL implementation of session repository."""
    
    def __init__(self):
        # Pass ConnectionType.POSTGRES to parent for centralized connection management
        super().__init__(ConnectionType.POSTGRES)
    
    async def _create_tables_if_not_exist(self):
        """Create session and message tables if they don't exist."""
        
        # Create sessions table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id UUID PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create messages table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id UUID PRIMARY KEY,
                session_id UUID REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages(session_id);
        """)
    
    def create_session(self, user_id: str, session_data: dict) -> str:
        """Create a new session for the given user and return the session ID"""
        session_id = str(uuid.uuid4())
        
        # This should be async in real implementation
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._create_session_async(session_id, user_id, session_data))
        
        return session_id
    
    async def _create_session_async(self, session_id: str, user_id: str, session_data: dict):
        """Async implementation of session creation."""
        await self._ensure_connection()
        
        await self._connection.execute("""
            INSERT INTO chat_sessions (session_id, title, user_id, metadata)
            VALUES ($1, $2, $3, $4)
        """, 
        uuid.UUID(session_id),
        session_data.get('title', 'New Chat'),
        user_id,
        session_data.get('metadata', {})
        )
    
    def get_session(self, user_id: str, session_id: str) -> ChatSession:
        """
        Retrieve a single session by ID for the given user.
        
        Returns:
            ChatSession object if found, None otherwise
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_session_async(user_id, session_id))
    
    async def _get_session_async(self, user_id: str, session_id: str) -> ChatSession:
        """Async implementation of get_session."""
        await self._ensure_connection()
        
        session = await self._connection.fetchrow("""
            SELECT session_id, title, user_id, created_at, updated_at, metadata
            FROM chat_sessions
            WHERE session_id = $1 AND user_id = $2
        """, uuid.UUID(session_id), user_id)
        
        if not session:
            return None
        
        return ChatSession(
            session_id=str(session['session_id']),
            title=session['title'],
            user_id=session['user_id'],
            created_at=session['created_at'],
            updated_at=session['updated_at'],
            metadata=session['metadata']
        )
    
    def get_session_messages(self, user_id: str, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """
        Retrieve messages for a session with optional limit.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum number of messages to retrieve (default 100)
        
        Returns:
            List of ChatMessage objects, ordered by timestamp
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_session_messages_async(user_id, session_id, limit))
    
    async def _get_session_messages_async(self, user_id: str, session_id: str, limit: int) -> List[ChatMessage]:
        """Async implementation of get_session_messages."""
        await self._ensure_connection()
        
        # Verify session belongs to user
        session_check = await self._connection.fetchrow("""
            SELECT session_id FROM chat_sessions 
            WHERE session_id = $1 AND user_id = $2
        """, uuid.UUID(session_id), user_id)
        
        if not session_check:
            return []
        
        # Get messages with limit
        messages = await self._connection.fetch("""
            SELECT message_id, session_id, role, content, timestamp
            FROM chat_messages
            WHERE session_id = $1
            ORDER BY timestamp ASC
            LIMIT $2
        """, uuid.UUID(session_id), limit)
        
        return [
            ChatMessage(
                message_id=str(msg['message_id']),
                session_id=str(msg['session_id']),
                role=msg['role'],
                content=msg['content'],
                timestamp=msg['timestamp']
            )
            for msg in messages
        ]
    
    async def get_session_history(self, user_id: str, session_id: str) -> List[ChatMessage]:
        """Retrieve the chat history for a given session ID"""
        await self._ensure_connection()
        
        # Verify session belongs to user
        session_check = await self._connection.fetchrow("""
            SELECT session_id FROM chat_sessions 
            WHERE session_id = $1 AND user_id = $2
        """, uuid.UUID(session_id), user_id)
        
        if not session_check:
            return []
        
        # Get messages
        messages = await self._connection.fetch("""
            SELECT message_id, session_id, role, content, timestamp
            FROM chat_messages
            WHERE session_id = $1
            ORDER BY timestamp ASC
        """, uuid.UUID(session_id))
        
        return [
            ChatMessage(
                message_id=str(msg['message_id']),
                session_id=str(msg['session_id']),
                role=msg['role'],
                content=msg['content'],
                timestamp=msg['timestamp']
            )
            for msg in messages
        ]
    
    def update_session(self, user_id: str, session_id: str, data: dict) -> bool:
        """Update session data for the given session ID"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._update_session_async(user_id, session_id, data))
    
    async def _update_session_async(self, user_id: str, session_id: str, data: dict) -> bool:
        """Async implementation of session update."""
        await self._ensure_connection()
        
        result = await self._connection.execute("""
            UPDATE chat_sessions 
            SET title = COALESCE($3, title),
                metadata = COALESCE($4, metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE session_id = $1 AND user_id = $2
        """, 
        uuid.UUID(session_id), 
        user_id,
        data.get('title'),
        data.get('metadata')
        )
        
        return result != 'UPDATE 0'
    
    def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> List[ChatSession]:
        """List sessions for the given user with pagination"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._list_sessions_async(user_id, page, limit))
    
    async def _list_sessions_async(self, user_id: str, page: int, limit: int) -> List[ChatSession]:
        """Async implementation of session listing."""
        await self._ensure_connection()
        
        offset = page * limit
        sessions = await self._connection.fetch("""
            SELECT session_id, title, user_id, created_at, updated_at, metadata
            FROM chat_sessions
            WHERE user_id = $1
            ORDER BY updated_at DESC
            LIMIT $2 OFFSET $3
        """, user_id, limit, offset)
        
        return [
            ChatSession(
                session_id=str(session['session_id']),
                title=session['title'],
                user_id=session['user_id'],
                created_at=session['created_at'],
                updated_at=session['updated_at'],
                metadata=session['metadata']
            )
            for session in sessions
        ]
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete the session with the given session ID"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._delete_session_async(user_id, session_id))
    
    async def _delete_session_async(self, user_id: str, session_id: str) -> bool:
        """Async implementation of session deletion."""
        await self._ensure_connection()
        
        result = await self._connection.execute("""
            DELETE FROM chat_sessions 
            WHERE session_id = $1 AND user_id = $2
        """, uuid.UUID(session_id), user_id)
        
        return result != 'DELETE 0'
    
    async def add_message(self, session_id: str, role: str, content: str) -> str:
        """Add a message to a session."""
        await self._ensure_connection()
        
        message_id = str(uuid.uuid4())
        await self._connection.execute("""
            INSERT INTO chat_messages (message_id, session_id, role, content)
            VALUES ($1, $2, $3, $4)
        """, 
        uuid.UUID(message_id),
        uuid.UUID(session_id),
        role,
        content
        )
        
        return message_id
