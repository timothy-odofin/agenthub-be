"""
Server Error Exceptions (5xx)

These exceptions represent errors caused by the server (bugs, misconfigurations, timeouts, etc.).
They should be logged at ERROR level and may trigger alerts/notifications.
"""

from typing import Any, Dict, Optional
from .base import ServerError


class InternalError(ServerError):
    """
    Raised for unexpected internal server errors.
    HTTP Status: 500 Internal Server Error
    """
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    error_type: str = "internal_error"
    
    def __init__(
        self,
        message: str = "An internal error occurred",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class ServiceUnavailableError(ServerError):
    """
    Raised when service is temporarily unavailable (maintenance, overload, etc.).
    HTTP Status: 503 Service Unavailable
    """
    
    status_code: int = 503
    error_code: str = "SERVICE_UNAVAILABLE"
    error_type: str = "service_unavailable_error"
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        # Store service_name as instance attribute for test access
        self.service_name = service_name
        
        details = kwargs.get("details", {})
        if service_name:
            details["service_name"] = service_name
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        kwargs["details"] = details
        super().__init__(message, **kwargs)


class ConfigurationError(ServerError):
    """
    Raised when there's a configuration error (missing env vars, invalid settings, etc.).
    HTTP Status: 500 Internal Server Error
    """
    
    status_code: int = 500
    error_code: str = "CONFIGURATION_ERROR"
    error_type: str = "configuration_error"
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if config_key:
            internal_details["config_key"] = config_key
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)


class TimeoutError(ServerError):
    """
    Raised when an operation times out.
    HTTP Status: 504 Gateway Timeout
    """
    
    status_code: int = 504
    error_code: str = "TIMEOUT"
    error_type: str = "timeout_error"
    
    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if timeout_seconds:
            internal_details["timeout_seconds"] = timeout_seconds
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)
