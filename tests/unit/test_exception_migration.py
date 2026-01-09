"""
Unit tests for Step 3: Exception Migration

Tests that all migrated code properly uses custom exceptions instead of HTTPException.
Validates error formats, request ID tracking, and exception behavior.
"""

import pytest
from datetime import datetime
from typing import Optional

from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    ServiceUnavailableError,
    InternalError,
    NotFoundError,
)


class TestExceptionFormats:
    """Test that all exceptions return uniform formats."""

    def test_authentication_error_format(self):
        """AuthenticationError should have uniform format with 401 status."""
        exc = AuthenticationError(
            message="Invalid token",
            request_id="req_test_001"
        )
        
        error_dict = exc.to_dict()
        
        assert "error" in error_dict
        assert error_dict["error"]["type"] == "authentication_error"
        assert error_dict["error"]["code"] == "AUTHENTICATION_ERROR"
        assert error_dict["error"]["message"] == "Invalid token"
        assert error_dict["error"]["status_code"] == 401
        assert error_dict["error"]["request_id"] == "req_test_001"
        assert "timestamp" in error_dict["error"]

    def test_validation_error_format(self):
        """ValidationError should include field information."""
        exc = ValidationError(
            message="Invalid email format",
            field="email",
            request_id="req_test_002"
        )
        
        error_dict = exc.to_dict()
        
        assert error_dict["error"]["type"] == "validation_error"
        assert error_dict["error"]["status_code"] == 400
        assert error_dict["error"]["details"]["field"] == "email"

    def test_service_unavailable_error_format(self):
        """ServiceUnavailableError should include service name."""
        exc = ServiceUnavailableError(
            service_name="chat_agent",
            message="Service is down",
            request_id="req_test_003"
        )
        
        error_dict = exc.to_dict()
        
        assert error_dict["error"]["type"] == "service_unavailable_error"
        assert error_dict["error"]["status_code"] == 503
        assert error_dict["error"]["details"]["service_name"] == "chat_agent"

    def test_internal_error_format(self):
        """InternalError should hide internal_details from API response."""
        exc = InternalError(
            message="Something went wrong",
            internal_details={
                "stack_trace": "line 1\nline 2",
                "sensitive_data": "secret_key_123"
            },
            request_id="req_test_004"
        )
        
        error_dict = exc.to_dict()
        
        assert error_dict["error"]["type"] == "internal_error"
        assert error_dict["error"]["status_code"] == 500
        # Internal details should NOT be in API response
        assert "internal_details" not in error_dict["error"]
        assert "stack_trace" not in str(error_dict)
        assert "sensitive_data" not in str(error_dict)

    def test_not_found_error_format(self):
        """NotFoundError should include resource information."""
        exc = NotFoundError(
            resource_type="user",
            resource_id="12345",
            request_id="req_test_005"
        )
        
        error_dict = exc.to_dict()
        
        assert error_dict["error"]["type"] == "not_found_error"
        assert error_dict["error"]["status_code"] == 404
        assert error_dict["error"]["details"]["resource_type"] == "user"
        assert error_dict["error"]["details"]["resource_id"] == "12345"


class TestRequestIDPropagation:
    """Test that request IDs propagate correctly through exceptions."""

    def test_request_id_in_exception(self):
        """Request ID should be included in exception."""
        request_id = "req_propagation_test"
        
        exc = ValidationError(
            message="Test error",
            request_id=request_id
        )
        
        assert exc.request_id == request_id
        assert exc.to_dict()["error"]["request_id"] == request_id

    def test_request_id_in_log_context(self):
        """Request ID should be in log context."""
        request_id = "req_log_test"
        
        exc = AuthenticationError(
            message="Test auth error",
            request_id=request_id
        )
        
        log_context = exc.get_log_context()
        assert log_context["request_id"] == request_id

    def test_optional_request_id(self):
        """Request ID should be optional (can be None and not included in response)."""
        exc = ValidationError(message="Test without request_id")
        
        assert exc.request_id is None
        error_dict = exc.to_dict()
        # Request ID should not be in response if it's None (cleaner API)
        assert "request_id" not in error_dict["error"]


