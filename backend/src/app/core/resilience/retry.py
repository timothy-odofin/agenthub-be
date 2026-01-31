"""
Retry decorator with exponential backoff and jitter.

Provides configurable retry logic for transient failures with:
- Multiple backoff strategies (exponential, linear, constant)
- Jitter to avoid thundering herd
- Custom retry conditions
- Detailed logging
"""

import asyncio
import functools
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Set, Type, TypeVar, Union, Any

from app.core.utils.logger import get_logger
from app.core.exceptions import BaseAppException, TimeoutError, ThirdPartyAPIError, RateLimitError

logger = get_logger(__name__)

T = TypeVar('T')


class RetryStrategy(str, Enum):
    """Available retry backoff strategies."""
    EXPONENTIAL = "exponential"  # delay = base * (2 ** attempt)
    LINEAR = "linear"            # delay = base * attempt
    CONSTANT = "constant"        # delay = base


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    # Maximum number of retry attempts (not including the first attempt)
    max_attempts: int = 3
    
    # Base delay in seconds between retries
    base_delay: float = 1.0
    
    # Maximum delay in seconds (cap for exponential backoff)
    max_delay: float = 60.0
    
    # Backoff strategy
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    
    # Jitter: adds randomness to delay to avoid thundering herd
    # If True, delay = delay * random(0.5, 1.5)
    jitter: bool = True
    
    # Exceptions that should trigger a retry
    retryable_exceptions: Set[Type[Exception]] = field(default_factory=lambda: {
        TimeoutError,
        ThirdPartyAPIError,
        ConnectionError,
        TimeoutError,  # Built-in
    })
    
    # Exceptions that should NOT trigger a retry (even if they match retryable_exceptions)
    non_retryable_exceptions: Set[Type[Exception]] = field(default_factory=lambda: {
        RateLimitError,  # Should use rate limiter instead
        ValueError,
        TypeError,
    })
    
    # Custom retry condition (optional)
    # Function that takes the exception and returns True if should retry
    retry_condition: Optional[Callable[[Exception], bool]] = None
    
    # Multiply delay after each retry (for exponential/linear)
    backoff_multiplier: float = 2.0


