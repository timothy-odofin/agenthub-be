"""
Timeout decorators for enforcing execution time limits.

Provides timeouts for both synchronous and asynchronous functions:
- Synchronous: Uses signal (Unix) or threading (cross-platform)
- Asynchronous: Uses asyncio.wait_for()
"""

import asyncio
import functools
import signal
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

from app.core.utils.logger import get_logger
from app.core.exceptions import TimeoutError as AppTimeoutError

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class TimeoutConfig:
    """Configuration for timeout behavior."""
    
    # Timeout in seconds
    timeout_seconds: float
    
    # Custom timeout exception (optional)
    exception_class: type = AppTimeoutError
    
    # Custom error message (optional)
    error_message: Optional[str] = None
    
    # Operation name for logging (optional, defaults to function name)
    operation_name: Optional[str] = None


class TimeoutException(Exception):
    """Internal timeout exception for signal handling."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException()


@contextmanager
def time_limit(seconds: float):
    """
    Context manager for timeout using signals (Unix only).
    
    Args:
        seconds: Timeout in seconds
        
    Raises:
        TimeoutException: If timeout is reached
        
    Example:
        with time_limit(5):
            slow_operation()
    """
    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(int(seconds))
    
    try:
        yield
    finally:
        # Cancel alarm and restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def timeout(config: Optional[TimeoutConfig] = None, timeout_seconds: Optional[float] = None) -> Callable:
    """
    Decorator for synchronous functions to enforce timeout.
    
    Note: Uses signal.SIGALRM on Unix systems. May not work on Windows.
    For cross-platform support, consider using threading or multiprocessing.
    
    Args:
        config: Timeout configuration. If None, uses timeout_seconds.
        timeout_seconds: Shorthand for timeout (if config not provided)
        
    Example:
        @timeout(timeout_seconds=5.0)
        def slow_operation():
            time.sleep(10)  # Will raise TimeoutError after 5 seconds
    """
    if config is None:
        if timeout_seconds is None:
            raise ValueError("Either config or timeout_seconds must be provided")
        config = TimeoutConfig(timeout_seconds=timeout_seconds)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            operation_name = config.operation_name or func.__name__
            
            try:
                with time_limit(config.timeout_seconds):
                    return func(*args, **kwargs)
                    
            except TimeoutException:
                error_msg = config.error_message or f"Operation '{operation_name}' timed out after {config.timeout_seconds}s"
                
                logger.warning(
                    f"Timeout in '{operation_name}' after {config.timeout_seconds}s",
                    extra={
                        "operation": operation_name,
                        "timeout_seconds": config.timeout_seconds
                    }
                )
                
                if config.exception_class == AppTimeoutError:
                    raise AppTimeoutError(
                        message=error_msg,
                        operation=operation_name,
                        internal_details={"timeout_seconds": config.timeout_seconds}
                    )
                else:
                    raise config.exception_class(error_msg)
                    
        return wrapper
    return decorator


def async_timeout(config: Optional[TimeoutConfig] = None, timeout_seconds: Optional[float] = None) -> Callable:
    """
    Decorator for asynchronous functions to enforce timeout.
    
    Uses asyncio.wait_for() for clean async timeout handling.
    
    Args:
        config: Timeout configuration. If None, uses timeout_seconds.
        timeout_seconds: Shorthand for timeout (if config not provided)
        
    Example:
        @async_timeout(timeout_seconds=5.0)
        async def slow_operation():
            await asyncio.sleep(10)  # Will raise TimeoutError after 5 seconds
    """
    if config is None:
        if timeout_seconds is None:
            raise ValueError("Either config or timeout_seconds must be provided")
        config = TimeoutConfig(timeout_seconds=timeout_seconds)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            operation_name = config.operation_name or func.__name__
            
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=config.timeout_seconds
                )
                
            except asyncio.TimeoutError:
                error_msg = config.error_message or f"Async operation '{operation_name}' timed out after {config.timeout_seconds}s"
                
                logger.warning(
                    f"Async timeout in '{operation_name}' after {config.timeout_seconds}s",
                    extra={
                        "operation": operation_name,
                        "timeout_seconds": config.timeout_seconds
                    }
                )
                
                if config.exception_class == AppTimeoutError:
                    raise AppTimeoutError(
                        message=error_msg,
                        operation=operation_name,
                        internal_details={"timeout_seconds": config.timeout_seconds}
                    )
                else:
                    raise config.exception_class(error_msg)
                    
        return wrapper
    return decorator