class TestLogContext:
    """Test that log contexts contain proper information without conflicts."""

    def test_log_context_uses_error_message(self):
        """Log context should use 'error_message' not 'message' (reserved field)."""
        exc = ValidationError(
            message="Test message",
            request_id="req_test"
        )
        
        log_context = exc.get_log_context()
        
        # Should use 'error_message' to avoid Python logging conflict
        assert "error_message" in log_context
        assert "message" not in log_context
        assert log_context["error_message"] == "Test message"

    def test_log_context_includes_internal_details(self):
        """Log context should include internal_details for debugging."""
        internal_data = {
            "database": "test_db",
            "query": "SELECT * FROM users"
        }
        
        exc = InternalError(
            message="Database error",
            internal_details=internal_data,
            request_id="req_test"
        )
        
        log_context = exc.get_log_context()
        
        assert log_context["internal_details"] == internal_data

    def test_log_context_no_reserved_fields(self):
        """Log context should not contain Python logging reserved fields."""
        exc = AuthenticationError(
            message="Test",
            request_id="req_test"
        )
        
        log_context = exc.get_log_context()
        
        # Python logging reserved fields that should NOT be in extra dict
        reserved_fields = [
            "message",  # We use 'error_message' instead
            "args",
            "name",
            "levelname",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
        ]
        
        for field in reserved_fields:
            assert field not in log_context, f"Reserved field '{field}' found in log context"


class TestSecurityImplications:
    """Test that security concerns are properly addressed."""

    def test_sensitive_data_not_in_api_response(self):
        """Sensitive data in internal_details should never appear in API response."""
        sensitive_data = {
            "password": "super_secret_password",
            "api_key": "sk_live_123456789",
            "connection_string": "postgresql://user:pass@localhost/db"
        }
        
        exc = InternalError(
            message="Connection failed",
            internal_details=sensitive_data
        )
        
        api_response = exc.to_dict()
        response_str = str(api_response)
        
        # Sensitive data should NOT appear anywhere in API response
        assert "super_secret_password" not in response_str
        assert "sk_live_123456789" not in response_str
        assert "postgresql://user:pass" not in response_str

    def test_stack_traces_not_exposed(self):
        """Stack traces should not be exposed in API responses."""
        exc = InternalError(
            message="Internal error",
            internal_details={
                "traceback": "Traceback (most recent call last):\n  File 'test.py'..."
            }
        )
        
        api_response = exc.to_dict()
        
        assert "traceback" not in str(api_response["error"])
        assert "Traceback" not in str(api_response["error"])


class TestExceptionHierarchy:
    """Test that exception hierarchy works as expected."""

    def test_authentication_error_is_client_error(self):
        """AuthenticationError should be a ClientError."""
        from app.core.exceptions.base import ClientError
        
        exc = AuthenticationError(message="Test")
        assert isinstance(exc, ClientError)

    def test_internal_error_is_server_error(self):
        """InternalError should be a ServerError."""
        from app.core.exceptions.base import ServerError
        
        exc = InternalError(message="Test")
        assert isinstance(exc, ServerError)

    def test_service_unavailable_is_server_error(self):
        """ServiceUnavailableError should be a ServerError."""
        from app.core.exceptions.base import ServerError
        
        exc = ServiceUnavailableError(service_name="test", message="Test")
        assert isinstance(exc, ServerError)


class TestTimestampBehavior:
    """Test that timestamps are properly handled."""

    def test_timestamp_auto_generated(self):
        """Timestamp should be auto-generated if not provided."""
        exc = ValidationError(message="Test")
        
        assert exc.timestamp is not None
        assert isinstance(exc.timestamp, datetime)

    def test_timestamp_in_api_response(self):
        """Timestamp should be in API response in ISO format."""
        exc = ValidationError(message="Test")
        
        error_dict = exc.to_dict()
        timestamp_str = error_dict["error"]["timestamp"]
        
        # Should be ISO 8601 format
        assert "T" in timestamp_str
        assert "Z" in timestamp_str or "+" in timestamp_str or "-" in timestamp_str[-6:]

    def test_timestamp_consistent(self):
        """Timestamp should be consistent across to_dict() calls."""
        exc = ValidationError(message="Test")
        
        timestamp1 = exc.to_dict()["error"]["timestamp"]
        timestamp2 = exc.to_dict()["error"]["timestamp"]
        
        assert timestamp1 == timestamp2


class TestDetailsAndInternalDetails:
    """Test the difference between details (public) and internal_details (private)."""

    def test_details_in_api_response(self):
        """Details should appear in API response."""
        exc = ValidationError(
            message="Invalid input",
            field="email",
            details={"expected_format": "email@example.com"}
        )
        
        error_dict = exc.to_dict()
        
        assert "details" in error_dict["error"]
        assert error_dict["error"]["details"]["field"] == "email"
        assert error_dict["error"]["details"]["expected_format"] == "email@example.com"

    def test_internal_details_not_in_api_response(self):
        """Internal details should NOT appear in API response."""
        exc = InternalError(
            message="Error",
            internal_details={"secret": "value"}
        )
        
        error_dict = exc.to_dict()
        
        assert "internal_details" not in error_dict["error"]

    def test_internal_details_in_log_context(self):
        """Internal details should appear in log context."""
        internal = {"database": "test", "query": "SELECT *"}
        exc = InternalError(
            message="Error",
            internal_details=internal
        )
        
        log_context = exc.get_log_context()
        
        assert log_context["internal_details"] == internal
