"""
Cache operation error handler decorator.

Provides consistent error handling for cache operations using the
exception hierarchy. Wraps cache provider methods to catch errors
and raise appropriate CacheError exceptions.
"""

import functools
import inspect
from typing import Any, Callable, Optional, TypeVar

from app.core.exceptions import CacheError
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def handle_cache_errors(
    operation: Optional[str] = None,
    default_return: Any = None,
    suppress_errors: bool = False
):
    """
    Decorator to handle cache operation errors consistently.
    
    Converts all cache-related exceptions into CacheError from the exception
    hierarchy, allowing global exception handlers to provide uniform error responses.
    
    Args:
        operation: Name of the cache operation (e.g., "set", "get", "delete").
                  If None, uses the function name.
        default_return: Value to return if suppress_errors=True and an error occurs.
        suppress_errors: If True, logs error and returns default_return instead of raising.
                        Useful for non-critical cache operations where failures shouldn't break the app.
        
    Example:
        @handle_cache_errors(operation="set")
        async def set(self, key: str, value: Any) -> bool:
            return await self.redis.set(key, value)
            
        @handle_cache_errors(operation="get", default_return=None, suppress_errors=True)
        async def get(self, key: str) -> Optional[Any]:
            # If this fails, return None instead of raising
            return await self.redis.get(key)
            
    Raises:
        CacheError: For all cache-related errors (unless suppress_errors=True)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            op_name = operation or func.__name__
            
            try:
                return await func(*args, **kwargs)
                
            except CacheError:
                # Already a CacheError, just re-raise
                raise
                
            except ConnectionError as e:
                error_msg = f"Cache connection failed during '{op_name}' operation"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                
            except TimeoutError as e:
                error_msg = f"Cache operation '{op_name}' timed out"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": "timeout"
                    }
                )
                
            except (KeyError, AttributeError) as e:
                error_msg = f"Cache operation '{op_name}' failed: Invalid data structure"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": "data_structure_error"
                    }
                )
                
            except Exception as e:
                error_msg = f"Unexpected error during cache operation '{op_name}'"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            op_name = operation or func.__name__
            
            try:
                return func(*args, **kwargs)
                
            except CacheError:
                # Already a CacheError, just re-raise
                raise
                
            except ConnectionError as e:
                error_msg = f"Cache connection failed during '{op_name}' operation"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                
            except TimeoutError as e:
                error_msg = f"Cache operation '{op_name}' timed out"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": "timeout"
                    }
                )
                
            except (KeyError, AttributeError) as e:
                error_msg = f"Cache operation '{op_name}' failed: Invalid data structure"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": "data_structure_error"
                    }
                )
                
            except Exception as e:
                error_msg = f"Unexpected error during cache operation '{op_name}'"
                logger.error(error_msg, exc_info=True)
                
                if suppress_errors:
                    return default_return
                
                raise CacheError(
                    message=error_msg,
                    operation=op_name,
                    internal_details={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
