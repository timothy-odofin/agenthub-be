"""
Unit tests for SignupSessionRepository.

Tests Redis-based session management for conversational signup flow.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.app.db.repositories.signup_session_repository import (
    SignupSessionRepository,
    signup_session_repository
)


class TestSignupSessionRepositoryInit:
    """Test repository initialization."""
    
    def test_init_creates_instance(self):
        """Test that repository can be instantiated."""
        repo = SignupSessionRepository()
        assert repo is not None
        assert repo.KEY_PREFIX == "signup"
        assert repo.SESSION_TTL == 900
    
    def test_singleton_instance_exists(self):
        """Test that singleton instance is created."""
        assert signup_session_repository is not None
        assert isinstance(signup_session_repository, SignupSessionRepository)
    
    def test_make_key_formats_correctly(self):
        """Test key formatting."""
        repo = SignupSessionRepository()
        key = repo._make_key("test-uuid-123")
        assert key == "signup:test-uuid-123"


class TestSignupSessionRepositoryCreate:
    """Test session creation."""
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_create_session_success(self, mock_factory):
        """Test successful session creation."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        # Create session
        result = await repo.create_session("test-uuid", {"current_step": "EMAIL"})
        
        assert result is True
        mock_redis.set.assert_called_once()
        
        # Verify call arguments
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "signup:test-uuid"  # Key
        assert call_args[1]["ex"] == 900  # TTL
        
        # Verify stored data contains required fields
        stored_data = json.loads(call_args[0][1])
        assert stored_data["session_id"] == "test-uuid"
        assert stored_data["current_step"] == "EMAIL"
        assert "created_at" in stored_data
        assert "last_updated" in stored_data
        assert "attempt_count" in stored_data
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_create_session_with_no_data(self, mock_factory):
        """Test session creation with no initial data."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.create_session("test-uuid")
        
        assert result is True
        stored_data = json.loads(mock_redis.set.call_args[0][1])
        assert stored_data["session_id"] == "test-uuid"
        assert stored_data["attempt_count"] == 0


class TestSignupSessionRepositoryGet:
    """Test session retrieval."""
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_get_session_success(self, mock_factory):
        """Test successful session retrieval."""
        # Mock session data
        session_data = {
            "session_id": "test-uuid",
            "email": "john@example.com",
            "current_step": "USERNAME",
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0,
            "attempt_count": 1
        }
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(session_data))
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.get_session("test-uuid")
        
        assert result is not None
        assert result["session_id"] == "test-uuid"
        assert result["email"] == "john@example.com"
        assert result["current_step"] == "USERNAME"
        mock_redis.get.assert_called_once_with("signup:test-uuid")
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_get_session_not_found(self, mock_factory):
        """Test get session when session doesn't exist."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.get_session("nonexistent-uuid")
        
        assert result is None


class TestSignupSessionRepositoryUpdate:
    """Test session updates."""
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_update_field_success(self, mock_factory):
        """Test updating a single field."""
        existing_data = {
            "session_id": "test-uuid",
            "current_step": "EMAIL",
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0,
            "attempt_count": 0
        }
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(existing_data))
        mock_redis.set = AsyncMock(return_value=True)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.update_field("test-uuid", "email", "john@example.com")
        
        assert result is True
        
        # Verify updated data
        call_args = mock_redis.set.call_args
        updated_data = json.loads(call_args[0][1])
        assert updated_data["email"] == "john@example.com"
        assert updated_data["last_updated"] > existing_data["last_updated"]
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_update_session_multiple_fields(self, mock_factory):
        """Test updating multiple fields at once."""
        existing_data = {
            "session_id": "test-uuid",
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0,
            "attempt_count": 0
        }
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(existing_data))
        mock_redis.set = AsyncMock(return_value=True)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        update_data = {
            "email": "john@example.com",
            "current_step": "USERNAME"
        }
        
        result = await repo.update_session("test-uuid", update_data)
        
        assert result is True
        
        # Verify all fields updated
        call_args = mock_redis.set.call_args
        updated_data = json.loads(call_args[0][1])
        assert updated_data["email"] == "john@example.com"
        assert updated_data["current_step"] == "USERNAME"


class TestSignupSessionRepositoryDelete:
    """Test session deletion."""
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_delete_session_success(self, mock_factory):
        """Test successful session deletion."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)  # 1 key deleted
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.delete_session("test-uuid")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("signup:test-uuid")
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_delete_session_not_found(self, mock_factory):
        """Test deletion when session doesn't exist."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=0)  # 0 keys deleted
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.delete_session("nonexistent-uuid")
        
        assert result is False


class TestSignupSessionRepositoryUtilities:
    """Test utility methods."""
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_session_exists_true(self, mock_factory):
        """Test session existence check - exists."""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.session_exists("test-uuid")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("signup:test-uuid")
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_session_exists_false(self, mock_factory):
        """Test session existence check - doesn't exist."""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.session_exists("test-uuid")
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_extend_ttl_success(self, mock_factory):
        """Test TTL extension."""
        mock_redis = AsyncMock()
        mock_redis.expire = AsyncMock(return_value=True)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.extend_ttl("test-uuid", 1800)
        
        assert result is True
        mock_redis.expire.assert_called_once_with("signup:test-uuid", 1800)
    
    @pytest.mark.asyncio
    @patch('src.app.db.repositories.signup_session_repository.ConnectionFactory')
    async def test_increment_attempt_success(self, mock_factory):
        """Test attempt counter increment."""
        existing_data = {
            "session_id": "test-uuid",
            "attempt_count": 2,
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0
        }
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(existing_data))
        mock_redis.set = AsyncMock(return_value=True)
        mock_factory.get_connection_manager.return_value = mock_redis
        
        repo = SignupSessionRepository()
        repo._redis_manager = mock_redis
        
        result = await repo.increment_attempt("test-uuid")
        
        assert result == 3
        
        # Verify attempt_count was updated
        call_args = mock_redis.set.call_args
        updated_data = json.loads(call_args[0][1])
        assert updated_data["attempt_count"] == 3
