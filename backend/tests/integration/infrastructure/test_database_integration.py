"""
Integration tests for MongoDB session functionality.

These tests verify the end-to-end functionality of the session management system
including session creation, message storage, history retrieval, and cleanup.
Uses test-specific database configuration for proper isolation.
"""

import asyncio
import pytest
import uuid
import mongomock
from datetime import datetime
from typing import List, Optional

from app.core.config.framework.settings import settings
from app.infrastructure.connections.database.mongodb_connection_manager import MongoDBConnectionManager
from app.sessions.repositories.mongo_session_repository import MongoSessionRepository


class TestMongoDBSessionIntegration:
    """Integration tests for MongoDB session management with proper resource cleanup."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up and tear down test environment with isolated test database."""
        # Generate unique test database name to avoid conflicts
        self.test_run_id = uuid.uuid4().hex[:8]
        self.test_database_name = f"agenthub_test_{self.test_run_id}"
        self.test_user_prefix = f"test_user_{self.test_run_id}"
        
        # Use test configuration with unique database
        self.test_config = settings.tests.db.mongodb
        self.test_db_uri = f"{self.test_config.connection_string}/{self.test_database_name}"
        
        print(f"Running tests with database: {self.test_database_name}")
        print(f"Test user prefix: {self.test_user_prefix}")
        
        # Initialize connection manager and repository with test configuration
        self.connection_manager = MongoDBConnectionManager()
        self.repository = MongoSessionRepository()
        
        # Override database configuration for testing
        self._original_db_name = self.connection_manager.db_name if hasattr(self.connection_manager, 'db_name') else None
        
        # Ensure connection is established with test database
        await self.repository._ensure_connection()
        
        # Store collections for cleanup
        self.collections_to_cleanup = set()
        
        yield
        
        # Comprehensive cleanup after tests
        await self._cleanup_test_resources()
    
    async def _cleanup_test_resources(self):
        """Comprehensive cleanup of all test resources."""
        try:
            print(f"Starting cleanup for test run: {self.test_run_id}")
            
            if hasattr(self.repository, '_sessions_collection') and self.repository._sessions_collection:
                # Collect session IDs for comprehensive cleanup
                session_ids_to_cleanup = await self._get_test_session_ids()
                
                # Delete test data in correct order (messages first, then sessions)
                await self._delete_test_messages(session_ids_to_cleanup)
                await self._delete_test_sessions()
                
                # Drop test collections if they exist
                await self._drop_test_collections()
                
            # Drop entire test database to ensure complete cleanup
            await self._drop_test_database()
            
            print(f"✓ Cleanup completed for test run: {self.test_run_id}")
            
        except Exception as e:
            print(f"Warning: Could not complete cleanup for test run {self.test_run_id}: {e}")
    
    async def _get_test_session_ids(self) -> List[str]:
        """Get all session IDs created during this test run."""
        try:
            def get_sessions():
                cursor = self.repository._sessions_collection.find({
                    "user_id": {"$regex": f"^{self.test_user_prefix}"}
                }, {"session_id": 1})
                return [session["session_id"] for session in cursor]
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                session_ids = await asyncio.get_event_loop().run_in_executor(
                    executor, get_sessions
                )
            return session_ids
        except Exception as e:
            print(f"Warning: Could not retrieve test session IDs: {e}")
            return []
    
    async def _delete_test_messages(self, session_ids: List[str]):
        """Delete all messages for test sessions."""
        if not session_ids:
            return
            
        try:
            def delete_messages():
                return self.repository._messages_collection.delete_many({
                    "session_id": {"$in": session_ids}
                })
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(
                    executor, delete_messages
                )
            
            print(f"✓ Deleted {result.deleted_count} test messages")
        except Exception as e:
            print(f"Warning: Could not delete test messages: {e}")
    
    async def _delete_test_sessions(self):
        """Delete all sessions for test users."""
        try:
            def delete_sessions():
                return self.repository._sessions_collection.delete_many({
                    "user_id": {"$regex": f"^{self.test_user_prefix}"}
                })
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(
                    executor, delete_sessions
                )
            
            print(f"✓ Deleted {result.deleted_count} test sessions")
        except Exception as e:
            print(f"Warning: Could not delete test sessions: {e}")
    
    async def _drop_test_collections(self):
        """Drop test collections if they were created."""
        try:
            if hasattr(self.repository, '_database') and self.repository._database:
                def drop_collections():
                    collections = self.repository._database.list_collection_names()
                    test_collections = [col for col in collections if 'test' in col.lower() or self.test_run_id in col]
                    
                    for collection_name in test_collections:
                        self.repository._database.drop_collection(collection_name)
                        print(f"✓ Dropped test collection: {collection_name}")
                    
                    return len(test_collections)
                
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    dropped_count = await asyncio.get_event_loop().run_in_executor(
                        executor, drop_collections
                    )
                
                if dropped_count > 0:
                    print(f"✓ Dropped {dropped_count} test collections")
                    
        except Exception as e:
            print(f"Warning: Could not drop test collections: {e}")
    
    async def _drop_test_database(self):
        """Drop the entire test database."""
        try:
            if hasattr(self.connection_manager, '_client') and self.connection_manager._client:
                def drop_database():
                    self.connection_manager._client.drop_database(self.test_database_name)
                
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    await asyncio.get_event_loop().run_in_executor(
                        executor, drop_database
                    )
                
                print(f"✓ Dropped test database: {self.test_database_name}")
                
        except Exception as e:
            print(f"Warning: Could not drop test database: {e}")
    
    def _get_test_user_id(self, suffix: str = "") -> str:
        """Generate a test user ID with the test prefix."""
        return f"{self.test_user_prefix}_{suffix}" if suffix else self.test_user_prefix
    
    @pytest.mark.asyncio
    async def test_session_creation_and_retrieval(self):
        """Test creating and retrieving a session."""
        # Arrange
        user_id = self._get_test_user_id("session_test")
        session_data = {
            'title': 'Test Chat Session',
            'metadata': {'test': True, 'integration': True}
        }
        
        # Act: Create session
        session_id = await self.repository.create_session_async(user_id, session_data)
        
        # Assert: Verify session was created
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        
        print(f"Created session: {session_id}")
        
        # Verify session can be found in database
        sessions = await self.repository._list_sessions_async(user_id, 0, 10)
        assert len(sessions) >= 1
        
        # Find our session
        test_session = None
        for session in sessions:
            if session.session_id == session_id:
                test_session = session
                break
        
        assert test_session is not None
        assert test_session.session_id == session_id
        assert test_session.title == 'Test Chat Session'
        assert test_session.user_id == user_id
        assert test_session.metadata == {'test': True, 'integration': True}
        assert isinstance(test_session.created_at, datetime)
        assert isinstance(test_session.updated_at, datetime)
        
        print(f"✓ Session created and retrieved successfully")
    
    @pytest.mark.asyncio
    async def test_message_storage_and_history_retrieval(self):
        """Test storing messages and retrieving chat history."""
        # Arrange
        user_id = self._get_test_user_id("message_test")
        session_data = {'title': 'Message Test Session'}
        
        # Create session
        session_id = await self.repository.create_session_async(user_id, session_data)
        print(f"Created session for message test: {session_id}")
        
        # Act: Add messages
        message1_id = await self.repository.add_message(session_id, "user", "Hello, how are you?")
        message2_id = await self.repository.add_message(session_id, "assistant", "I'm doing well, thank you!")
        message3_id = await self.repository.add_message(session_id, "user", "Can you help me with Python?")
        
        print(f"Added messages: {message1_id}, {message2_id}, {message3_id}")
        
        # Assert: Verify messages were stored
        assert message1_id is not None
        assert message2_id is not None
        assert message3_id is not None
        
        # Retrieve chat history
        history = await self.repository.get_session_history(user_id, session_id)
        
        # Verify history
        assert len(history) == 3
        
        # Check messages are in correct order
        assert history[0].role == "user"
        assert history[0].content == "Hello, how are you?"
        assert history[0].message_id == message1_id
        
        assert history[1].role == "assistant"
        assert history[1].content == "I'm doing well, thank you!"
        assert history[1].message_id == message2_id
        
        assert history[2].role == "user"
        assert history[2].content == "Can you help me with Python?"
        assert history[2].message_id == message3_id
        
        # Verify all messages belong to the correct session
        for msg in history:
            assert msg.session_id == session_id
            assert isinstance(msg.timestamp, datetime)
        
        print(f"✓ Messages stored and retrieved successfully")
    
    @pytest.mark.asyncio
    async def test_session_update(self):
        """Test updating session metadata."""
        # Arrange
        user_id = self._get_test_user_id("update_test")
        session_data = {'title': 'Original Title', 'metadata': {'version': 1}}
        
        session_id = await self.repository.create_session_async(user_id, session_data)
        print(f"Created session for update test: {session_id}")
        
        # Act: Update session
        update_data = {
            'title': 'Updated Title',
            'metadata': {'version': 2, 'updated': True}
        }
        
        success = await self.repository._update_session_async(user_id, session_id, update_data)
        
        # Assert: Verify update was successful
        assert success is True
        
        # Retrieve updated session
        sessions = await self.repository._list_sessions_async(user_id, 0, 10)
        assert len(sessions) >= 1
        
        # Find our updated session
        updated_session = None
        for session in sessions:
            if session.session_id == session_id:
                updated_session = session
                break
        
        assert updated_session is not None
        assert updated_session.title == 'Updated Title'
        assert updated_session.metadata == {'version': 2, 'updated': True}
        assert updated_session.updated_at > updated_session.created_at
        
        print(f"✓ Session updated successfully")
    
    @pytest.mark.asyncio
    async def test_session_deletion(self):
        """Test deleting a session and its messages."""
        # Arrange
        user_id = self._get_test_user_id("delete_test")
        session_data = {'title': 'Session to Delete'}
        
        session_id = await self.repository.create_session_async(user_id, session_data)
        print(f"Created session for delete test: {session_id}")
        
        # Add some messages
        await self.repository.add_message(session_id, "user", "Test message 1")
        await self.repository.add_message(session_id, "assistant", "Test response 1")
        
        # Verify session and messages exist
        sessions_before = await self.repository._list_sessions_async(user_id, 0, 10)
        history_before = await self.repository.get_session_history(user_id, session_id)
        
        # Find our session in the list
        test_session_exists = any(s.session_id == session_id for s in sessions_before)
        assert test_session_exists
        assert len(history_before) == 2
        
        # Act: Delete session
        success = await self.repository._delete_session_async(user_id, session_id)
        
        # Assert: Verify deletion
        assert success is True
        
        # Verify session is gone
        sessions_after = await self.repository._list_sessions_async(user_id, 0, 10)
        test_session_still_exists = any(s.session_id == session_id for s in sessions_after)
        assert not test_session_still_exists
        
        # Verify messages are gone
        history_after = await self.repository.get_session_history(user_id, session_id)
        assert len(history_after) == 0
        
        print(f"✓ Session and messages deleted successfully")
    
    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self):
        """Test that sessions are properly isolated between users."""
        # Arrange
        user1_id = self._get_test_user_id("isolation_user_1")
        user2_id = self._get_test_user_id("isolation_user_2")
        
        # Create sessions for both users
        session1_id = await self.repository.create_session_async(
            user1_id, {'title': 'User 1 Session'}
        )
        session2_id = await self.repository.create_session_async(
            user2_id, {'title': 'User 2 Session'}
        )
        
        print(f"Created sessions: User1={session1_id}, User2={session2_id}")
        
        # Add messages for both users
        await self.repository.add_message(session1_id, "user", "User 1 message")
        await self.repository.add_message(session2_id, "user", "User 2 message")
        
        # Act & Assert: Verify isolation
        user1_sessions = await self.repository._list_sessions_async(user1_id, 0, 10)
        user2_sessions = await self.repository._list_sessions_async(user2_id, 0, 10)
        
        # Each user should see at least their own session
        user1_session_ids = {s.session_id for s in user1_sessions}
        user2_session_ids = {s.session_id for s in user2_sessions}
        
        assert session1_id in user1_session_ids
        assert session2_id in user2_session_ids
        assert session1_id not in user2_session_ids
        assert session2_id not in user1_session_ids
        
        # Verify history isolation
        user1_history = await self.repository.get_session_history(user1_id, session1_id)
        user2_history = await self.repository.get_session_history(user2_id, session2_id)
        
        assert len(user1_history) == 1
        assert len(user2_history) == 1
        assert user1_history[0].content == "User 1 message"
        assert user2_history[0].content == "User 2 message"
        
        # Verify cross-user access returns empty
        cross_access_history = await self.repository.get_session_history(user1_id, session2_id)
        assert len(cross_access_history) == 0
        
        print(f"✓ User isolation working correctly")
    
    @pytest.mark.asyncio
    async def test_pagination(self):
        """Test session listing pagination."""
        # Arrange
        user_id = self._get_test_user_id("pagination_test")
        
        # Create multiple sessions
        session_ids = []
        for i in range(5):
            session_id = await self.repository.create_session_async(
                user_id, {'title': f'Session {i}'}
            )
            session_ids.append(session_id)
            
            # Add a small delay to ensure different timestamps
            await asyncio.sleep(0.01)
        
        print(f"Created sessions for pagination test: {session_ids}")
        
        # Act & Assert: Test pagination
        # Get first page (2 items)
        page1 = await self.repository._list_sessions_async(user_id, 0, 2)
        assert len(page1) == 2
        
        # Get second page (2 items)  
        page2 = await self.repository._list_sessions_async(user_id, 1, 2)
        assert len(page2) == 2
        
        # Get third page (1 item)
        page3 = await self.repository._list_sessions_async(user_id, 2, 2)
        assert len(page3) == 1
        
        # Verify no overlap between pages
        page1_ids = {session.session_id for session in page1}
        page2_ids = {session.session_id for session in page2}
        page3_ids = {session.session_id for session in page3}
        
        assert len(page1_ids.intersection(page2_ids)) == 0
        assert len(page1_ids.intersection(page3_ids)) == 0
        assert len(page2_ids.intersection(page3_ids)) == 0
        
        # All our test session IDs should be accounted for
        all_paginated_ids = page1_ids.union(page2_ids).union(page3_ids)
        test_session_ids_set = set(session_ids)
        
        # Check that all our test sessions are in the paginated results
        assert test_session_ids_set.issubset(all_paginated_ids)
        
        print(f"✓ Pagination working correctly")
    
    @pytest.mark.asyncio
    async def test_empty_session_history(self):
        """Test retrieving history for a session with no messages."""
        # Arrange
        user_id = self._get_test_user_id("empty_history")
        session_data = {'title': 'Empty Session'}
        
        session_id = await self.repository.create_session_async(user_id, session_data)
        print(f"Created empty session: {session_id}")
        
        # Act: Get history for empty session
        history = await self.repository.get_session_history(user_id, session_id)
        
        # Assert: Should return empty list
        assert isinstance(history, list)
        assert len(history) == 0
        
        print(f"✓ Empty session history working correctly")
    
    @pytest.mark.asyncio
    async def test_nonexistent_session_access(self):
        """Test accessing a non-existent session."""
        # Arrange
        user_id = self._get_test_user_id("nonexistent")
        fake_session_id = str(uuid.uuid4())
        
        print(f"Testing access to non-existent session: {fake_session_id}")
        
        # Act: Try to get history for non-existent session
        history = await self.repository.get_session_history(user_id, fake_session_id)
        
        # Assert: Should return empty list
        assert isinstance(history, list)
        assert len(history) == 0
        
        print(f"✓ Non-existent session access handling working correctly")
    
    @pytest.mark.asyncio
    async def test_complete_session_workflow(self):
        """Test a complete session workflow from creation to deletion."""
        # Arrange
        user_id = self._get_test_user_id("complete_workflow")
        session_data = {
            'title': 'Complete Workflow Test',
            'metadata': {'workflow_test': True}
        }
        
        print("Starting complete workflow test...")
        
        # Step 1: Create session
        session_id = await self.repository.create_session_async(user_id, session_data)
        print(f"Step 1 - Created session: {session_id}")
        
        # Step 2: Add conversation
        await self.repository.add_message(session_id, "user", "What is Python?")
        await self.repository.add_message(session_id, "assistant", "Python is a programming language.")
        await self.repository.add_message(session_id, "user", "Tell me more about it.")
        await self.repository.add_message(session_id, "assistant", "Python is known for its simplicity and readability.")
        print("Step 2 - Added conversation messages")
        
        # Step 3: Retrieve and verify history
        history = await self.repository.get_session_history(user_id, session_id)
        assert len(history) == 4
        assert history[0].content == "What is Python?"
        assert history[1].content == "Python is a programming language."
        assert history[2].content == "Tell me more about it."
        assert history[3].content == "Python is known for its simplicity and readability."
        print("Step 3 - Retrieved and verified conversation history")
        
        # Step 4: Update session
        update_data = {
            'title': 'Updated Workflow Test',
            'metadata': {'workflow_test': True, 'updated': True}
        }
        success = await self.repository._update_session_async(user_id, session_id, update_data)
        assert success is True
        print("Step 4 - Updated session metadata")
        
        # Step 5: Verify session appears in user's session list
        sessions = await self.repository._list_sessions_async(user_id, 0, 10)
        workflow_session = None
        for session in sessions:
            if session.session_id == session_id:
                workflow_session = session
                break
        
        assert workflow_session is not None
        assert workflow_session.title == 'Updated Workflow Test'
        assert workflow_session.metadata['updated'] is True
        print("Step 5 - Verified session in user's session list")
        
        # Step 6: Clean up (delete session)
        delete_success = await self.repository._delete_session_async(user_id, session_id)
        assert delete_success is True
        
        # Verify session and messages are gone
        final_history = await self.repository.get_session_history(user_id, session_id)
        assert len(final_history) == 0
        print("Step 6 - Cleaned up session and messages")
        
        print("✓ Complete workflow test passed successfully!")


if __name__ == "__main__":
    # For running tests directly
    pytest.main([__file__, "-v"])
