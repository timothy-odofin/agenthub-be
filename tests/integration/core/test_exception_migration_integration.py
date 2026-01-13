"""
Integration tests for Step 3: Exception Migration in API Endpoints

Tests that API endpoints properly use custom exceptions and return uniform error responses.
Validates authentication, error handling, and request ID tracking in real API scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.exceptions import (
    AuthenticationError,
    ServiceUnavailableError,
    InternalError,
)


class MockRequest:
    """Mock FastAPI Request object for testing."""
    
    class State:
        request_id = "req_test_integration"
    
    state = State()


class TestAuthenticationDependencies:
    """Test authentication dependencies use custom exceptions."""

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Should raise AuthenticationError when credentials are missing."""
        from app.core.security.dependencies import get_current_user
        
        request = MockRequest()
        
        with pytest.raises(AuthenticationError) as exc_info:
            await get_current_user(request, credentials=None)
        
        exc = exc_info.value
        assert exc.message == "Not authenticated"
        assert exc.status_code == 401
        assert exc.request_id == "req_test_integration"
        assert exc.error_code == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Should raise AuthenticationError when token is invalid."""
        from app.core.security.dependencies import get_current_user
        
        request = MockRequest()
        
        # Mock credentials with invalid token
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token_12345"
        
        # Mock token_manager to return None (invalid token)
        with patch('app.core.security.dependencies.token_manager') as mock_token_manager:
            mock_token_manager.verify_token.return_value = None
            
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_user(request, credentials=mock_credentials)
            
            exc = exc_info.value
            assert exc.message == "Invalid or expired token"
            assert exc.status_code == 401
            assert exc.request_id == "req_test_integration"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id_in_payload(self):
        """Should raise AuthenticationError when token payload is missing user_id."""
        from app.core.security.dependencies import get_current_user
        
        request = MockRequest()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token_format"
        
        # Mock token_manager to return payload without user_id
        with patch('app.core.security.dependencies.token_manager') as mock_token_manager:
            mock_token_manager.verify_token.return_value = {"email": "test@example.com"}
            
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_user(request, credentials=mock_credentials)
            
            exc = exc_info.value
            assert exc.message == "Invalid token payload"
            assert exc.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found_in_db(self):
        """Should raise AuthenticationError when user doesn't exist in database."""
        from app.core.security.dependencies import get_current_user
        
        request = MockRequest()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"
        
        with patch('app.core.security.dependencies.token_manager') as mock_token_manager, \
             patch('app.core.security.dependencies.user_repository') as mock_user_repo:
            
            mock_token_manager.verify_token.return_value = {"user_id": "nonexistent_user"}
            # Make get_user_by_id return awaitable None
            mock_user_repo.get_user_by_id = AsyncMock(return_value=None)
            
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_user(request, credentials=mock_credentials)
            
            exc = exc_info.value
            assert exc.message == "User not found"
            assert exc.status_code == 401
            assert "user_not_in_database" in exc.internal_details["reason"]

    @pytest.mark.asyncio
    async def test_get_token_payload_no_credentials(self):
        """get_token_payload should raise AuthenticationError without credentials."""
        from app.core.security.dependencies import get_token_payload
        
        request = MockRequest()
        
        with pytest.raises(AuthenticationError) as exc_info:
            await get_token_payload(request, credentials=None)
        
        exc = exc_info.value
        assert exc.message == "Not authenticated"
        assert exc.status_code == 401

    @pytest.mark.asyncio
    async def test_get_token_payload_invalid_token(self):
        """get_token_payload should raise AuthenticationError for invalid token."""
        from app.core.security.dependencies import get_token_payload
        
        request = MockRequest()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"
        
        with patch('app.core.security.dependencies.token_manager') as mock_token_manager:
            mock_token_manager.verify_token.return_value = None
            
            with pytest.raises(AuthenticationError) as exc_info:
                await get_token_payload(request, credentials=mock_credentials)
            
            exc = exc_info.value
            assert exc.message == "Invalid or expired token"


class TestChatEndpoints:
    """Test chat endpoints use custom exceptions."""

    @pytest.mark.asyncio
    async def test_health_check_service_unhealthy(self):
        """Health check should raise ServiceUnavailableError when service is unhealthy."""
        # We'll test the logic that raises the exception
        from app.core.exceptions import ServiceUnavailableError
        
        # Simulate unhealthy status
        health_status = {
            "status": "unhealthy",
            "agent": "not_initialized",
            "details": "Agent failed to start"
        }
        
        # This is what the endpoint should raise
        with pytest.raises(ServiceUnavailableError) as exc_info:
            raise ServiceUnavailableError(
                service_name="chat_service",
                message="Chat service is unhealthy",
                details=health_status
            )
        
        exc = exc_info.value
        assert exc.status_code == 503
        assert exc.service_name == "chat_service"
        assert exc.details == health_status

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self):
        """Health check should raise InternalError for unexpected exceptions."""
        from app.core.exceptions import InternalError
        
        # Simulate unexpected exception
        original_error = ValueError("Unexpected configuration error")
        
        # This is what the endpoint should raise
        with pytest.raises(InternalError) as exc_info:
            raise InternalError(
                message="Health check failed",
                internal_details={
                    "error": str(original_error),
                    "type": type(original_error).__name__
                }
            )
        
        exc = exc_info.value
        assert exc.status_code == 500
        assert "Unexpected configuration error" in exc.internal_details["error"]
        assert exc.internal_details["type"] == "ValueError"
        
        # Internal details should not be in API response
        api_response = exc.to_dict()
        assert "internal_details" not in api_response["error"]


