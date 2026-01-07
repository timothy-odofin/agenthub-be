"""
Unit tests for authentication API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from datetime import datetime, timezone

from src.app.api.v1.auth import router, signup, login, refresh_token
from src.app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
)
from src.app.db.models.user import UserInDB
from datetime import datetime
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


class TestSignupEndpoint:
    """Test suite for signup endpoint."""
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_signup_success(self, mock_auth_service):
        """Test successful user signup."""
        # Arrange
        request = SignupRequest(
            email="newuser@example.com",
            username="newuser",
            password="SecurePass123!",
            firstname="Jane",
            lastname="Smith",
        )
        
        # Mock service response
        mock_auth_service.signup = AsyncMock(return_value={
            "success": True,
            "message": "User created successfully",
            "user_id": "507f1f77bcf86cd799439011",
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_456",
        })
        
        # Act
        response = await signup(request)
        
        # Assert
        assert response.success is True
        assert response.message == "User created successfully"
        assert response.user_id == "507f1f77bcf86cd799439011"
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_456"
        
        # Verify service was called with correct args
        mock_auth_service.signup.assert_called_once_with(
            email=request.email,
            username=request.username,
            password=request.password,
            firstname=request.firstname,
            lastname=request.lastname,
        )
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_signup_validation_failure(self, mock_auth_service):
        """Test signup with validation errors from workflow."""
        # Arrange - valid Pydantic schema but will fail workflow validation
        request = SignupRequest(
            email="invalid@example.com",
            username="validuser",
            password="SecurePass123!",
            firstname="Jane",
            lastname="Smith",
        )
        
        # Mock service failure - duplicate email
        mock_auth_service.signup = AsyncMock(return_value={
            "success": False,
            "message": "Email is already registered",
            "user_id": None,
            "access_token": None,
            "refresh_token": None,
        })
        
        # Act
        response = await signup(request)
        
        # Assert
        assert response.success is False
        assert "already registered" in response.message.lower()
        assert response.user_id is None
        assert response.access_token is None


class TestLoginEndpoint:
    """Test suite for login endpoint."""
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_login_with_email_success(
        self,
        mock_auth_service,
        mock_user,
    ):
        """Test successful login with email."""
        # Arrange
        request = LoginRequest(
            identifier="test@example.com",
            password="password123",
        )
        
        mock_auth_service.login = AsyncMock(return_value={
            "success": True,
            "message": "Login successful",
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "user": {
                "id": str(mock_user.id),
                "email": mock_user.email,
                "username": mock_user.username,
                "firstname": mock_user.firstname,
                "lastname": mock_user.lastname,
            }
        })
        
        # Act
        response = await login(request)
        
        # Assert
        assert response.success is True
        assert response.message == "Login successful"
        assert response.access_token == "access_token"
        assert response.refresh_token == "refresh_token"
        assert response.user is not None
        assert response.user["email"] == mock_user.email
        assert response.user["username"] == mock_user.username
        
        mock_auth_service.login.assert_called_once_with(
            identifier=request.identifier,
            password=request.password,
        )
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_login_with_username_success(
        self,
        mock_auth_service,
        mock_user,
    ):
        """Test successful login with username."""
        # Arrange
        request = LoginRequest(
            identifier="testuser",
            password="password123",
        )
        
        mock_auth_service.login = AsyncMock(return_value={
            "success": True,
            "message": "Login successful",
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "user": {
                "id": str(mock_user.id),
                "email": mock_user.email,
                "username": mock_user.username,
                "firstname": mock_user.firstname,
                "lastname": mock_user.lastname,
            }
        })
        
        # Act
        response = await login(request)
        
        # Assert
        assert response.success is True
        assert response.message == "Login successful"
        
        mock_auth_service.login.assert_called_once_with(
            identifier=request.identifier,
            password=request.password,
        )
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_login_user_not_found(self, mock_auth_service):
        """Test login with non-existent user."""
        # Arrange
        request = LoginRequest(
            identifier="nonexistent@example.com",
            password="password123",
        )
        
        mock_auth_service.login = AsyncMock(return_value={
            "success": False,
            "message": "Invalid credentials",
            "access_token": None,
            "refresh_token": None,
            "user": None,
        })
        
        # Act
        response = await login(request)
        
        # Assert
        assert response.success is False
        assert response.message == "Invalid credentials"
        assert response.access_token is None
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_login_invalid_password(
        self,
        mock_auth_service,
        mock_user,
    ):
        """Test login with incorrect password."""
        # Arrange
        request = LoginRequest(
            identifier="test@example.com",
            password="wrongpassword",
        )
        
        mock_auth_service.login = AsyncMock(return_value={
            "success": False,
            "message": "Invalid credentials",
            "access_token": None,
            "refresh_token": None,
            "user": None,
        })
        
        # Act
        response = await login(request)
        
        # Assert
        assert response.success is False
        assert response.message == "Invalid credentials"
        assert response.access_token is None


class TestRefreshTokenEndpoint:
    """Test suite for refresh token endpoint."""
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_refresh_token_success(
        self,
        mock_auth_service,
        mock_user,
    ):
        """Test successful token refresh."""
        # Arrange
        request = RefreshTokenRequest(refresh_token="valid_refresh_token")
        
        mock_auth_service.refresh_token = AsyncMock(return_value={
            "success": True,
            "message": "Token refreshed successfully",
            "access_token": "new_access_token",
        })
        
        # Act
        response = await refresh_token(request)
        
        # Assert
        assert response.success is True
        assert response.message == "Token refreshed successfully"
        assert response.access_token == "new_access_token"
        
        mock_auth_service.refresh_token.assert_called_once_with(
            refresh_token=request.refresh_token
        )
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_refresh_token_invalid(self, mock_auth_service):
        """Test refresh with invalid token."""
        # Arrange
        request = RefreshTokenRequest(refresh_token="invalid_token")
        
        mock_auth_service.refresh_token = AsyncMock(return_value={
            "success": False,
            "message": "Invalid or expired refresh token",
            "access_token": None,
        })
        
        # Act
        response = await refresh_token(request)
        
        # Assert
        assert response.success is False
        assert response.message == "Invalid or expired refresh token"
        assert response.access_token is None
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_refresh_token_user_not_found(
        self,
        mock_auth_service,
    ):
        """Test refresh when user no longer exists."""
        # Arrange
        request = RefreshTokenRequest(refresh_token="valid_refresh_token")
        
        mock_auth_service.refresh_token = AsyncMock(return_value={
            "success": False,
            "message": "User not found",
            "access_token": None,
        })
        
        # Act
        response = await refresh_token(request)
        
        # Assert
        assert response.success is False
        assert response.message == "User not found"
        assert response.access_token is None


class TestAuthEndpointIntegration:
    """Integration tests for auth endpoint workflows."""
    
    @pytest.mark.asyncio
    @patch('src.app.api.v1.auth.auth_service')
    async def test_signup_then_login_workflow(
        self,
        mock_auth_service,
        mock_user,
    ):
        """Test complete signup then login workflow."""
        # Signup
        signup_request = SignupRequest(
            email="newuser@example.com",
            username="newuser",
            password="SecurePass123!",
            firstname="Jane",
            lastname="Smith",
        )
        
        mock_auth_service.signup = AsyncMock(return_value={
            "success": True,
            "message": "User created successfully",
            "user_id": str(mock_user.id),
            "access_token": "signup_access_token",
            "refresh_token": "signup_refresh_token",
        })
        
        signup_response = await signup(signup_request)
        
        assert signup_response.success is True
        assert signup_response.access_token == "signup_access_token"
        
        # Login
        login_request = LoginRequest(
            identifier="newuser@example.com",
            password="SecurePass123!",
        )
        
        mock_auth_service.login = AsyncMock(return_value={
            "success": True,
            "message": "Login successful",
            "access_token": "login_access_token",
            "refresh_token": "login_refresh_token",
            "user": {
                "id": str(mock_user.id),
                "email": mock_user.email,
                "username": mock_user.username,
                "firstname": mock_user.firstname,
                "lastname": mock_user.lastname,
            }
        })
        
        login_response = await login(login_request)
        
        assert login_response.success is True
        assert login_response.access_token == "login_access_token"
        assert login_response.user["email"] == mock_user.email
