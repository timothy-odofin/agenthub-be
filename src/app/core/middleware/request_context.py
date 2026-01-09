"""
Request Context Middleware

Adds request ID to all incoming requests for distributed tracing.
The request ID is used to correlate logs, errors, and metrics.
"""

import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds request context to all incoming requests.
    
    Features:
    - Generates or extracts request ID from X-Request-ID header
    - Stores request ID in request.state for access in handlers
    - Adds request ID to response headers
    - Logs request/response with timing information
    - Provides request context for error handlers
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add context.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response with added headers and context
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"
        
        # Store request ID in request state (accessible in handlers and exception handlers)
        request.state.request_id = request_id
        
        # Store request start time for duration calculation
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "http_method": request.method,
                "http_url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent"),
            }
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log successful response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "http_method": request.method,
                    "http_url": str(request.url),
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log error (detailed logging will be done by exception handlers)
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "http_method": request.method,
                    "http_url": str(request.url),
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            
            # Re-raise to be caught by exception handlers
            raise
