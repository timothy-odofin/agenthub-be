"""
Utility decorators for common functionality across the application.
"""
import functools
from typing import Any, Callable, Optional, TypeVar
import requests
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def handle_atlassian_errors(default_return: Any = None):
    """
    Decorator to handle common Atlassian API exceptions with specific HTTP status handling.
    
    Args:
        default_return: Value to return when an exception occurs
        
    Example:
        @handle_atlassian_errors(default_return=[])
        def get_spaces(self):
            return self._confluence.get_all_spaces()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:

                status_code = getattr(e.response, 'status_code', None)
                
                if status_code == 401:
                    logger.error(f"Authentication failed in {func.__name__}: Invalid API credentials or token expired")
                elif status_code == 403:
                    logger.error(f"Access forbidden in {func.__name__}: User lacks permission for this resource")
                elif status_code == 404:
                    logger.warning(f"Resource not found in {func.__name__}: The requested space, page, or endpoint doesn't exist")
                elif status_code == 429:
                    logger.error(f"Rate limit exceeded in {func.__name__}: Too many requests to Atlassian API")
                elif status_code == 500:
                    logger.error(f"Atlassian server error in {func.__name__}: Internal server error on Atlassian's side")
                elif status_code == 502 or status_code == 503:
                    logger.error(f"Atlassian service unavailable in {func.__name__}: Service temporarily down")
                elif 400 <= status_code < 500:
                    logger.error(f"Client error in {func.__name__}: HTTP {status_code} - Check request parameters")
                elif 500 <= status_code < 600:
                    logger.error(f"Server error in {func.__name__}: HTTP {status_code} - Atlassian service issue")
                else:
                    logger.error(f"HTTP error in {func.__name__}: {status_code} - {e}")
                return default_return
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection failed in {func.__name__}: Check network connectivity or Atlassian URL. Error: {e}")
                return default_return
            except requests.exceptions.Timeout as e:
                logger.error(f"Request timeout in {func.__name__}: Atlassian API response too slow. Error: {e}")
                return default_return
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed in {func.__name__}: Network or request issue. Error: {e}")
                return default_return
            except KeyError as e:
                logger.error(f"Unexpected API response in {func.__name__}: Missing expected field {e}. API might have changed.")
                return default_return
            except AttributeError as e:
                logger.error(f"API client issue in {func.__name__}: {e}. Check if Confluence client is properly initialized.")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                return default_return
        return wrapper
    return decorator


def handle_vector_db_errors(default_return: Any = None):
    """
    Decorator to handle vector database exceptions.
    
    Args:
        default_return: Value to return when an exception occurs
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                logger.error(f"Vector DB connection failed in {func.__name__}: {e}")
                return default_return
            except Exception as e:
                logger.error(f"Vector DB error in {func.__name__}: {e}", exc_info=True)
                return default_return
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
