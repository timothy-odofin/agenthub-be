"""
Utility decorators for common functionality across the application.

This module provides decorators for handling errors in a consistent way
using the new exception hierarchy. All decorators now raise specific
exceptions instead of returning default values, allowing global handlers
to provide uniform error responses.
"""
import functools
from typing import Any, Callable, Optional, TypeVar
import requests
from app.core.utils.logger import get_logger
from app.core.exceptions import (
    ThirdPartyAPIError,
    VectorDBError,
    TimeoutError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
)

logger = get_logger(__name__)

T = TypeVar('T')


def handle_atlassian_errors(default_return: Any = None):
    """
    Decorator to handle common Atlassian API exceptions with specific HTTP status handling.
    
    Now raises specific exceptions from the exception hierarchy instead of returning
    default values. This allows global exception handlers to provide uniform error responses.
    
    Args:
        default_return: DEPRECATED - Kept for backward compatibility but ignored.
                       The decorator now raises exceptions instead of returning defaults.
        
    Example:
        @handle_atlassian_errors()
        def get_spaces(self):
            return self._confluence.get_all_spaces()
            
    Raises:
        AuthenticationError: When API credentials are invalid (401)
        AuthorizationError: When user lacks permissions (403)
        NotFoundError: When resource doesn't exist (404)
        RateLimitError: When rate limit is exceeded (429)
        ThirdPartyAPIError: For all other Atlassian API errors
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                status_code = getattr(e.response, 'status_code', None)
                response_text = getattr(e.response, 'text', 'No response body')
                
                # Map HTTP status codes to specific exceptions
                if status_code == 401:
                    logger.error(f"Authentication failed in {func.__name__}: Invalid API credentials or token expired")
                    raise AuthenticationError(
                        message="Atlassian authentication failed. Please check your API credentials.",
                        internal_details={
                            "function": func.__name__,
                            "status_code": status_code,
                            "response": response_text[:500]  # Truncate for security
                        }
                    )
                    
                elif status_code == 403:
                    logger.error(f"Access forbidden in {func.__name__}: User lacks permission for this resource")
                    raise AuthorizationError(
                        message="Access to Atlassian resource forbidden. Check your permissions.",
                        resource="atlassian_resource",
                        internal_details={
                            "function": func.__name__,
                            "status_code": status_code,
                            "response": response_text[:500]
                        }
                    )
                    
                elif status_code == 404:
                    logger.warning(f"Resource not found in {func.__name__}: The requested space, page, or endpoint doesn't exist")
                    raise NotFoundError(
                        message="Atlassian resource not found",
                        resource_type="atlassian_resource",
                        internal_details={
                            "function": func.__name__,
                            "status_code": status_code
                        }
                    )
                    
                elif status_code == 429:
                    logger.error(f"Rate limit exceeded in {func.__name__}: Too many requests to Atlassian API")
                    retry_after = e.response.headers.get('Retry-After')
                    raise RateLimitError(
                        message="Atlassian API rate limit exceeded. Please try again later.",
                        retry_after=int(retry_after) if retry_after else None,
                        internal_details={
                            "function": func.__name__,
                            "status_code": status_code
                        }
                    )
                    
                else:
                    # Generic Atlassian API error
                    error_category = "Client error" if 400 <= status_code < 500 else "Server error"
                    logger.error(f"{error_category} in {func.__name__}: HTTP {status_code}")
                    raise ThirdPartyAPIError(
                        message=f"Atlassian API error: {error_category}",
                        api_name="atlassian",
                        status_code=status_code,
                        internal_details={
                            "function": func.__name__,
                            "response": response_text[:500]
                        }
                    )
                    
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection failed in {func.__name__}: Check network connectivity or Atlassian URL")
                raise ThirdPartyAPIError(
                    message="Failed to connect to Atlassian API. Please check network connectivity.",
                    api_name="atlassian",
                    internal_details={
                        "function": func.__name__,
                        "error": str(e)
                    }
                )
                
            except requests.exceptions.Timeout as e:
                logger.error(f"Request timeout in {func.__name__}: Atlassian API response too slow")
                raise TimeoutError(
                    message="Atlassian API request timed out",
                    operation=f"atlassian_{func.__name__}",
                    internal_details={
                        "function": func.__name__,
                        "error": str(e)
                    }
                )
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed in {func.__name__}: Network or request issue")
                raise ThirdPartyAPIError(
                    message="Atlassian API request failed",
                    api_name="atlassian",
                    internal_details={
                        "function": func.__name__,
                        "error": str(e)
                    }
                )
                
            except KeyError as e:
                logger.error(f"Unexpected API response in {func.__name__}: Missing expected field {e}")
                raise ThirdPartyAPIError(
                    message="Unexpected Atlassian API response format",
                    api_name="atlassian",
                    internal_details={
                        "function": func.__name__,
                        "missing_field": str(e)
                    }
                )
                
            except AttributeError as e:
                logger.error(f"API client issue in {func.__name__}: {e}. Check if Confluence client is properly initialized.")
                raise ThirdPartyAPIError(
                    message="Atlassian API client error",
                    api_name="atlassian",
                    internal_details={
                        "function": func.__name__,
                        "error": str(e)
                    }
                )
                
            except Exception as e:
                # Catch-all for unexpected exceptions
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                raise ThirdPartyAPIError(
                    message="An unexpected error occurred while calling Atlassian API",
                    api_name="atlassian",
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
        return wrapper
    return decorator


def handle_vector_db_errors(default_return: Any = None):
    """
    Decorator to handle vector database exceptions.
    
    Now raises VectorDBError from the exception hierarchy instead of returning
    default values. This allows global exception handlers to provide uniform error responses.
    
    Args:
        default_return: DEPRECATED - Kept for backward compatibility but ignored.
        
    Example:
        @handle_vector_db_errors()
        def search_vectors(self, query):
            return self.vector_db.search(query)
            
    Raises:
        VectorDBError: For all vector database errors
        TimeoutError: When vector DB operations timeout
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                logger.error(f"Vector DB connection failed in {func.__name__}: {e}")
                raise VectorDBError(
                    message="Failed to connect to vector database",
                    operation=func.__name__,
                    internal_details={
                        "error": str(e)
                    }
                )
            except Exception as e:
                logger.error(f"Vector DB error in {func.__name__}: {e}", exc_info=True)
                # Check if it's a timeout-like error
                if "timeout" in str(e).lower():
                    raise TimeoutError(
                        message="Vector database operation timed out",
                        operation=f"vector_db_{func.__name__}",
                        internal_details={
                            "error": str(e)
                        }
                    )
                else:
                    raise VectorDBError(
                        message="Vector database operation failed",
                        operation=func.__name__,
                        internal_details={
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
        return wrapper
    return decorator


def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log function execution time.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}")
            raise
    return wrapper
