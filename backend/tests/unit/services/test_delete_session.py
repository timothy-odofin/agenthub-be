"""
Unit tests for session deletion functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.chat_service import ChatService


class TestDeleteSession:
    """Test suite for delete_session functionality."""
    
    @pytest.fixture
    def chat_service(self):
        """Create a ChatService instance for testing."""
        return ChatService()
    
    @pytest.fixture
    def mock_session_repo(self):
        """Create a mock session repository."""
        return Mock()
    
    def test_delete_session_success(self, chat_service, mock_session_repo):
        """Test successful session deletion."""
        # Arrange
        user_id = "user_123"
        session_id = "session_456"
        mock_session_repo.delete_session.return_value = True
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            result = chat_service.delete_session(user_id, session_id)
        
        # Assert
        assert result is True
        mock_session_repo.delete_session.assert_called_once_with(
            user_id=user_id,
            session_id=session_id
        )
    
    def test_delete_session_not_found(self, chat_service, mock_session_repo):
        """Test deleting a non-existent session."""
        # Arrange
        user_id = "user_123"
        session_id = "nonexistent_session"
        mock_session_repo.delete_session.return_value = False
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            result = chat_service.delete_session(user_id, session_id)
        
        # Assert
        assert result is False
        mock_session_repo.delete_session.assert_called_once_with(
            user_id=user_id,
            session_id=session_id
        )
    
    def test_delete_session_unauthorized(self, chat_service, mock_session_repo):
        """Test deleting another user's session (should fail)."""
        # Arrange
        user_id = "user_123"
        other_user_session = "other_user_session"
        mock_session_repo.delete_session.return_value = False
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            result = chat_service.delete_session(user_id, other_user_session)
        
        # Assert
        assert result is False
    
    def test_delete_session_exception_handling(self, chat_service, mock_session_repo):
        """Test exception handling during session deletion."""
        # Arrange
        user_id = "user_123"
        session_id = "session_456"
        mock_session_repo.delete_session.side_effect = Exception("Database error")
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            result = chat_service.delete_session(user_id, session_id)
        
        # Assert
        assert result is False
    
    def test_delete_session_with_messages(self, chat_service, mock_session_repo):
        """Test that deleting a session also deletes associated messages."""
        # Arrange
        user_id = "user_123"
        session_id = "session_with_messages"
        mock_session_repo.delete_session.return_value = True
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            result = chat_service.delete_session(user_id, session_id)
        
        # Assert
        assert result is True
        # Verify the repository method was called (repository handles cascade deletion)
        mock_session_repo.delete_session.assert_called_once()
    
    def test_delete_multiple_sessions(self, chat_service, mock_session_repo):
        """Test deleting multiple sessions sequentially."""
        # Arrange
        user_id = "user_123"
        session_ids = ["session_1", "session_2", "session_3"]
        mock_session_repo.delete_session.return_value = True
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            results = [chat_service.delete_session(user_id, sid) for sid in session_ids]
        
        # Assert
        assert all(results)
        assert mock_session_repo.delete_session.call_count == 3
    
    def test_delete_session_empty_session_id(self, chat_service, mock_session_repo):
        """Test deleting with empty session ID."""
        # Arrange
        user_id = "user_123"
        session_id = ""
        mock_session_repo.delete_session.return_value = False
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            result = chat_service.delete_session(user_id, session_id)
        
        # Assert
        assert result is False
    
    def test_delete_session_empty_user_id(self, chat_service, mock_session_repo):
        """Test deleting with empty user ID."""
        # Arrange
        user_id = ""
        session_id = "session_456"
        mock_session_repo.delete_session.return_value = False
        
        with patch('app.services.chat_service.SessionRepositoryFactory.get_default_repository', return_value=mock_session_repo):
            # Act
            result = chat_service.delete_session(user_id, session_id)
        
        # Assert
        assert result is False

