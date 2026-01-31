"""
Unit tests for JWT authentication dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone

from src.app.core.security.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_token_payload,
    require_auth,
)
from src.app.db.models.user import UserInDB
from bson import ObjectId


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user_id = str(ObjectId())
    return UserInDB(
        id=user_id,
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$hash",
        firstname="John",
        lastname="Doe",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def valid_credentials():
    """Create valid HTTP credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid_token_here"
    )


@pytest.fixture
def valid_token_payload():
    """Create a valid token payload."""
    return {
        "sub": "user123",
        "user_id": "user123",
        "email": "test@example.com",
        "username": "testuser",
        "type": "access",
        "exp": 1234567890,
        "iat": 1234567000,
    }


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    @patch('src.app.core.security.dependencies.user_repository')
    async def test_get_current_user_success(
        self,
        mock_user_repo,
        mock_token_manager,
        valid_credentials,
        valid_token_payload,
        mock_user,
    ):
        """Test successful authentication."""
        # Arrange
        mock_token_manager.verify_token.return_value = valid_token_payload
        mock_user_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        
        # Act
        result = await get_current_user(valid_credentials)
        
        # Assert
        assert result == mock_user
        mock_token_manager.verify_token.assert_called_once_with("valid_token_here")
        mock_user_repo.get_user_by_id.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Test authentication without credentials."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    async def test_get_current_user_invalid_token(
        self,
        mock_token_manager,
        valid_credentials,
    ):
        """Test authentication with invalid token."""
        # Arrange
        mock_token_manager.verify_token.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(valid_credentials)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired token"
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    async def test_get_current_user_missing_user_id(
        self,
        mock_token_manager,
        valid_credentials,
    ):
        """Test authentication with token missing user_id."""
        # Arrange
        payload_without_user_id = {"email": "test@example.com"}
        mock_token_manager.verify_token.return_value = payload_without_user_id
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(valid_credentials)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token payload"
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    @patch('src.app.core.security.dependencies.user_repository')
    async def test_get_current_user_user_not_found(
        self,
        mock_user_repo,
        mock_token_manager,
        valid_credentials,
        valid_token_payload,
    ):
        """Test authentication when user doesn't exist in database."""
        # Arrange
        mock_token_manager.verify_token.return_value = valid_token_payload
        mock_user_repo.get_user_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(valid_credentials)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User not found"


class TestGetCurrentUserOptional:
    """Test suite for get_current_user_optional dependency."""
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    @patch('src.app.core.security.dependencies.user_repository')
    async def test_get_current_user_optional_success(
        self,
        mock_user_repo,
        mock_token_manager,
        valid_credentials,
        valid_token_payload,
        mock_user,
    ):
        """Test successful optional authentication."""
        # Arrange
        mock_token_manager.verify_token.return_value = valid_token_payload
        mock_user_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        
        # Act
        result = await get_current_user_optional(valid_credentials)
        
        # Assert
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self):
        """Test optional authentication without credentials returns None."""
        # Act
        result = await get_current_user_optional(None)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    async def test_get_current_user_optional_invalid_token(
        self,
        mock_token_manager,
        valid_credentials,
    ):
        """Test optional authentication with invalid token returns None."""
        # Arrange
        mock_token_manager.verify_token.return_value = None
        
        # Act
        result = await get_current_user_optional(valid_credentials)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    @patch('src.app.core.security.dependencies.user_repository')
    async def test_get_current_user_optional_user_not_found(
        self,
        mock_user_repo,
        mock_token_manager,
        valid_credentials,
        valid_token_payload,
    ):
        """Test optional authentication when user doesn't exist returns None."""
        # Arrange
        mock_token_manager.verify_token.return_value = valid_token_payload
        mock_user_repo.get_user_by_id = AsyncMock(return_value=None)
        
        # Act
        result = await get_current_user_optional(valid_credentials)
        
        # Assert
        assert result is None


class TestGetTokenPayload:
    """Test suite for get_token_payload dependency."""
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    async def test_get_token_payload_success(
        self,
        mock_token_manager,
        valid_credentials,
        valid_token_payload,
    ):
        """Test successful token payload extraction."""
        # Arrange
        mock_token_manager.verify_token.return_value = valid_token_payload
        
        # Act
        result = await get_token_payload(valid_credentials)
        
        # Assert
        assert result == valid_token_payload
        assert result["user_id"] == "user123"
        assert result["email"] == "test@example.com"
        mock_token_manager.verify_token.assert_called_once_with("valid_token_here")
    
    @pytest.mark.asyncio
    async def test_get_token_payload_no_credentials(self):
        """Test token payload extraction without credentials."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_token_payload(None)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    async def test_get_token_payload_invalid_token(
        self,
        mock_token_manager,
        valid_credentials,
    ):
        """Test token payload extraction with invalid token."""
        # Arrange
        mock_token_manager.verify_token.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_token_payload(valid_credentials)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired token"


class TestRequireAuth:
    """Test suite for require_auth alias."""
    
    @pytest.mark.asyncio
    async def test_require_auth_passes_through_user(self, mock_user):
        """Test that require_auth simply passes through the user."""
        # Act
        result = require_auth(mock_user)
        
        # Assert
        assert result == mock_user


class TestDependenciesIntegration:
    """Integration tests for authentication dependencies."""
    
    @pytest.mark.asyncio
    @patch('src.app.core.security.dependencies.token_manager')
    @patch('src.app.core.security.dependencies.user_repository')
    async def test_full_authentication_flow(
        self,
        mock_user_repo,
        mock_token_manager,
        mock_user,
    ):
        """Test complete authentication flow from token to user."""
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
        
        payload = {
            "sub": str(mock_user.id),
            "user_id": str(mock_user.id),
            "email": mock_user.email,
            "username": mock_user.username,
            "type": "access",
        }
        
        mock_token_manager.verify_token.return_value = payload
        mock_user_repo.get_user_by_id = AsyncMock(return_value=mock_user)
        
        # Act - get full user
        user = await get_current_user(credentials)
        
        # Assert
        assert user.id == mock_user.id
        assert user.email == mock_user.email
        assert user.username == mock_user.username
        
        # Act - get just payload (lighter weight)
        payload_result = await get_token_payload(credentials)
        
        # Assert
        assert payload_result["user_id"] == str(mock_user.id)
        assert payload_result["email"] == mock_user.email
        
        # Verify repository only called once (for get_current_user)
        assert mock_user_repo.get_user_by_id.call_count == 1
