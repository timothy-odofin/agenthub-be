"""
MongoDB session repository implementation.
"""

import uuid
import asyncio
import concurrent.futures
from typing import List
from datetime import datetime

from app.sessions.repositories.base_session_repository import BaseSessionRepository
from app.sessions.models.session import ChatSession
from app.sessions.models.message import ChatMessage
from app.connections.base import ConnectionType
from app.sessions.repositories.session_repository_factory import register_repository, SessionRepositoryType


@register_repository(SessionRepositoryType.MONGODB)
class MongoSessionRepository(BaseSessionRepository):
    """MongoDB implementation of session repository."""
    
    def __init__(self):
        # Pass ConnectionType.MONGODB to parent for centralized connection management
        super().__init__(ConnectionType.MONGODB)
        self._db = None
        self._sessions_collection = None
        self._messages_collection = None
    
    def _create_tables_if_not_exist(self):
        """Create MongoDB collections and indexes if they don't exist."""
        # Get database from connection manager (not directly from PyMongo client)
        self._db = self._connection_manager.get_database()
        
        # Get collections
        self._sessions_collection = self._db.chat_sessions
        self._messages_collection = self._db.chat_messages
        
        # Create indexes for better performance (sync operations since PyMongo is sync)
        try:
            # Use sync operations since we're using PyMongo, not Motor
            self._sessions_collection.create_index("user_id")
            self._sessions_collection.create_index("session_id", unique=True)
            self._messages_collection.create_index("session_id")
            self._messages_collection.create_index([("session_id", 1), ("timestamp", 1)])
        except Exception as e:
            # Index might already exist, that's fine
            print(f"Note: Index creation info: {e}")
    
    def create_session(self, user_id: str, session_data: dict) -> str:
        """
        Create a new session for the given user and return the session ID.
        
        This is a synchronous wrapper around the async implementation.
        For async contexts, use create_session_async() directly.
        """
        session_id = str(uuid.uuid4())
        
        try:
            # Check if we're in an async context
            asyncio.get_running_loop()
            # We're in an async context - delegate to thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_create_session_sync, session_id, user_id, session_data)
                future.result()  # Wait for completion
        except RuntimeError:
            # No running event loop - safe to run directly
            asyncio.run(self._create_session_async(session_id, user_id, session_data))
        
        return session_id
    
    def _run_create_session_sync(self, session_id: str, user_id: str, session_data: dict) -> None:
        """Helper method to run async session creation in a new event loop."""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._create_session_async(session_id, user_id, session_data))
        finally:
            loop.close()

    async def create_session_async(self, user_id: str, session_data: dict) -> str:
        """Async version of create_session for use in async contexts."""
        session_id = str(uuid.uuid4())
        await self._create_session_async(session_id, user_id, session_data)
        return session_id
    
    async def ensure_session_exists(self, session_id: str, user_id: str, session_data: dict = None) -> bool:
        """Ensure a session with the given ID exists for the user. Creates it if it doesn't exist."""
        await self._ensure_connection()
        
        # Check if session already exists
        def check_session():
            return self._sessions_collection.find_one({
                "session_id": session_id,
                "user_id": user_id
            })
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            existing_session = await asyncio.get_event_loop().run_in_executor(executor, check_session)
        
        if existing_session:
            return False  # Session already existed
        
        # Create the session with the specific session_id
        if session_data is None:
            session_data = {}
            
        await self._create_session_async(session_id, user_id, session_data)
        return True  # Session was created
    
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
        
        # Run sync operation in thread pool
        def insert_session():
            return self._sessions_collection.insert_one(session_doc)
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await asyncio.get_event_loop().run_in_executor(executor, insert_session)
    
    async def get_session_history(self, user_id: str, session_id: str) -> List[ChatMessage]:
        """Retrieve the chat history for a given session ID"""
        await self._ensure_connection()
        
        # Run sync operations in thread pool
        def get_session_and_messages():
            # Verify session belongs to user
            session = self._sessions_collection.find_one({
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
            for msg in cursor:
                messages.append(ChatMessage(
                    message_id=msg['message_id'],
                    session_id=msg['session_id'],
                    role=msg['role'],
                    content=msg['content'],
                    timestamp=msg['timestamp']
                ))
            
            return messages
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(executor, get_session_and_messages)
    
    def update_session(self, user_id: str, session_id: str, data: dict) -> bool:
        """Update session data for the given session ID"""
        try:
            # Check if we're in an async context
            asyncio.get_running_loop()
            # We're in an async context - delegate to thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_update_session_sync, user_id, session_id, data)
                return future.result()
        except RuntimeError:
            # No running event loop - safe to run directly
            return asyncio.run(self._update_session_async(user_id, session_id, data))
    
    def _run_update_session_sync(self, user_id: str, session_id: str, data: dict) -> bool:
        """Helper method to run async session update in a new event loop."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._update_session_async(user_id, session_id, data))
        finally:
            loop.close()
    
    async def _update_session_async(self, user_id: str, session_id: str, data: dict) -> bool:
        """Async implementation of session update."""
        await self._ensure_connection()
        
        update_doc = {"updated_at": datetime.utcnow()}
        if 'title' in data:
            update_doc['title'] = data['title']
        if 'metadata' in data:
            update_doc['metadata'] = data['metadata']
        
        # Run sync operation in thread pool
        def update_session():
            return self._sessions_collection.update_one(
                {"session_id": session_id, "user_id": user_id},
                {"$set": update_doc}
            )
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(executor, update_session)
        
        return result.modified_count > 0
    
    def list_paginated_sessions(self, user_id: str, page: int = 0, limit: int = 10) -> List[ChatSession]:
        """List sessions for the given user with pagination"""
        try:
            # Check if we're in an async context
            asyncio.get_running_loop()
            # We're in an async context - delegate to thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_list_sessions_sync, user_id, page, limit)
                return future.result()
        except RuntimeError:
            # No running event loop - safe to run directly
            return asyncio.run(self._list_sessions_async(user_id, page, limit))
    
    def _run_list_sessions_sync(self, user_id: str, page: int, limit: int) -> List[ChatSession]:
        """Helper method to run async session listing in a new event loop."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._list_sessions_async(user_id, page, limit))
        finally:
            loop.close()
    
    async def _list_sessions_async(self, user_id: str, page: int, limit: int) -> List[ChatSession]:
        """Async implementation of session listing."""
        await self._ensure_connection()
        
        skip = page * limit
        
        # Run sync operation in thread pool
        def list_sessions():
            cursor = self._sessions_collection.find({
                "user_id": user_id
            }).sort("updated_at", -1).skip(skip).limit(limit)
            
            sessions = []
            for session in cursor:
                sessions.append(ChatSession(
                    session_id=session['session_id'],
                    title=session['title'],
                    user_id=session['user_id'],
                    created_at=session['created_at'],
                    updated_at=session['updated_at'],
                    metadata=session['metadata']
                ))
            
            return sessions
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(executor, list_sessions)
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete the session with the given session ID"""
        try:
            # Check if we're in an async context
            asyncio.get_running_loop()
            # We're in an async context - delegate to thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_delete_session_sync, user_id, session_id)
                return future.result()
        except RuntimeError:
            # No running event loop - safe to run directly
            return asyncio.run(self._delete_session_async(user_id, session_id))
    
    def _run_delete_session_sync(self, user_id: str, session_id: str) -> bool:
        """Helper method to run async session deletion in a new event loop."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._delete_session_async(user_id, session_id))
        finally:
            loop.close()
    
    async def _delete_session_async(self, user_id: str, session_id: str) -> bool:
        """Async implementation of session deletion."""
        await self._ensure_connection()
        
        # Run sync operations in thread pool
        def delete_session_and_messages():
            # Delete messages first
            self._messages_collection.delete_many({"session_id": session_id})
            
            # Delete session
            result = self._sessions_collection.delete_one({
                "session_id": session_id,
                "user_id": user_id
            })
            
            return result.deleted_count > 0
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(executor, delete_session_and_messages)
    
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
        
        # Run sync operation in thread pool
        def insert_message():
            self._messages_collection.insert_one(message_doc)
            return message_id
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(executor, insert_message)
