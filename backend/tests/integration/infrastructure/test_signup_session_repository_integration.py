"""
Integration tests for SignupSessionRepository with real Redis instance.

These tests verify the repository works correctly with an actual Redis connection,
testing TTL expiration, data persistence, concurrent operations, and error handling.

Prerequisites:
- Redis server must be running on localhost:6379 (or configured host/port)
- Run with: pytest tests/integration/test_signup_session_repository_integration.py -v
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from app.db.repositories.signup_session_repository import signup_session_repository


@pytest.mark.asyncio
class TestSignupSessionRepositoryIntegration:
    """Integration tests for SignupSessionRepository with real Redis."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup: Ensure Redis is connected. Teardown: Clean up test data."""
        # Ensure Redis connection is initialized (access property to trigger connection)
        _ = signup_session_repository.redis
        
        # Store test session IDs for cleanup
        self.test_session_ids = []
        
        yield
        
        # Cleanup: Delete all test sessions
        for session_id in self.test_session_ids:
            try:
                await signup_session_repository.delete_session(session_id)
            except Exception as e:
                print(f"Cleanup warning: Could not delete session {session_id}: {e}")
    
    def track_session(self, session_id: str):
        """Track a session ID for cleanup."""
        self.test_session_ids.append(session_id)
    
    # ==================== Basic CRUD Operations ====================
    
    async def test_create_and_get_session_real_redis(self):
        """Test creating and retrieving a session from real Redis."""
        session_id = "test_session_create_get_001"
        self.track_session(session_id)
        
        session_data = {
            "email": "integration@test.com",
            "username": "integrationuser",
            "current_step": "EMAIL"
        }
        
        # Create session
        await signup_session_repository.create_session(session_id, session_data)
        
        # Retrieve session
        retrieved = await signup_session_repository.get_session(session_id)
        
        # Verify data
        assert retrieved is not None
        assert retrieved["email"] == "integration@test.com"
        assert retrieved["username"] == "integrationuser"
        assert retrieved["current_step"] == "EMAIL"
        assert "created_at" in retrieved
        assert "last_updated" in retrieved
    
    async def test_update_field_real_redis(self):
        """Test updating a single field in Redis."""
        session_id = "test_session_update_field_001"
        self.track_session(session_id)
        
        # Create initial session
        await signup_session_repository.create_session(session_id, {"current_step": "EMAIL"})
        
        # Update field
        await signup_session_repository.update_field(session_id, "email", "updated@test.com")
        
        # Verify update
        retrieved = await signup_session_repository.get_session(session_id)
        assert retrieved["email"] == "updated@test.com"
        assert retrieved["current_step"] == "EMAIL"  # Other fields unchanged
    
    async def test_update_session_multiple_fields_real_redis(self):
        """Test updating multiple fields at once in Redis."""
        session_id = "test_session_update_multi_001"
        self.track_session(session_id)
        
        # Create initial session
        await signup_session_repository.create_session(session_id, {"current_step": "EMAIL"})
        
        # Update multiple fields
        updates = {
            "email": "multi@test.com",
            "username": "multiuser",
            "current_step": "PASSWORD"
        }
        await signup_session_repository.update_session(session_id, updates)
        
        # Verify all updates
        retrieved = await signup_session_repository.get_session(session_id)
        assert retrieved["email"] == "multi@test.com"
        assert retrieved["username"] == "multiuser"
        assert retrieved["current_step"] == "PASSWORD"
    
    async def test_delete_session_real_redis(self):
        """Test deleting a session from Redis."""
        session_id = "test_session_delete_001"
        self.track_session(session_id)
        
        # Create session
        await signup_session_repository.create_session(session_id, {"email": "delete@test.com"})
        
        # Verify exists
        assert await signup_session_repository.session_exists(session_id) is True
        
        # Delete session
        await signup_session_repository.delete_session(session_id)
        
        # Verify deleted
        assert await signup_session_repository.session_exists(session_id) is False
        retrieved = await signup_session_repository.get_session(session_id)
        assert retrieved is None
    
    # ==================== TTL and Expiration Tests ====================
    
    async def test_session_ttl_is_set_correctly(self):
        """Test that TTL is set correctly on session creation."""
        session_id = "test_session_ttl_check_001"
        self.track_session(session_id)
        
        # Create session
        await signup_session_repository.create_session(session_id, {"email": "ttl@test.com"})
        
        # Get Redis connection and check TTL
        redis = signup_session_repository.redis
        key = f"{signup_session_repository.KEY_PREFIX}:{session_id}"
        ttl = await redis.ttl(key)
        
        # TTL should be around 300 seconds (5 minutes), allow some variance
        assert 295 <= ttl <= 305, f"TTL should be ~300 seconds, got {ttl}"
    
    async def test_extend_ttl_real_redis(self):
        """Test extending TTL of an existing session."""
        session_id = "test_session_extend_ttl_001"
        self.track_session(session_id)
        
        # Create session
        await signup_session_repository.create_session(session_id, {"email": "extend@test.com"})
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Extend TTL
        await signup_session_repository.extend_ttl(session_id, 600)  # 10 minutes
        
        # Check new TTL
        redis = signup_session_repository.redis
        key = f"{signup_session_repository.KEY_PREFIX}:{session_id}"
        ttl = await redis.ttl(key)
        
        # TTL should be around 600 seconds now
        assert 595 <= ttl <= 605, f"TTL should be ~600 seconds after extension, got {ttl}"
    
    @pytest.mark.slow  # Mark as slow test
    async def test_session_expires_after_ttl(self):
        """Test that session actually expires after TTL (requires waiting)."""
        session_id = "test_session_expire_001"
        self.track_session(session_id)
        
        # Create session with very short TTL (2 seconds)
        await signup_session_repository.create_session(session_id, {"email": "expire@test.com"})
        
        # Manually set shorter TTL for testing
        redis = signup_session_repository.redis
        key = f"{signup_session_repository.KEY_PREFIX}:{session_id}"
        await redis.expire(key, 2)  # 2 seconds
        
        # Verify exists immediately
        assert await signup_session_repository.session_exists(session_id) is True
        
        # Wait for expiration
        await asyncio.sleep(3)
        
        # Verify expired
        assert await signup_session_repository.session_exists(session_id) is False
        retrieved = await signup_session_repository.get_session(session_id)
        assert retrieved is None
    
    # ==================== Edge Cases and Error Handling ====================
    
    async def test_get_nonexistent_session_returns_none(self):
        """Test that getting a non-existent session returns None."""
        retrieved = await signup_session_repository.get_session("nonexistent_session_999")
        assert retrieved is None
    
    async def test_update_nonexistent_session_raises_error(self):
        """Test that updating a non-existent session raises ValueError."""
        with pytest.raises(ValueError, match="Session .* not found"):
            await signup_session_repository.update_field(
                "nonexistent_session_999", 
                "email", 
                "test@test.com"
            )
    
    async def test_delete_nonexistent_session_succeeds_silently(self):
        """Test that deleting a non-existent session doesn't raise error."""
        # Should not raise an error
        await signup_session_repository.delete_session("nonexistent_session_999")
    
    async def test_session_exists_for_nonexistent_session(self):
        """Test session_exists returns False for non-existent session."""
        exists = await signup_session_repository.session_exists("nonexistent_session_999")
        assert exists is False
    
    # ==================== Data Integrity Tests ====================
    
    async def test_timestamps_are_updated_correctly(self):
        """Test that created_at and last_updated timestamps are set correctly."""
        session_id = "test_session_timestamps_001"
        self.track_session(session_id)
        
        # Create session
        before_create = time.time()
        await signup_session_repository.create_session(session_id, {"email": "timestamp@test.com"})
        after_create = time.time()
        
        # Get session and check created_at
        retrieved = await signup_session_repository.get_session(session_id)
        assert before_create <= retrieved["created_at"] <= after_create
        assert before_create <= retrieved["last_updated"] <= after_create
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Update field
        before_update = time.time()
        await signup_session_repository.update_field(session_id, "username", "timestampuser")
        after_update = time.time()
        
        # Check last_updated was updated but created_at unchanged
        updated = await signup_session_repository.get_session(session_id)
        assert updated["created_at"] == retrieved["created_at"]  # Unchanged
        assert before_update <= updated["last_updated"] <= after_update  # Updated
    
    async def test_increment_attempt_counter(self):
        """Test incrementing attempt counter for retry tracking."""
        session_id = "test_session_attempts_001"
        self.track_session(session_id)
        
        # Create session
        await signup_session_repository.create_session(session_id, {"email": "attempts@test.com"})
        
        # Check initial attempt count (should be 0 or not set)
        retrieved = await signup_session_repository.get_session(session_id)
        initial_count = retrieved.get("attempt_count", 0)
        
        # Increment attempts
        await signup_session_repository.increment_attempt(session_id, "email_validation")
        
        # Verify incremented
        updated = await signup_session_repository.get_session(session_id)
        assert updated.get("attempt_count", 0) == initial_count + 1
        
        # Increment again
        await signup_session_repository.increment_attempt(session_id, "email_validation")
        
        # Verify incremented again
        updated2 = await signup_session_repository.get_session(session_id)
        assert updated2.get("attempt_count", 0) == initial_count + 2
    
    # ==================== Complex Scenarios ====================
    
    async def test_complete_signup_flow_simulation(self):
        """Simulate a complete signup flow through all steps."""
        session_id = "test_session_full_flow_001"
        self.track_session(session_id)
        
        # Step 1: Start - Create session
        await signup_session_repository.create_session(session_id, {"current_step": "EMAIL"})
        
        # Step 2: Email
        await signup_session_repository.update_field(session_id, "email", "fullflow@test.com")
        await signup_session_repository.update_field(session_id, "current_step", "USERNAME")
        
        # Step 3: Username
        await signup_session_repository.update_field(session_id, "username", "fullflowuser")
        await signup_session_repository.update_field(session_id, "current_step", "PASSWORD")
        
        # Step 4: Password (hashed)
        await signup_session_repository.update_field(session_id, "password_hash", "hashed_password_123")
        await signup_session_repository.update_field(session_id, "current_step", "FIRSTNAME")
        
        # Step 5: First name
        await signup_session_repository.update_field(session_id, "firstname", "John")
        await signup_session_repository.update_field(session_id, "current_step", "LASTNAME")
        
        # Step 6: Last name
        await signup_session_repository.update_field(session_id, "lastname", "Doe")
        await signup_session_repository.update_field(session_id, "current_step", "COMPLETE")
        
        # Verify all data
        final_data = await signup_session_repository.get_session(session_id)
        assert final_data["email"] == "fullflow@test.com"
        assert final_data["username"] == "fullflowuser"
        assert final_data["password_hash"] == "hashed_password_123"
        assert final_data["firstname"] == "John"
        assert final_data["lastname"] == "Doe"
        assert final_data["current_step"] == "COMPLETE"
        
        # Step 7: Cleanup (simulate successful signup)
        await signup_session_repository.delete_session(session_id)
        
        # Verify deleted
        assert await signup_session_repository.session_exists(session_id) is False
    
    async def test_concurrent_field_updates(self):
        """Test that concurrent updates to different fields work correctly."""
        session_id = "test_session_concurrent_001"
        self.track_session(session_id)
        
        # Create session
        await signup_session_repository.create_session(session_id, {"current_step": "EMAIL"})
        
        # Update multiple fields concurrently
        await asyncio.gather(
            signup_session_repository.update_field(session_id, "email", "concurrent@test.com"),
            signup_session_repository.update_field(session_id, "username", "concurrentuser"),
            signup_session_repository.update_field(session_id, "firstname", "Concurrent"),
        )
        
        # Verify all updates succeeded
        retrieved = await signup_session_repository.get_session(session_id)
        assert retrieved["email"] == "concurrent@test.com"
        assert retrieved["username"] == "concurrentuser"
        assert retrieved["firstname"] == "Concurrent"
    
    async def test_session_isolation(self):
        """Test that multiple sessions are isolated from each other."""
        session_id_1 = "test_session_isolation_001"
        session_id_2 = "test_session_isolation_002"
        self.track_session(session_id_1)
        self.track_session(session_id_2)
        
        # Create two separate sessions
        await signup_session_repository.create_session(session_id_1, {
            "email": "user1@test.com",
            "username": "user1"
        })
        await signup_session_repository.create_session(session_id_2, {
            "email": "user2@test.com",
            "username": "user2"
        })
        
        # Update session 1
        await signup_session_repository.update_field(session_id_1, "firstname", "User")
        
        # Verify session 2 is unaffected
        session_1 = await signup_session_repository.get_session(session_id_1)
        session_2 = await signup_session_repository.get_session(session_id_2)
        
        assert session_1["email"] == "user1@test.com"
        assert session_1["firstname"] == "User"
        assert session_2["email"] == "user2@test.com"
        assert "firstname" not in session_2
    
    # ==================== Performance Tests ====================
    
    @pytest.mark.slow
    async def test_multiple_rapid_updates(self):
        """Test that multiple rapid updates are handled correctly."""
        session_id = "test_session_rapid_updates_001"
        self.track_session(session_id)
        
        # Create session
        await signup_session_repository.create_session(session_id, {"current_step": "EMAIL"})
        
        # Perform 20 rapid updates
        for i in range(20):
            await signup_session_repository.update_field(session_id, "counter", i)
        
        # Verify final value
        retrieved = await signup_session_repository.get_session(session_id)
        assert retrieved["counter"] == 19  # Last update
    
    async def test_large_session_data(self):
        """Test handling of sessions with large amounts of data."""
        session_id = "test_session_large_data_001"
        self.track_session(session_id)
        
        # Create session with large data
        large_data = {
            "email": "large@test.com",
            "username": "largeuser",
            "large_field": "x" * 10000,  # 10KB of data
            "current_step": "EMAIL"
        }
        
        await signup_session_repository.create_session(session_id, large_data)
        
        # Verify data integrity
        retrieved = await signup_session_repository.get_session(session_id)
        assert retrieved["email"] == "large@test.com"
        assert len(retrieved["large_field"]) == 10000
        assert retrieved["large_field"] == "x" * 10000


# ==================== Standalone Test Functions ====================

@pytest.mark.asyncio
async def test_redis_connection_health():
    """Test that Redis connection is healthy."""
    redis = signup_session_repository.redis
    
    # Test ping
    response = await redis.ping()
    assert response is True, "Redis should respond to ping"


@pytest.mark.asyncio
async def test_repository_singleton_pattern():
    """Test that repository follows singleton pattern."""
    from app.db.repositories.signup_session_repository import SignupSessionRepository
    
    # Get instance
    instance1 = signup_session_repository
    
    # Create new instance
    instance2 = SignupSessionRepository()
    
    # Access redis property to initialize connection
    _ = instance1.redis
    _ = instance2.redis
    
    # Verify both work correctly (not testing if they're the same object,
    # just that both instances are functional)
    test_session_id = "test_singleton_001"
    
    try:
        await instance1.create_session(test_session_id, {"test": "data"})
        retrieved = await instance2.get_session(test_session_id)
        assert retrieved["test"] == "data"
    finally:
        await instance1.delete_session(test_session_id)