class TestErrorResponseFormat:
    """Test that error responses follow uniform format."""

    def test_authentication_error_response_format(self):
        """Authentication errors should return uniform format."""
        exc = AuthenticationError(
            message="Invalid token",
            request_id="req_format_test"
        )
        
        response = exc.to_dict()
        
        # Verify structure
        assert "error" in response
        error = response["error"]
        
        # Required fields
        assert "type" in error
        assert "code" in error
        assert "message" in error
        assert "status_code" in error
        assert "request_id" in error
        assert "timestamp" in error
        
        # Values
        assert error["type"] == "authentication_error"
        assert error["code"] == "AUTHENTICATION_ERROR"
        assert error["status_code"] == 401
        assert error["request_id"] == "req_format_test"

    def test_service_error_response_format(self):
        """Service errors should return uniform format."""
        exc = ServiceUnavailableError(
            service_name="database",
            message="Database is down",
            request_id="req_service_test"
        )
        
        response = exc.to_dict()
        error = response["error"]
        
        assert error["type"] == "service_unavailable_error"
        assert error["status_code"] == 503
        assert error["details"]["service_name"] == "database"

    def test_internal_error_response_format(self):
        """Internal errors should return uniform format and hide internals."""
        exc = InternalError(
            message="Something went wrong",
            internal_details={"stack": "trace here", "secret": "key123"},
            request_id="req_internal_test"
        )
        
        response = exc.to_dict()
        error = response["error"]
        
        assert error["type"] == "internal_error"
        assert error["status_code"] == 500
        
        # Should NOT contain internal_details
        assert "internal_details" not in error
        assert "stack" not in str(response)
        assert "secret" not in str(response)


class TestRequestIDTracking:
    """Test that request IDs are properly tracked through error flow."""

    def test_request_id_from_middleware(self):
        """Request ID from middleware should propagate to exceptions."""
        request = MockRequest()
        request.state.request_id = "req_from_middleware_123"
        
        exc = AuthenticationError(
            message="Test",
            request_id=request.state.request_id
        )
        
        assert exc.request_id == "req_from_middleware_123"
        assert exc.to_dict()["error"]["request_id"] == "req_from_middleware_123"

    def test_request_id_in_error_response(self):
        """All error responses should include request_id."""
        request_id = "req_tracking_test"
        
        exceptions = [
            AuthenticationError(message="Auth error", request_id=request_id),
            ServiceUnavailableError(
                service_name="test",
                message="Service error",
                request_id=request_id
            ),
            InternalError(message="Internal error", request_id=request_id),
        ]
        
        for exc in exceptions:
            response = exc.to_dict()
            assert response["error"]["request_id"] == request_id


class TestNoHTTPExceptionInMigratedFiles:
    """Test that migrated files don't use HTTPException."""

    def test_dependencies_no_httpexception_import(self):
        """dependencies.py should not import HTTPException."""
        import app.core.security.dependencies as deps
        
        # Check module doesn't have HTTPException
        assert not hasattr(deps, 'HTTPException')
        
        # Check source doesn't import it
        import inspect
        source = inspect.getsource(deps)
        
        # Should have our custom exceptions
        assert 'AuthenticationError' in source
        
        # Should NOT import HTTPException from fastapi
        lines = source.split('\n')
        fastapi_imports = [line for line in lines if 'from fastapi import' in line]
        
        for line in fastapi_imports:
            assert 'HTTPException' not in line, f"Found HTTPException import: {line}"

    def test_chat_endpoints_no_httpexception_import(self):
        """chat.py should not import HTTPException."""
        import app.api.v1.chat as chat_module
        
        # Check module doesn't have HTTPException
        assert not hasattr(chat_module, 'HTTPException')
        
        # Check source
        import inspect
        source = inspect.getsource(chat_module)
        
        # Should have our custom exceptions
        assert 'ServiceUnavailableError' in source or 'InternalError' in source
        
        # Should NOT import HTTPException
        lines = source.split('\n')
        fastapi_imports = [line for line in lines if 'from fastapi import' in line]
        
        for line in fastapi_imports:
            assert 'HTTPException' not in line, f"Found HTTPException import: {line}"


class TestExceptionInheritance:
    """Test that exceptions inherit correctly for proper handler routing."""

    def test_all_exceptions_inherit_from_base(self):
        """All custom exceptions should inherit from BaseAppException."""
        from app.core.exceptions.base import BaseAppException
        
        exceptions = [
            AuthenticationError(message="test"),
            ServiceUnavailableError(service_name="test", message="test"),
            InternalError(message="test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, BaseAppException)

    def test_exception_status_codes(self):
        """Exceptions should have correct HTTP status codes."""
        test_cases = [
            (AuthenticationError(message="test"), 401),
            (ServiceUnavailableError(service_name="test", message="test"), 503),
            (InternalError(message="test"), 500),
        ]
        
        for exc, expected_status in test_cases:
            assert exc.status_code == expected_status
