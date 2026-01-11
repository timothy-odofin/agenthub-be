"""
Global Exception Handlers for FastAPI

This module provides centralized exception handling for all API errors.
All handlers return uniform error responses following the error format standard.

Exception Handling Flow:
    Request → Middleware (add request_id) 
           → Route Handler (may raise exception)
           → Exception Handler (format error)
           → Response (uniform format)
"""

from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    BaseAppException,
    ClientError,
    ServerError,
    ValidationError,
    InternalError,
)
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    Handler for all custom application exceptions (BaseAppException).
    
    This catches all exceptions from our exception hierarchy and returns
    uniform error responses with proper HTTP status codes.
    
    Args:
        request: The FastAPI request object
        exc: The raised BaseAppException or its subclass
        
    Returns:
        JSONResponse with uniform error format
    """
    # Get request ID from request state (added by middleware)
    request_id = getattr(request.state, "request_id", None)
    
    # Add request ID to exception if not already present
    if not exc.request_id and request_id:
        exc.request_id = request_id
    
    # Log the error with full context
    log_context = exc.get_log_context()
    log_context.update({
        "http_method": request.method,
        "http_url": str(request.url),
        "client_ip": request.client.host if request.client else None,
    })
    
    # Determine log level based on exception type
    if isinstance(exc, ClientError):
        # Client errors are user mistakes, log at INFO level
        logger.info(f"Client error: {exc.error_code}", extra=log_context)
    elif isinstance(exc, ServerError):
        # Server errors are our fault, log at ERROR level with stack trace
        logger.error(f"Server error: {exc.error_code}", extra=log_context, exc_info=True)
    else:
        # External service errors, log at WARN level
        logger.warning(f"External service error: {exc.error_code}", extra=log_context)
    
    # Return uniform error response (sanitized, no internal details)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for FastAPI request validation errors (Pydantic validation).
    
    Converts FastAPI validation errors into our uniform ValidationError format.
    
    Args:
        request: The FastAPI request object
        exc: The RequestValidationError from FastAPI/Pydantic
        
    Returns:
        JSONResponse with uniform error format
    """
    # Get request ID from request state
    request_id = getattr(request.state, "request_id", None)
    
    # Extract validation errors
    errors = exc.errors()
    
    # Format validation errors for response
    validation_details = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        validation_details.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    # Create our ValidationError
    validation_error = ValidationError(
        message="Request validation failed",
        details={"validation_errors": validation_details},
        request_id=request_id,
        internal_details={
            "raw_errors": errors,
            "body": str(exc.body) if hasattr(exc, 'body') else None,
        }
    )
    
    # Log validation error
    logger.info(
        "Request validation failed",
        extra={
            "request_id": request_id,
            "http_method": request.method,
            "http_url": str(request.url),
            "validation_errors": validation_details,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=validation_error.to_dict(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for Starlette/FastAPI HTTPException.
    
    Converts standard HTTPException into our uniform error format.
    This catches HTTPException that might be raised directly in code
    before migration to custom exceptions is complete.
    
    Args:
        request: The FastAPI request object
        exc: The HTTPException from Starlette/FastAPI
        
    Returns:
        JSONResponse with uniform error format
    """
    # Get request ID from request state
    request_id = getattr(request.state, "request_id", None)
    
    # Map HTTP status code to error type
    if 400 <= exc.status_code < 500:
        error_type = "client_error"
        log_level = "info"
    else:
        error_type = "server_error"
        log_level = "error"
    
    # Create uniform error response
    error_response = {
        "error": {
            "type": error_type,
            "code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail) if exc.detail else "An error occurred",
            "request_id": request_id,
        }
    }
    
    # Log the error
    log_method = getattr(logger, log_level)
    log_method(
        f"HTTPException: {exc.status_code}",
        extra={
            "request_id": request_id,
            "http_method": request.method,
            "http_url": str(request.url),
            "status_code": exc.status_code,
            "detail": exc.detail,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    
    This is the last line of defense for unhandled exceptions.
    Returns a generic 500 error without exposing internal details.
    
    Args:
        request: The FastAPI request object
        exc: Any unhandled exception
        
    Returns:
        JSONResponse with generic error message
    """
    # Get request ID from request state
    request_id = getattr(request.state, "request_id", None)
    
    # Create InternalError
    internal_error = InternalError(
        message="An unexpected error occurred. Please try again later.",
        request_id=request_id,
        internal_details={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
    )
    
    # Log with full stack trace
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "http_method": request.method,
            "http_url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        },
        exc_info=True,  # Include full stack trace
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=internal_error.to_dict(),
    )


# Export all handlers
__all__ = [
    "base_app_exception_handler",
    "validation_error_handler",
    "http_exception_handler",
    "generic_exception_handler",
]
