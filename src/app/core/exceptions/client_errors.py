"""
Client Error Exceptions (4xx)

These exceptions represent errors caused by the client (invalid input, unauthorized access, etc.).
They should be logged at INFO or WARN level since they're not server issues.
"""

from typing import Any, Dict, Optional
from .base import ClientError


class ValidationError(ClientError):
    """
    Raised when request validation fails (invalid input format, missing fields, etc.).
    HTTP Status: 400 Bad Request
    """
    
    status_code: int = 400
    error_code: str = "VALIDATION_ERROR"
    error_type: str = "validation_error"
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        constraint: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if constraint:
            details["constraint"] = constraint
        
        kwargs["details"] = details
        super().__init__(message, **kwargs)


class AuthenticationError(ClientError):
    """
    Raised when authentication fails (invalid credentials, missing token, etc.).
    HTTP Status: 401 Unauthorized
    """
    
    status_code: int = 401
    error_code: str = "AUTHENTICATION_ERROR"
    error_type: str = "authentication_error"
    
    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class AuthorizationError(ClientError):
    """
    Raised when user lacks permission to access a resource.
    HTTP Status: 403 Forbidden
    """
    
    status_code: int = 403
    error_code: str = "AUTHORIZATION_ERROR"
    error_type: str = "authorization_error"
    
    def __init__(
        self,
        message: str = "You don't have permission to access this resource",
        resource: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if resource:
            details["resource"] = resource
        
        kwargs["details"] = details
        super().__init__(message, **kwargs)


class NotFoundError(ClientError):
    """
    Raised when a requested resource is not found.
    HTTP Status: 404 Not Found
    """
    
    status_code: int = 404
    error_code: str = "NOT_FOUND"
    error_type: str = "not_found_error"
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        kwargs["details"] = details
        super().__init__(message, **kwargs)


class ConflictError(ClientError):
    """
    Raised when a request conflicts with current state (duplicate resource, etc.).
    HTTP Status: 409 Conflict
    """
    
    status_code: int = 409
    error_code: str = "CONFLICT"
    error_type: str = "conflict_error"
    
    def __init__(
        self,
        message: str = "Resource conflict",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class RateLimitError(ClientError):
    """
    Raised when rate limit is exceeded.
    HTTP Status: 429 Too Many Requests
    """
    
    status_code: int = 429
    error_code: str = "RATE_LIMIT_EXCEEDED"
    error_type: str = "rate_limit_error"
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        kwargs["details"] = details
        super().__init__(message, **kwargs)


class BadRequestError(ClientError):
    """
    Raised for generic bad requests that don't fit other categories.
    HTTP Status: 400 Bad Request
    """
    
    status_code: int = 400
    error_code: str = "BAD_REQUEST"
    error_type: str = "bad_request_error"
    
    def __init__(
        self,
        message: str = "Bad request",
        **kwargs
    ):
        super().__init__(message, **kwargs)
