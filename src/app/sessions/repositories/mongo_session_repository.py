"""
MongoDB session repository implementation.
"""

import uuid
from typing import List
from datetime import datetime
from app.sessions.repositories.base_session_repository import BaseSessionRepository
from app.sessions.models.session import ChatSession
from app.sessions.models.message import ChatMessage
from app.connections.base import ConnectionType


class MongoSessionRepository(BaseSessionRepository):
    """MongoDB implementation of session repository."""
    
    def __init__(self):
        # Pass ConnectionType.MONGODB to parent for centralized connection management
        super().__init__(ConnectionType.MONGODB)
        self._db = None
        self._sessions_collection = None
        self._messages_collection = None
    
    async def _create_tables_if_not_exist(self):
        """Create MongoDB collections and indexes if they don't exist."""
        # Get database from connection
        self._db = self._connection.get_database()
        
        # Get collections
        self._sessions_collection = self._db.chat_sessions
        self._messages_collection = self._db.chat_messages
        
        # Create indexes for better performance
        await self._sessions_collection.create_index("user_id")
        await self._sessions_collection.create_index("session_id", unique=True)
        await self._messages_collection.create_index("session_id")
        await self._messages_collection.create_index([("session_id", 1), ("timestamp", 1)])
    
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
        
        session_doc = {
            "session_id": session_id,
            "title": session_data.get('title', 'New Chat'),
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": session_data.get('metadata', {})
        }
        
        await self._sessions_collection.insert_one(session_doc)
    
    async def get_session_history(self, user_id: str, session_id: str) -> List[ChatMessage]:
        """Retrieve the chat history for a given session ID"""
        await self._ensure_connection()
        
        # Verify session belongs to user
        session = await self._sessions_collection.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if not session:
            return []
        
        # Get messages
        cursor = self._messages_collection.find({
            "session_id": session_id
        }).sort("timestamp", 1)
        
        messages = []
        async for msg in cursor:
            messages.append(ChatMessage(
                message_id=msg['message_id'],
                session_id=msg['session_id'],
                role=msg['role'],
                content=msg['content'],
                timestamp=msg['timestamp']
            ))
        
        return messages
    
    def update_session(self, user_id: str, session_id: str, data: dict) -> bool:
        """Update session data for the given session ID"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._update_session_async(user_id, session_id, data))
    
    async def _update_session_async(self, user_id: str, session_id: str, data: dict) -> bool:
        """Async implementation of session update."""
        await self._ensure_connection()
        
        update_doc = {"updated_at": datetime.utcnow()}
        if 'title' in data:
            update_doc['title'] = data['title']
        if 'metadata' in data:
            update_doc['metadata'] = data['metadata']
        
        result = await self._sessions_collection.update_one(
            {"session_id": session_id, "user_id": user_id},
            {"$set": update_doc}
        )
        
        return result.modified_count > 0
    
    def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> List[ChatSession]:
        """List sessions for the given user with pagination"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._list_sessions_async(user_id, page, limit))
    
    async def _list_sessions_async(self, user_id: str, page: int, limit: int) -> List[ChatSession]:
        """Async implementation of session listing."""
        await self._ensure_connection()
        
        skip = page * limit
        cursor = self._sessions_collection.find({
            "user_id": user_id
        }).sort("updated_at", -1).skip(skip).limit(limit)
        
        sessions = []
        async for session in cursor:
            sessions.append(ChatSession(
                session_id=session['session_id'],
                title=session['title'],
                user_id=session['user_id'],
                created_at=session['created_at'],
                updated_at=session['updated_at'],
                metadata=session['metadata']
            ))
        
        return sessions
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete the session with the given session ID"""
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._delete_session_async(user_id, session_id))
    
    async def _delete_session_async(self, user_id: str, session_id: str) -> bool:
        """Async implementation of session deletion."""
        await self._ensure_connection()
        
        # Delete messages first
        await self._messages_collection.delete_many({"session_id": session_id})
        
        # Delete session
        result = await self._sessions_collection.delete_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        return result.deleted_count > 0
    
    async def add_message(self, session_id: str, role: str, content: str) -> str:
        """Add a message to a session."""
        await self._ensure_connection()
        
        message_id = str(uuid.uuid4())
        message_doc = {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        
        await self._messages_collection.insert_one(message_doc)
        return message_id
