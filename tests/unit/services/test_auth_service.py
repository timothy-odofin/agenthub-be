"""
Unit tests for AuthService.
Tests the business logic of authentication operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from src.app.services.auth_service import AuthService
from src.app.db.models.user import UserInDB


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
def auth_service():
    """Create an AuthService instance with mocked dependencies."""
    with patch('src.app.services.auth_service.user_repository') as mock_user_repo, \
         patch('src.app.services.auth_service.password_manager') as mock_pwd_mgr, \
         patch('src.app.services.auth_service.token_manager') as mock_token_mgr, \
         patch('src.app.services.auth_service.signup_workflow') as mock_workflow:
        
        service = AuthService()
        service.user_repository = mock_user_repo
        service.password_manager = mock_pwd_mgr
        service.token_manager = mock_token_mgr
        service.signup_workflow = mock_workflow
        
        yield service


class TestAuthServiceSignup:
    """Test suite for AuthService.signup() method."""
    
    @pytest.mark.asyncio
    async def test_signup_success(self, auth_service):
        """Test successful user signup."""
        # Arrange
        email = "newuser@example.com"
        username = "newuser"
        password = "SecurePass123!"
        firstname = "Jane"
        lastname = "Smith"
        user_id = str(ObjectId())
        
        # Mock workflow success
        auth_service.signup_workflow.ainvoke = AsyncMock(return_value={
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id,
        })
        
        # Mock token creation
        auth_service.token_manager.create_access_token.return_value = "access_token_123"
        auth_service.token_manager.create_refresh_token.return_value = "refresh_token_456"
        
        # Act
        result = await auth_service.signup(email, username, password, firstname, lastname)
        
        # Assert
        assert result["success"] is True
        assert result["message"] == "User registered successfully"
        assert result["user_id"] == user_id
        assert result["access_token"] == "access_token_123"
        assert result["refresh_token"] == "refresh_token_456"
        
        # Verify workflow was called with correct args
        auth_service.signup_workflow.ainvoke.assert_called_once()
        call_args = auth_service.signup_workflow.ainvoke.call_args[0][0]
        assert call_args["email"] == email
        assert call_args["username"] == username
        assert call_args["password"] == password
        assert call_args["firstname"] == firstname
        assert call_args["lastname"] == lastname
        
        # Verify token creation was called
        auth_service.token_manager.create_access_token.assert_called_once()
        auth_service.token_manager.create_refresh_token.assert_called_once()
        
        # Verify token creation was called with correct user_id
        access_call_kwargs = auth_service.token_manager.create_access_token.call_args.kwargs
        assert access_call_kwargs["user_id"] == user_id
        assert access_call_kwargs["email"] == email
        assert access_call_kwargs["username"] == username
        
        refresh_call_kwargs = auth_service.token_manager.create_refresh_token.call_args.kwargs
        assert refresh_call_kwargs["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, auth_service):
        """Test signup with duplicate email."""
        # Arrange
        email = "existing@example.com"
        username = "newuser"
        password = "SecurePass123!"
        firstname = "Jane"
        lastname = "Smith"
        
        # Mock workflow failure - duplicate email
        auth_service.signup_workflow.ainvoke = AsyncMock(return_value={
            "success": False,
            "message": "Email is already registered",
        })
        
        # Act
        result = await auth_service.signup(email, username, password, firstname, lastname)
        
        # Assert
        assert result["success"] is False
        assert "email" in result["message"].lower()
        assert result.get("user_id") is None
        assert result.get("access_token") is None
        assert result.get("refresh_token") is None
        
        # Verify tokens were NOT created
        auth_service.token_manager.create_access_token.assert_not_called()
        auth_service.token_manager.create_refresh_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_username(self, auth_service):
        """Test signup with duplicate username."""
        # Arrange
        email = "newuser@example.com"
        username = "existinguser"
        password = "SecurePass123!"
        firstname = "Jane"
        lastname = "Smith"
        
        # Mock workflow failure - duplicate username
        auth_service.signup_workflow.ainvoke = AsyncMock(return_value={
            "success": False,
            "message": "Username is already taken",
        })
        
        # Act
        result = await auth_service.signup(email, username, password, firstname, lastname)
        
        # Assert
        assert result["success"] is False
        assert "username" in result["message"].lower()
        assert result.get("user_id") is None
        assert result.get("access_token") is None
        assert result.get("refresh_token") is None


class TestAuthServiceLogin:
    """Test suite for AuthService.login() method."""
    
    @pytest.mark.asyncio
    async def test_login_with_email_success(self, auth_service, mock_user):
        """Test successful login with email."""
        # Arrange
        identifier = "test@example.com"
        password = "password123"
        
        auth_service.user_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.password_manager.verify_password.return_value = True
        auth_service.token_manager.create_access_token.return_value = "access_token"
        auth_service.token_manager.create_refresh_token.return_value = "refresh_token"
        
        # Act
        result = await auth_service.login(identifier, password)
        
        # Assert
        assert result["success"] is True
        assert result["message"] == "Login successful"
        assert result["access_token"] == "access_token"
        assert result["refresh_token"] == "refresh_token"
        assert result["user"] is not None
        assert result["user"]["user_id"] == mock_user.id
        assert result["user"]["email"] == mock_user.email
        assert result["user"]["username"] == mock_user.username
        assert result["user"]["firstname"] == mock_user.firstname
        assert result["user"]["lastname"] == mock_user.lastname
        
        # Verify method calls
        auth_service.user_repository.get_user_by_email.assert_called_once_with(identifier)
        auth_service.password_manager.verify_password.assert_called_once_with(password, mock_user.password_hash)
        # Verify tokens were created (keyword args, so just check they were called)
        auth_service.token_manager.create_access_token.assert_called_once()
        auth_service.token_manager.create_refresh_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_with_username_success(self, auth_service, mock_user):
        """Test successful login with username."""
        # Arrange
        identifier = "testuser"
        password = "password123"
        
        # Email lookup returns None, username lookup returns user
        auth_service.user_repository.get_user_by_email = AsyncMock(return_value=None)
        auth_service.user_repository.get_user_by_username = AsyncMock(return_value=mock_user)
        auth_service.password_manager.verify_password.return_value = True
        auth_service.token_manager.create_access_token.return_value = "access_token"
        auth_service.token_manager.create_refresh_token.return_value = "refresh_token"
        
        # Act
        result = await auth_service.login(identifier, password)
        
        # Assert
        assert result["success"] is True
        assert result["message"] == "Login successful"
        assert result["access_token"] == "access_token"
        assert result["refresh_token"] == "refresh_token"
        
        # Verify both lookups were attempted
        auth_service.user_repository.get_user_by_email.assert_called_once_with(identifier)
        auth_service.user_repository.get_user_by_username.assert_called_once_with(identifier)
        auth_service.password_manager.verify_password.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service):
        """Test login with non-existent user."""
        # Arrange
        identifier = "nonexistent@example.com"
        password = "password123"
        
        auth_service.user_repository.get_user_by_email = AsyncMock(return_value=None)
        auth_service.user_repository.get_user_by_username = AsyncMock(return_value=None)
        
        # Act
        result = await auth_service.login(identifier, password)
        
        # Assert
        assert result["success"] is False
        assert result["message"] == "Invalid credentials"
        assert result.get("access_token") is None
        assert result.get("refresh_token") is None
        assert result.get("user") is None
        
        # Verify password was NOT checked
        auth_service.password_manager.verify_password.assert_not_called()
        # Verify tokens were NOT created
        auth_service.token_manager.create_access_token.assert_not_called()
        auth_service.token_manager.create_refresh_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, mock_user):
        """Test login with incorrect password."""
        # Arrange
        identifier = "test@example.com"
        password = "wrongpassword"
        
        auth_service.user_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.password_manager.verify_password.return_value = False
        
        # Act
        result = await auth_service.login(identifier, password)
        
        # Assert
        assert result["success"] is False
        assert result["message"] == "Invalid credentials"
        assert result.get("access_token") is None
        assert result.get("refresh_token") is None
        assert result.get("user") is None
        
        # Verify password was checked
        auth_service.password_manager.verify_password.assert_called_once_with(password, mock_user.password_hash)
        # Verify tokens were NOT created
        auth_service.token_manager.create_access_token.assert_not_called()
        auth_service.token_manager.create_refresh_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_login_email_priority_over_username(self, auth_service, mock_user):
        """Test that email lookup is attempted first before username."""
        # Arrange
        identifier = "test@example.com"
        password = "password123"
        
        auth_service.user_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.password_manager.verify_password.return_value = True
        auth_service.token_manager.create_access_token.return_value = "access_token"
        auth_service.token_manager.create_refresh_token.return_value = "refresh_token"
        
        # Act
        result = await auth_service.login(identifier, password)
        
        # Assert
        assert result["success"] is True
        
        # Verify email was checked first and username was NOT checked
        auth_service.user_repository.get_user_by_email.assert_called_once()
        auth_service.user_repository.get_user_by_username.assert_not_called()


class TestAuthServiceRefreshToken:
    """Test suite for AuthService.refresh_token() method."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_user):
        """Test successful token refresh."""
        # Arrange
        refresh_token = "valid_refresh_token"
        
        auth_service.token_manager.verify_refresh_token.return_value = mock_user.id
        auth_service.user_repository.get_user_by_id = AsyncMock(return_value=mock_user)
        auth_service.token_manager.create_access_token.return_value = "new_access_token"
        
        # Act
        result = await auth_service.refresh_token(refresh_token)
        
        # Assert
        assert result["success"] is True
        assert result["message"] == "Token refreshed successfully"
        assert result["access_token"] == "new_access_token"
        
        # Verify method calls
        auth_service.token_manager.verify_refresh_token.assert_called_once_with(refresh_token)
        auth_service.user_repository.get_user_by_id.assert_called_once_with(mock_user.id)
        # Verify token was created (keyword args)
        auth_service.token_manager.create_access_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service):
        """Test refresh with invalid token."""
        # Arrange
        refresh_token = "invalid_token"
        
        auth_service.token_manager.verify_refresh_token.return_value = None
        
        # Act
        result = await auth_service.refresh_token(refresh_token)
        
        # Assert
        assert result["success"] is False
        assert result["message"] == "Invalid or expired refresh token"
        assert result.get("access_token") is None
        
        # Verify token was verified but user lookup was NOT attempted
        auth_service.token_manager.verify_refresh_token.assert_called_once_with(refresh_token)
        auth_service.user_repository.get_user_by_id.assert_not_called()
        # Verify new token was NOT created
        auth_service.token_manager.create_access_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self, auth_service):
        """Test refresh when user no longer exists."""
        # Arrange
        refresh_token = "valid_refresh_token"
        user_id = "deleted_user_id"
        
        auth_service.token_manager.verify_refresh_token.return_value = user_id
        auth_service.user_repository.get_user_by_id = AsyncMock(return_value=None)
        
        # Act
        result = await auth_service.refresh_token(refresh_token)
        
        # Assert
        assert result["success"] is False
        assert result["message"] == "User not found"
        assert result.get("access_token") is None
        
        # Verify both token verification and user lookup were attempted
        auth_service.token_manager.verify_refresh_token.assert_called_once_with(refresh_token)
        auth_service.user_repository.get_user_by_id.assert_called_once_with(user_id)
        # Verify new token was NOT created
        auth_service.token_manager.create_access_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, auth_service):
        """Test refresh with expired token (verify returns None)."""
        # Arrange
        refresh_token = "expired_token"
        
        # Expired tokens return None from verify
        auth_service.token_manager.verify_refresh_token.return_value = None
        
        # Act
        result = await auth_service.refresh_token(refresh_token)
        
        # Assert
        assert result["success"] is False
        assert "expired" in result["message"].lower()
        assert result.get("access_token") is None


class TestAuthServiceIntegration:
    """Integration tests for AuthService workflow."""
    
    @pytest.mark.asyncio
    async def test_signup_then_login_workflow(self, auth_service, mock_user):
        """Test complete signup then login workflow."""
        # Phase 1: Signup
        signup_email = "newuser@example.com"
        signup_username = "newuser"
        signup_password = "SecurePass123!"
        
        auth_service.signup_workflow.ainvoke = AsyncMock(return_value={
            "success": True,
            "message": "User registered successfully",
            "user_id": mock_user.id,
        })
        auth_service.token_manager.create_access_token.return_value = "signup_access_token"
        auth_service.token_manager.create_refresh_token.return_value = "signup_refresh_token"
        
        signup_result = await auth_service.signup(
            signup_email, signup_username, signup_password, "Jane", "Smith"
        )
        
        assert signup_result["success"] is True
        assert signup_result["user_id"] == mock_user.id
        
        # Phase 2: Login with the new credentials
        auth_service.user_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.password_manager.verify_password.return_value = True
        auth_service.token_manager.create_access_token.return_value = "login_access_token"
        auth_service.token_manager.create_refresh_token.return_value = "login_refresh_token"
        
        login_result = await auth_service.login(signup_email, signup_password)
        
        assert login_result["success"] is True
        assert login_result["user"]["email"] == mock_user.email
        assert login_result["access_token"] == "login_access_token"
    
    @pytest.mark.asyncio
    async def test_login_then_refresh_workflow(self, auth_service, mock_user):
        """Test login followed by token refresh."""
        # Phase 1: Login
        auth_service.user_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.password_manager.verify_password.return_value = True
        auth_service.token_manager.create_access_token.return_value = "access_token"
        auth_service.token_manager.create_refresh_token.return_value = "refresh_token"
        
        login_result = await auth_service.login("test@example.com", "password123")
        
        assert login_result["success"] is True
        refresh_token = login_result["refresh_token"]
        
        # Phase 2: Refresh the token
        auth_service.token_manager.verify_refresh_token.return_value = mock_user.id
        auth_service.user_repository.get_user_by_id = AsyncMock(return_value=mock_user)
        auth_service.token_manager.create_access_token.return_value = "new_access_token"
        
        refresh_result = await auth_service.refresh_token(refresh_token)
        
        assert refresh_result["success"] is True
        assert refresh_result["access_token"] == "new_access_token"
        assert refresh_result["access_token"] != login_result["access_token"]
