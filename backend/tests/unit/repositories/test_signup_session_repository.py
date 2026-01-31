"""
Unit tests for SignupSessionRepository.

Tests Redis cache-based session management for conversational signup flow.
Updated to work with signup_cache implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.db.repositories.signup_session_repository import (
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
        assert repo.SESSION_TTL == 300  # Updated from 900 to 300
    
    def test_singleton_instance_exists(self):
        """Test that singleton instance is created."""
        assert signup_session_repository is not None
        assert isinstance(signup_session_repository, SignupSessionRepository)
    
    def test_make_key_formats_correctly(self):
        """Test key formatting - now returns session_id (namespace handles prefix)."""
        repo = SignupSessionRepository()
        key = repo._make_key("test-uuid-123")
        assert key == "test-uuid-123"  # Changed: namespace handles 'signup:' prefix


class TestSignupSessionRepositoryCreate:
    """Test session creation."""
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_create_session_success(self, mock_cache):
        """Test successful session creation."""
        # Mock cache
        mock_cache.set = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        # Create session
        result = await repo.create_session("test-uuid", {"current_step": "EMAIL"})
        
        assert result is True
        mock_cache.set.assert_called_once()
        
        # Verify call arguments
        call_args = mock_cache.set.call_args
        assert call_args[1]["key"] == "test-uuid"  # Key (session_id)
        assert call_args[1]["ttl"] == 300  # TTL (updated from 900)
        
        # Verify stored data contains required fields (passed as dict, not JSON)
        stored_data = call_args[1]["value"]
        assert stored_data["session_id"] == "test-uuid"
        assert stored_data["current_step"] == "EMAIL"
        assert "created_at" in stored_data
        assert "last_updated" in stored_data
        assert "attempt_count" in stored_data
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_create_session_with_no_data(self, mock_cache):
        """Test session creation with no initial data."""
        mock_cache.set = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.create_session("test-uuid")
        
        assert result is True
        stored_data = mock_cache.set.call_args[1]["value"]
        assert stored_data["session_id"] == "test-uuid"
        assert stored_data["attempt_count"] == 0


class TestSignupSessionRepositoryGet:
    """Test session retrieval."""
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_get_session_success(self, mock_cache):
        """Test successful session retrieval."""
        # Mock session data (cache returns dict, not JSON string)
        session_data = {
            "session_id": "test-uuid",
            "email": "john@example.com",
            "current_step": "USERNAME",
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0,
            "attempt_count": 1
        }
        
        mock_cache.get = AsyncMock(return_value=session_data)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.get_session("test-uuid")
        
        assert result is not None
        assert result["session_id"] == "test-uuid"
        assert result["email"] == "john@example.com"
        assert result["current_step"] == "USERNAME"
        mock_cache.get.assert_called_once_with("test-uuid")  # Key without prefix
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_get_session_not_found(self, mock_cache):
        """Test get session when session doesn't exist."""
        mock_cache.get = AsyncMock(return_value=None)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.get_session("nonexistent-uuid")
        
        assert result is None


class TestSignupSessionRepositoryUpdate:
    """Test session updates."""
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_update_field_success(self, mock_cache):
        """Test updating a single field."""
        existing_data = {
            "session_id": "test-uuid",
            "current_step": "EMAIL",
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0,
            "attempt_count": 0
        }
        
        mock_cache.get = AsyncMock(return_value=existing_data)
        mock_cache.set = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.update_field("test-uuid", "email", "john@example.com")
        
        assert result is True
        
        # Verify updated data (cache.set receives dict, not JSON)
        call_args = mock_cache.set.call_args
        updated_data = call_args[1]["value"]  # Dict from keyword args
        assert updated_data["email"] == "john@example.com"
        assert updated_data["last_updated"] >= existing_data["last_updated"]  # >= for fast execution
        assert call_args[1]["ttl"] == 300  # Updated TTL
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_update_session_multiple_fields(self, mock_cache):
        """Test updating multiple fields at once."""
        existing_data = {
            "session_id": "test-uuid",
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0,
            "attempt_count": 0
        }
        
        mock_cache.get = AsyncMock(return_value=existing_data)
        mock_cache.set = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        update_data = {
            "email": "john@example.com",
            "current_step": "USERNAME"
        }
        
        result = await repo.update_session("test-uuid", update_data)
        
        assert result is True
        
        # Verify all fields updated (cache returns dict)
        call_args = mock_cache.set.call_args
        updated_data = call_args[1]["value"]
        assert updated_data["email"] == "john@example.com"
        assert updated_data["current_step"] == "USERNAME"


class TestSignupSessionRepositoryDelete:
    """Test session deletion."""
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_delete_session_success(self, mock_cache):
        """Test successful session deletion."""
        mock_cache.delete = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.delete_session("test-uuid")
        
        assert result is True
        mock_cache.delete.assert_called_once_with("test-uuid")  # Key without prefix
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_delete_session_not_found(self, mock_cache):
        """Test deletion when session doesn't exist."""
        mock_cache.delete = AsyncMock(return_value=False)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.delete_session("nonexistent-uuid")
        
        assert result is False


class TestSignupSessionRepositoryUtilities:
    """Test utility methods."""
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_session_exists_true(self, mock_cache):
        """Test session existence check - exists."""
        mock_cache.exists = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.session_exists("test-uuid")
        
        assert result is True
        mock_cache.exists.assert_called_once_with("test-uuid")  # Key without prefix
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_session_exists_false(self, mock_cache):
        """Test session existence check - doesn't exist."""
        mock_cache.exists = AsyncMock(return_value=False)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.session_exists("test-uuid")
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_extend_ttl_success(self, mock_cache):
        """Test TTL extension."""
        mock_cache.set_ttl = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.extend_ttl("test-uuid", 1800)
        
        assert result is True
        mock_cache.set_ttl.assert_called_once_with("test-uuid", 1800)  # Key without prefix
    
    @pytest.mark.asyncio
    @patch('app.db.repositories.signup_session_repository.signup_cache')
    async def test_increment_attempt_success(self, mock_cache):
        """Test attempt counter increment."""
        existing_data = {
            "session_id": "test-uuid",
            "attempt_count": 2,
            "created_at": 1704638400.0,
            "last_updated": 1704638400.0
        }
        
        mock_cache.get = AsyncMock(return_value=existing_data)
        mock_cache.set = AsyncMock(return_value=True)
        
        repo = SignupSessionRepository()
        repo.cache = mock_cache
        
        result = await repo.increment_attempt("test-uuid")
        
        assert result == 3
        
        # Verify attempt_count was updated (cache receives dict)
        call_args = mock_cache.set.call_args
        updated_data = call_args[1]["value"]
        assert updated_data["attempt_count"] == 3
