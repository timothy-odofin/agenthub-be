"""
Base Exception Classes

Provides the foundation for all custom exceptions in AgentHub.
Each exception includes:
- HTTP status code for API responses
- Error code for machine-readable identification
- User-friendly message
- Additional context for logging
- Request ID for tracing
"""

from typing import Any, Dict, Optional
from datetime import datetime


class BaseAppException(Exception):
    """
    Base exception for all custom application exceptions.
    
    Attributes:
        status_code: HTTP status code for API responses
        error_code: Machine-readable error code (e.g., "AGENT_001")
        message: Human-readable error message
        details: Additional context (sanitized for client response)
        internal_details: Internal context (for logging only, never exposed to client)
        request_id: Correlation ID for distributed tracing
    """
    
    status_code: int = 500
    error_code: str = "UNKNOWN_ERROR"
    error_type: str = "application_error"
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.error_code
        self.details = details or {}
        self.internal_details = internal_details or {}
        self.request_id = request_id
        self.timestamp = datetime.utcnow()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API response.
        Only includes sanitized information safe for client consumption.
        """
        error_dict = {
            "error": {
                "type": self.error_type,
                "code": self.error_code,
                "message": self.message,
                "status_code": self.status_code,
                "timestamp": self.timestamp.isoformat() + "Z",
            }
        }
        
        if self.details:
            error_dict["error"]["details"] = self.details
        
        if self.request_id is not None:
            error_dict["error"]["request_id"] = self.request_id
        
        return error_dict
    
    def get_log_context(self) -> Dict[str, Any]:
        """
        Get full context for logging (includes internal details).
        Note: Uses 'error_message' instead of 'message' to avoid conflicts
        with Python logging's reserved 'message' field.
        """
        return {
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error_message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "internal_details": self.internal_details,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }


class ClientError(BaseAppException):
    """
    Base class for client errors (4xx).
    These errors are caused by the client (user's mistake).
    Should be logged at INFO or WARN level.
    """
    
    status_code: int = 400
    error_type: str = "client_error"
    error_code: str = "CLIENT_ERROR"


class ServerError(BaseAppException):
    """
    Base class for server errors (5xx).
    These errors are caused by the server (our fault).
    Should be logged at ERROR level and trigger alerts.
    """
    
    status_code: int = 500
    error_type: str = "server_error"
    error_code: str = "SERVER_ERROR"


class ExternalServiceError(BaseAppException):
    """
    Base class for external service errors.
    These errors are caused by dependencies (database, cache, external APIs).
    Should be logged at WARN or ERROR level depending on severity.
    May trigger circuit breakers or retry logic.
    """
    
    status_code: int = 503
    error_type: str = "external_service_error"
    error_code: str = "EXTERNAL_SERVICE_ERROR"
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        internal_details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.service_name = service_name
        
        # Add service name to internal details
        if internal_details is None:
            internal_details = {}
        if service_name:
            internal_details["service_name"] = service_name
        
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            internal_details=internal_details,
            request_id=request_id,
        )