def exponential_backoff(attempt: int, base_delay: float, max_delay: float, jitter: bool = True) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap
        jitter: Whether to add randomness
        
    Returns:
        Delay in seconds
    """
    delay = base_delay * (2 ** attempt)
    delay = min(delay, max_delay)
    
    if jitter:
        # Add jitter: delay * random(0.5, 1.5)
        delay = delay * random.uniform(0.5, 1.5)
    
    return delay


def linear_backoff(attempt: int, base_delay: float, max_delay: float, jitter: bool = True) -> float:
    """
    Calculate linear backoff delay.
    
    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap
        jitter: Whether to add randomness
        
    Returns:
        Delay in seconds
    """
    delay = base_delay * (attempt + 1)
    delay = min(delay, max_delay)
    
    if jitter:
        delay = delay * random.uniform(0.5, 1.5)
    
    return delay


def constant_backoff(attempt: int, base_delay: float, max_delay: float, jitter: bool = True) -> float:
    """
    Calculate constant backoff delay.
    
    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Constant delay in seconds
        max_delay: Not used (kept for interface consistency)
        jitter: Whether to add randomness
        
    Returns:
        Delay in seconds
    """
    delay = base_delay
    
    if jitter:
        delay = delay * random.uniform(0.5, 1.5)
    
    return delay


def _calculate_delay(config: RetryConfig, attempt: int) -> float:
    """Calculate delay based on retry configuration and attempt number."""
    if config.strategy == RetryStrategy.EXPONENTIAL:
        return exponential_backoff(attempt, config.base_delay, config.max_delay, config.jitter)
    elif config.strategy == RetryStrategy.LINEAR:
        return linear_backoff(attempt, config.base_delay, config.max_delay, config.jitter)
    elif config.strategy == RetryStrategy.CONSTANT:
        return constant_backoff(attempt, config.base_delay, config.max_delay, config.jitter)
    else:
        # Default to exponential
        return exponential_backoff(attempt, config.base_delay, config.max_delay, config.jitter)


def _should_retry(exception: Exception, config: RetryConfig) -> bool:
    """Determine if an exception should trigger a retry."""
    # If custom retry condition is provided, use ONLY that
    if config.retry_condition is not None:
        try:
            return config.retry_condition(exception)
        except Exception as e:
            logger.warning(f"Custom retry condition failed: {e}")
            # Fall through to default logic if custom condition fails
    
    # Check non-retryable exceptions first (higher priority)
    for exc_type in config.non_retryable_exceptions:
        if isinstance(exception, exc_type):
            return False
    
    # Check retryable exceptions
    for exc_type in config.retryable_exceptions:
        if isinstance(exception, exc_type):
            return True
    
    return False


def retry(config: Optional[RetryConfig] = None) -> Callable:
    """
    Decorator for synchronous functions to retry on failure.
    
    Args:
        config: Retry configuration. If None, uses default config.
        
    Example:
        @retry(RetryConfig(max_attempts=3, base_delay=1.0))
        def fetch_data(url: str) -> dict:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts + 1):  # +1 for initial attempt
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful retry if not first attempt
                    if attempt > 0:
                        logger.info(
                            f"Function '{func.__name__}' succeeded after {attempt} retries",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt,
                                "total_attempts": attempt + 1
                            }
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not _should_retry(e, config):
                        logger.warning(
                            f"Non-retryable exception in '{func.__name__}': {type(e).__name__}",
                            extra={
                                "function": func.__name__,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e)
                            }
                        )
                        raise
                    
                    # Check if we have retries left
                    if attempt >= config.max_attempts:
                        logger.error(
                            f"Function '{func.__name__}' failed after {config.max_attempts} retries",
                            extra={
                                "function": func.__name__,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                                "max_attempts": config.max_attempts
                            }
                        )
                        raise
                    
                    # Calculate delay and sleep
                    delay = _calculate_delay(config, attempt)
                    
                    logger.info(
                        f"Retrying '{func.__name__}' after {delay:.2f}s (attempt {attempt + 1}/{config.max_attempts})",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": config.max_attempts,
                            "delay_seconds": delay,
                            "exception_type": type(e).__name__
                        }
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def async_retry(config: Optional[RetryConfig] = None) -> Callable:
    """
    Decorator for asynchronous functions to retry on failure.
    
    Args:
        config: Retry configuration. If None, uses default config.
        
    Example:
        @async_retry(RetryConfig(max_attempts=3, base_delay=1.0))
        async def fetch_data(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts + 1):  # +1 for initial attempt
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log successful retry if not first attempt
                    if attempt > 0:
                        logger.info(
                            f"Async function '{func.__name__}' succeeded after {attempt} retries",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt,
                                "total_attempts": attempt + 1
                            }
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not _should_retry(e, config):
                        logger.warning(
                            f"Non-retryable exception in async '{func.__name__}': {type(e).__name__}",
                            extra={
                                "function": func.__name__,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e)
                            }
                        )
                        raise
                    
                    # Check if we have retries left
                    if attempt >= config.max_attempts:
                        logger.error(
                            f"Async function '{func.__name__}' failed after {config.max_attempts} retries",
                            extra={
                                "function": func.__name__,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                                "max_attempts": config.max_attempts
                            }
                        )
                        raise
                    
                    # Calculate delay and sleep
                    delay = _calculate_delay(config, attempt)
                    
                    logger.info(
                        f"Retrying async '{func.__name__}' after {delay:.2f}s (attempt {attempt + 1}/{config.max_attempts})",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": config.max_attempts,
                            "delay_seconds": delay,
                            "exception_type": type(e).__name__
                        }
                    )
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator
