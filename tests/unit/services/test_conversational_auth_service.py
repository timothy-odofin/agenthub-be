"""
Unit tests for ConversationalAuthService.
Tests the business logic of conversational authentication operations including:
- Registry design pattern
- LLM-based field extraction
- Email and username uniqueness validation
- Simplified password validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from src.app.services.conversational_auth_service import ConversationalAuthService
from src.app.schemas.conversational_auth import (
    SignupStep,
    ConversationalSignupRequest,
    ConversationalSignupResponse,
)
from src.app.db.models.user import UserInDB


@pytest.fixture
def mock_settings():
    """Mock settings with conversational auth prompts."""
    mock_prompts = MagicMock()
    mock_prompts.start = "👋 Welcome! Let's create your account. What's your email address?"
    mock_prompts.email_success = "Great! Now choose a username (3-30 characters, letters, numbers, _ or -)."
    mock_prompts.username_success = "Perfect! Create a password (min 8 characters, at least one uppercase, one lowercase, and one number)."
    mock_prompts.password_success = "Excellent! What's your first name?"
    mock_prompts.firstname_success = "Almost there! What's your last name?"
    mock_prompts.complete = "🎉 Welcome aboard, {firstname}! Your account has been created successfully!"
    
    mock_extraction = MagicMock()
    mock_extraction.system = "You are a field extractor."
    mock_extraction.user_template = "Extract {field_type} from: {user_message}"
    
    mock_validation_errors = MagicMock()
    mock_validation_errors.email_invalid = "❌ That doesn't look like a valid email."
    mock_validation_errors.email_exists = "❌ This email is already registered."
    mock_validation_errors.username_invalid = "❌ Username must be 3-30 characters."
    mock_validation_errors.username_exists = "❌ This username is already taken."
    mock_validation_errors.password_weak = "❌ Password must be at least 8 characters and include: {requirements}."
    mock_validation_errors.firstname_invalid = "❌ Please enter a valid first name."
    mock_validation_errors.lastname_invalid = "❌ Please enter a valid last name."
    mock_validation_errors.signup_error = "❌ Oops! Something went wrong: {error}."
    
    mock_conv_auth = MagicMock()
    mock_conv_auth.prompts = mock_prompts
    mock_conv_auth.extraction.universal = mock_extraction
    mock_conv_auth.validation_errors = mock_validation_errors
    
    mock_settings_obj = MagicMock()
    mock_settings_obj.prompt.conversational_auth = mock_conv_auth
    
    return mock_settings_obj


@pytest.fixture
def mock_llm():
    """Mock LLM for field extraction."""
    mock = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "extracted_value"
    mock.ainvoke = AsyncMock(return_value=mock_response)
    return mock


@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    return AsyncMock()


@pytest.fixture
def mock_auth_service():
    """Mock auth service."""
    return AsyncMock()


@pytest.fixture
def conversational_auth_service(mock_settings, mock_llm, mock_user_repository, mock_auth_service):
    """Create ConversationalAuthService instance with mocked dependencies."""
    with patch('src.app.services.conversational_auth_service.settings', mock_settings), \
         patch('src.app.services.conversational_auth_service.LLMFactory') as mock_factory, \
         patch('src.app.services.conversational_auth_service.user_repository', mock_user_repository), \
         patch('src.app.services.conversational_auth_service.auth_service', mock_auth_service):
        
        # Mock the LLM factory to return our mock LLM (matching chat_service pattern)
        mock_factory.get_llm.return_value = mock_llm
        
        service = ConversationalAuthService()
        service.llm = mock_llm
        
        yield service


class TestConversationalAuthServiceInit:
    """Test suite for ConversationalAuthService initialization."""
    
    def test_init_loads_prompts_from_config(self, conversational_auth_service):
        """Test that initialization loads prompts from configuration."""
        assert conversational_auth_service.prompts is not None
        assert conversational_auth_service.extraction_config is not None
        assert conversational_auth_service.validation_errors is not None
    
    def test_init_creates_step_handlers_registry(self, conversational_auth_service):
        """Test that initialization creates registry of step handlers."""
        assert hasattr(conversational_auth_service, '_step_handlers')
        assert SignupStep.EMAIL in conversational_auth_service._step_handlers
        assert SignupStep.USERNAME in conversational_auth_service._step_handlers
        assert SignupStep.PASSWORD in conversational_auth_service._step_handlers
        assert SignupStep.FIRSTNAME in conversational_auth_service._step_handlers
        assert SignupStep.LASTNAME in conversational_auth_service._step_handlers
    
    def test_init_assigns_correct_handlers(self, conversational_auth_service):
        """Test that registry maps to correct handler methods."""
        assert conversational_auth_service._step_handlers[SignupStep.EMAIL] == conversational_auth_service._process_email
        assert conversational_auth_service._step_handlers[SignupStep.USERNAME] == conversational_auth_service._process_username
        assert conversational_auth_service._step_handlers[SignupStep.PASSWORD] == conversational_auth_service._process_password
        assert conversational_auth_service._step_handlers[SignupStep.FIRSTNAME] == conversational_auth_service._process_firstname
        assert conversational_auth_service._step_handlers[SignupStep.LASTNAME] == conversational_auth_service._process_lastname


class TestLLMExtraction:
    """Test suite for LLM-based field extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_field_from_message_success(self, conversational_auth_service):
        """Test successful field extraction using LLM."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "john@example.com"
        conversational_auth_service.llm.generate.return_value = mock_response
        
        # Act
        result = await conversational_auth_service._extract_field_from_message(
            "My email is john@example.com",
            "email address"
        )
        
        # Assert
        assert result == "john@example.com"
        conversational_auth_service.llm.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_field_removes_quotes(self, conversational_auth_service):
        """Test that extraction removes quotes added by LLM."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = '"johndoe"'
        conversational_auth_service.llm.generate.return_value = mock_response
        
        # Act
        result = await conversational_auth_service._extract_field_from_message(
            "You can call me johndoe",
            "username"
        )
        
        # Assert
        assert result == "johndoe"
    
    @pytest.mark.asyncio
    async def test_extract_field_handles_single_quotes(self, conversational_auth_service):
        """Test that extraction removes single quotes added by LLM."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "'johndoe'"
        conversational_auth_service.llm.generate.return_value = mock_response
        
        # Act
        result = await conversational_auth_service._extract_field_from_message(
            "Call me 'johndoe'",
            "username"
        )
        
        # Assert
        assert result == "johndoe"
    
    @pytest.mark.asyncio
    async def test_extract_field_fallback_on_error(self, conversational_auth_service):
        """Test that extraction falls back to original message on error."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock(side_effect=Exception("LLM error"))
        
        # Act
        result = await conversational_auth_service._extract_field_from_message(
            "john@example.com",
            "email address"
        )
        
        # Assert
        assert result == "john@example.com"


class TestProcessSignupStepRegistryPattern:
    """Test suite for process_signup_step using registry pattern."""
    
    @pytest.mark.asyncio
    async def test_process_start_step(self, conversational_auth_service):
        """Test processing START step returns welcome message."""
        # Arrange
        request = ConversationalSignupRequest(
            message="Hi",
            current_step=SignupStep.START
        )
        
        # Act
        response = await conversational_auth_service.process_signup_step(request)
        
        # Assert
        assert response.success is True
        assert response.next_step == SignupStep.EMAIL
        assert response.session_id is not None
        assert response.progress_percentage == 0
        assert response.fields_remaining == 5
    
    @pytest.mark.asyncio
    async def test_process_step_uses_registry(self, conversational_auth_service):
        """Test that process_signup_step uses registry to dispatch to handler."""
        # Arrange
        request = ConversationalSignupRequest(
            message="john@example.com",
            current_step=SignupStep.EMAIL,
            session_id="test-session-123"
        )
        
        # Mock the handler by replacing it in the registry
        mock_response = ConversationalSignupResponse(
            success=True,
            message="Email processed",
            next_step=SignupStep.USERNAME,
            session_id="test-session-123",
            progress_percentage=20,
            fields_remaining=4
        )
        mock_handler = AsyncMock(return_value=mock_response)
        conversational_auth_service._step_handlers[SignupStep.EMAIL] = mock_handler
        
        # Act
        response = await conversational_auth_service.process_signup_step(request)
        
        # Assert
        assert response.success is True
        assert response.message == "Email processed"
        mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_step_generates_session_id(self, conversational_auth_service):
        """Test that process_signup_step generates session_id if not provided."""
        # Arrange
        request = ConversationalSignupRequest(
            message="Hi",
            current_step=SignupStep.START
        )
        
        # Act
        response = await conversational_auth_service.process_signup_step(request)
        
        # Assert
        assert response.session_id is not None
        assert len(response.session_id) > 0
    
    @pytest.mark.asyncio
    async def test_process_step_invalid_step(self, conversational_auth_service):
        """Test handling of invalid step."""
        # Arrange - Remove handler from registry
        conversational_auth_service._step_handlers.clear()
        
        request = ConversationalSignupRequest(
            message="test",
            current_step=SignupStep.EMAIL
        )
        
        # Act
        response = await conversational_auth_service.process_signup_step(request)
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert response.next_step == SignupStep.START


class TestEmailValidation:
    """Test suite for email validation with uniqueness check."""
    
    @pytest.mark.asyncio
    async def test_process_email_valid_and_unique(self, conversational_auth_service):
        """Test processing valid and unique email."""
        # Arrange
        with patch('src.app.services.conversational_auth_service.user_repository') as mock_repo:
            mock_repo.get_user_by_email = AsyncMock(return_value=None)
            
            conversational_auth_service.llm.generate = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "john@example.com"
            conversational_auth_service.llm.generate.return_value = mock_response
            
            request = ConversationalSignupRequest(
                message="My email is john@example.com",
                current_step=SignupStep.EMAIL
            )
            
            # Act
            response = await conversational_auth_service._process_email(request, "session-123")
            
            # Assert
            assert response.success is True
            assert response.next_step == SignupStep.USERNAME
            assert response.progress_percentage == 20
            assert response.fields_remaining == 4
            mock_repo.get_user_by_email.assert_called_once_with("john@example.com")
    
    @pytest.mark.asyncio
    async def test_process_email_invalid_format(self, conversational_auth_service):
        """Test processing email with invalid format."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "not-an-email"
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="not-an-email",
            current_step=SignupStep.EMAIL
        )
        
        # Act
        response = await conversational_auth_service._process_email(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert response.next_step == SignupStep.EMAIL
        assert response.validation_error == "Invalid email format"
    
    @pytest.mark.asyncio
    async def test_process_email_already_exists(self, conversational_auth_service):
        """Test processing email that already exists in database."""
        # Arrange
        with patch('src.app.services.conversational_auth_service.user_repository') as mock_repo:
            # Mock existing user
            existing_user = UserInDB(
                id=str(ObjectId()),
                email="john@example.com",
                username="john",
                password_hash="hash",
                firstname="John",
                lastname="Doe",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_repo.get_user_by_email = AsyncMock(return_value=existing_user)
            
            conversational_auth_service.llm.generate = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "john@example.com"
            conversational_auth_service.llm.generate.return_value = mock_response
            
            request = ConversationalSignupRequest(
                message="john@example.com",
                current_step=SignupStep.EMAIL
            )
            
            # Act
            response = await conversational_auth_service._process_email(request, "session-123")
            
            # Assert
            assert response.success is False
            assert response.is_valid is False
            assert response.next_step == SignupStep.EMAIL
            assert response.validation_error == "Email already registered"
            mock_repo.get_user_by_email.assert_called_once_with("john@example.com")


class TestUsernameValidation:
    """Test suite for username validation with uniqueness check."""
    
    @pytest.mark.asyncio
    async def test_process_username_valid_and_unique(self, conversational_auth_service):
        """Test processing valid and unique username."""
        # Arrange
        with patch('src.app.services.conversational_auth_service.user_repository') as mock_repo:
            mock_repo.get_user_by_username = AsyncMock(return_value=None)
            
            conversational_auth_service.llm.generate = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "johndoe"
            conversational_auth_service.llm.generate.return_value = mock_response
            
            request = ConversationalSignupRequest(
                message="Call me johndoe",
                current_step=SignupStep.USERNAME
            )
            
            # Act
            response = await conversational_auth_service._process_username(request, "session-123")
            
            # Assert
            assert response.success is True
            assert response.next_step == SignupStep.PASSWORD
            assert response.progress_percentage == 40
            assert response.fields_remaining == 3
            mock_repo.get_user_by_username.assert_called_once_with("johndoe")
    
    @pytest.mark.asyncio
    async def test_process_username_invalid_format(self, conversational_auth_service):
        """Test processing username with invalid format."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "ab"  # Too short
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="ab",
            current_step=SignupStep.USERNAME
        )
        
        # Act
        response = await conversational_auth_service._process_username(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert response.next_step == SignupStep.USERNAME
        assert response.validation_error == "Invalid username format"
    
    @pytest.mark.asyncio
    async def test_process_username_already_exists(self, conversational_auth_service):
        """Test processing username that already exists in database."""
        # Arrange
        with patch('src.app.services.conversational_auth_service.user_repository') as mock_repo:
            # Mock existing user
            existing_user = UserInDB(
                id=str(ObjectId()),
                email="john@example.com",
                username="johndoe",
                password_hash="hash",
                firstname="John",
                lastname="Doe",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_repo.get_user_by_username = AsyncMock(return_value=existing_user)
            
            conversational_auth_service.llm.generate = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "johndoe"
            conversational_auth_service.llm.generate.return_value = mock_response
            
            request = ConversationalSignupRequest(
                message="johndoe",
                current_step=SignupStep.USERNAME
            )
            
            # Act
            response = await conversational_auth_service._process_username(request, "session-123")
            
            # Assert
            assert response.success is False
            assert response.is_valid is False
            assert response.next_step == SignupStep.USERNAME
            assert response.validation_error == "Username already taken"
            mock_repo.get_user_by_username.assert_called_once_with("johndoe")


class TestPasswordValidationSimplified:
    """Test suite for simplified password validation."""
    
    @pytest.mark.asyncio
    async def test_process_password_valid(self, conversational_auth_service):
        """Test processing valid password (8+ chars, 1 upper, 1 lower, 1 number)."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Password123"
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="Password123",
            current_step=SignupStep.PASSWORD
        )
        
        # Act
        response = await conversational_auth_service._process_password(request, "session-123")
        
        # Assert
        assert response.success is True
        assert response.next_step == SignupStep.FIRSTNAME
        assert response.progress_percentage == 60
        assert response.fields_remaining == 2
    
    @pytest.mark.asyncio
    async def test_process_password_too_short(self, conversational_auth_service):
        """Test processing password that's too short."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Pass1"  # Only 5 chars
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="Pass1",
            current_step=SignupStep.PASSWORD
        )
        
        # Act
        response = await conversational_auth_service._process_password(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert response.validation_error == "Weak password"
        assert "at least 8 characters" in response.message
    
    @pytest.mark.asyncio
    async def test_process_password_no_uppercase(self, conversational_auth_service):
        """Test processing password without uppercase letter."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "password123"  # No uppercase
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="password123",
            current_step=SignupStep.PASSWORD
        )
        
        # Act
        response = await conversational_auth_service._process_password(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert "one uppercase letter" in response.message
    
    @pytest.mark.asyncio
    async def test_process_password_no_lowercase(self, conversational_auth_service):
        """Test processing password without lowercase letter."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "PASSWORD123"  # No lowercase
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="PASSWORD123",
            current_step=SignupStep.PASSWORD
        )
        
        # Act
        response = await conversational_auth_service._process_password(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert "one lowercase letter" in response.message
    
    @pytest.mark.asyncio
    async def test_process_password_no_number(self, conversational_auth_service):
        """Test processing password without number."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Password"  # No number
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="Password",
            current_step=SignupStep.PASSWORD
        )
        
        # Act
        response = await conversational_auth_service._process_password(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert "one number" in response.message
    
    @pytest.mark.asyncio
    async def test_process_password_no_special_char_required(self, conversational_auth_service):
        """Test that password WITHOUT special character is valid (simplified requirement)."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Password123"  # No special char but should be valid
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="Password123",
            current_step=SignupStep.PASSWORD
        )
        
        # Act
        response = await conversational_auth_service._process_password(request, "session-123")
        
        # Assert
        assert response.success is True
        assert response.next_step == SignupStep.FIRSTNAME


class TestNameValidation:
    """Test suite for first name and last name validation."""
    
    @pytest.mark.asyncio
    async def test_process_firstname_valid(self, conversational_auth_service):
        """Test processing valid first name."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "John"
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="John",
            current_step=SignupStep.FIRSTNAME
        )
        
        # Act
        response = await conversational_auth_service._process_firstname(request, "session-123")
        
        # Assert
        assert response.success is True
        assert response.next_step == SignupStep.LASTNAME
        assert response.progress_percentage == 80
        assert response.fields_remaining == 1
    
    @pytest.mark.asyncio
    async def test_process_firstname_invalid(self, conversational_auth_service):
        """Test processing invalid first name."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "123"  # Numbers not allowed
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="123",
            current_step=SignupStep.FIRSTNAME
        )
        
        # Act
        response = await conversational_auth_service._process_firstname(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert response.validation_error == "Invalid first name"
    
    @pytest.mark.asyncio
    async def test_process_lastname_valid_completes_signup(self, conversational_auth_service):
        """Test processing valid last name completes signup."""
        # Arrange
        with patch('src.app.services.conversational_auth_service.auth_service') as mock_auth:
            mock_auth.signup = AsyncMock(return_value={
                "success": True,
                "user_id": "user-123",
                "access_token": "access-token",
                "refresh_token": "refresh-token"
            })
            
            conversational_auth_service.llm.generate = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Doe"
            conversational_auth_service.llm.generate.return_value = mock_response
            
            request = ConversationalSignupRequest(
                message="Doe",
                current_step=SignupStep.LASTNAME,
                email="john@example.com",
                username="johndoe",
                password="Password123",
                firstname="John"
            )
            
            # Act
            response = await conversational_auth_service._process_lastname(request, "session-123")
            
            # Assert
            assert response.success is True
            assert response.next_step == SignupStep.COMPLETE
            assert response.user_id == "user-123"
            assert response.access_token == "access-token"
            assert response.refresh_token == "refresh-token"
            assert response.progress_percentage == 100
            assert response.fields_remaining == 0
            
            # Verify signup was called with correct data
            mock_auth.signup.assert_called_once_with(
                email="john@example.com",
                username="johndoe",
                password="Password123",
                firstname="John",
                lastname="Doe"
            )
    
    @pytest.mark.asyncio
    async def test_process_lastname_invalid(self, conversational_auth_service):
        """Test processing invalid last name."""
        # Arrange
        conversational_auth_service.llm.generate = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = ""  # Empty not allowed
        conversational_auth_service.llm.generate.return_value = mock_response
        
        request = ConversationalSignupRequest(
            message="",
            current_step=SignupStep.LASTNAME,
            firstname="John"
        )
        
        # Act
        response = await conversational_auth_service._process_lastname(request, "session-123")
        
        # Assert
        assert response.success is False
        assert response.is_valid is False
        assert response.validation_error == "Invalid last name"
    
    @pytest.mark.asyncio
    async def test_process_lastname_signup_error(self, conversational_auth_service):
        """Test handling signup error during last name processing."""
        # Arrange
        with patch('src.app.services.conversational_auth_service.auth_service') as mock_auth:
            mock_auth.signup = AsyncMock(side_effect=Exception("Database error"))
            
            conversational_auth_service.llm.generate = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Doe"
            conversational_auth_service.llm.generate.return_value = mock_response
            
            request = ConversationalSignupRequest(
                message="Doe",
                current_step=SignupStep.LASTNAME,
                email="john@example.com",
                username="johndoe",
                password="Password123",
                firstname="John"
            )
            
            # Act
            response = await conversational_auth_service._process_lastname(request, "session-123")
            
            # Assert
            assert response.success is False
            assert response.is_valid is False
            assert "Database error" in response.validation_error


class TestValidationPatterns:
    """Test suite for validation regex patterns."""
    
    def test_email_pattern_valid(self, conversational_auth_service):
        """Test email validation pattern with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@test.com",
        ]
        
        for email in valid_emails:
            assert conversational_auth_service.EMAIL_PATTERN.match(email), f"{email} should be valid"
    
    def test_email_pattern_invalid(self, conversational_auth_service):
        """Test email validation pattern with invalid emails."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
        ]
        
        for email in invalid_emails:
            assert not conversational_auth_service.EMAIL_PATTERN.match(email), f"{email} should be invalid"
    
    def test_username_pattern_valid(self, conversational_auth_service):
        """Test username validation pattern with valid usernames."""
        valid_usernames = [
            "user",
            "user123",
            "user_name",
            "user-name",
            "a1b",  # Minimum 3 chars
        ]
        
        for username in valid_usernames:
            assert conversational_auth_service.USERNAME_PATTERN.match(username), f"{username} should be valid"
    
    def test_username_pattern_invalid(self, conversational_auth_service):
        """Test username validation pattern with invalid usernames."""
        invalid_usernames = [
            "ab",  # Too short
            "user@name",  # Invalid character
            "user name",  # Space not allowed
            "a" * 31,  # Too long
        ]
        
        for username in invalid_usernames:
            assert not conversational_auth_service.USERNAME_PATTERN.match(username), f"{username} should be invalid"
    
    def test_password_pattern_simplified(self, conversational_auth_service):
        """Test simplified password pattern (no special char required)."""
        # Valid passwords (8+ chars, 1 upper, 1 lower, 1 number)
        valid_passwords = [
            "Password123",
            "Admin2024",
            "MySecurePass1",
            "Testing1",
        ]
        
        for password in valid_passwords:
            assert conversational_auth_service.PASSWORD_PATTERN.match(password), f"{password} should be valid"
        
        # Invalid passwords
        invalid_passwords = [
            "Pass1",  # Too short
            "password123",  # No uppercase
            "PASSWORD123",  # No lowercase
            "Password",  # No number
        ]
        
        for password in invalid_passwords:
            assert not conversational_auth_service.PASSWORD_PATTERN.match(password), f"{password} should be invalid"
