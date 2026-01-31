"""
Circuit Breaker pattern implementation.

Prevents cascading failures by temporarily blocking calls to failing services:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests fail immediately
- HALF_OPEN: Testing if service recovered, limited requests allowed

The circuit breaker tracks failure rates and automatically transitions between states.
"""

import asyncio
import functools
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Callable, Optional, Set, Type, TypeVar, Dict, Any

from app.core.utils.logger import get_logger
from app.core.exceptions import BaseAppException, ServiceUnavailableError

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Circuit is open, failing fast
    HALF_OPEN = "half_open"    # Testing if service recovered


class CircuitBreakerError(BaseAppException):
    """Base exception for circuit breaker errors."""
    
    def __init__(self, message: str, circuit_name: str, state: CircuitState, **kwargs):
        super().__init__(
            message=message,
            details={"circuit_name": circuit_name, "state": state.value},
            **kwargs
        )
        self.circuit_name = circuit_name
        self.state = state


class CircuitBreakerOpenError(ServiceUnavailableError):
    """Raised when circuit breaker is open and blocking requests."""
    
    def __init__(self, circuit_name: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            service_name=circuit_name,
            message=f"Circuit breaker '{circuit_name}' is OPEN. Service temporarily unavailable.",
            details={"state": "open", "circuit_name": circuit_name},
            **kwargs
        )
        self.circuit_name = circuit_name
        self.retry_after = retry_after


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    # Circuit breaker name (for logging and metrics)
    name: str = "default"
    
    # Number of consecutive failures before opening circuit
    failure_threshold: int = 5
    
    # Time window for counting failures (seconds)
    failure_window: float = 60.0
    
    # Time to wait before transitioning from OPEN to HALF_OPEN (seconds)
    recovery_timeout: float = 30.0
    
    # Number of successful calls in HALF_OPEN state to close circuit
    success_threshold: int = 2
    
    # Exceptions that count as failures
    failure_exceptions: Set[Type[Exception]] = field(default_factory=lambda: {
        ConnectionError,
        TimeoutError,
        ServiceUnavailableError,
    })
    
    # Exceptions that should NOT count as failures (even if they match failure_exceptions)
    ignored_exceptions: Set[Type[Exception]] = field(default_factory=lambda: {
        ValueError,
        TypeError,
    })
    
    # Custom failure condition (optional)
    # Function that takes the exception and returns True if it counts as failure
    failure_condition: Optional[Callable[[Exception], bool]] = None
    
    # Fallback function to call when circuit is open (optional)
    # Function signature: (exception, *args, **kwargs) -> result
    fallback: Optional[Callable] = None


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.
    
    Tracks failures and automatically opens circuit when failure threshold is reached.
    After recovery timeout, enters half-open state to test if service recovered.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.failures_window: list = []  # List of (timestamp, exception_type) tuples
        self._lock = Lock()
        
        logger.info(
            f"Circuit breaker '{self.config.name}' initialized",
            extra={
                "circuit_name": self.config.name,
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout
            }
        )
    
    def _should_count_as_failure(self, exception: Exception) -> bool:
        """Determine if an exception should count as a failure."""
        # Check ignored exceptions first (higher priority)
        for exc_type in self.config.ignored_exceptions:
            if isinstance(exception, exc_type):
                return False
        
        # Check failure exceptions
        is_failure = False
        for exc_type in self.config.failure_exceptions:
            if isinstance(exception, exc_type):
                is_failure = True
                break
        
        # If custom failure condition is provided, use it
        if self.config.failure_condition is not None:
            try:
                return self.config.failure_condition(exception)
            except Exception as e:
                logger.warning(f"Custom failure condition failed: {e}")
                return is_failure
        
        return is_failure
    
    def _clean_old_failures(self):
        """Remove failures outside the failure window."""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=self.config.failure_window)
        
        self.failures_window = [
            (timestamp, exc_type)
            for timestamp, exc_type in self.failures_window
            if timestamp > cutoff_time
        ]
    
    def _record_failure(self, exception: Exception):
        """Record a failure."""
        with self._lock:
            self.failures_window.append((datetime.now(), type(exception).__name__))
            self._clean_old_failures()
            self.failure_count = len(self.failures_window)
            self.last_failure_time = datetime.now()
            self.success_count = 0  # Reset success count on failure
    
    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
            self.failure_count = 0
            self.failures_window = []
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset from OPEN to HALF_OPEN."""
        if self.state != CircuitState.OPEN or self.opened_at is None:
            return False
        
        elapsed = (datetime.now() - self.opened_at).total_seconds()
        return elapsed >= self.config.recovery_timeout
    
    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        with self._lock:
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now()
            
            logger.warning(
                f"Circuit breaker '{self.config.name}' OPENED due to {self.failure_count} failures",
                extra={
                    "circuit_name": self.config.name,
                    "state": "open",
                    "failure_count": self.failure_count,
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout
                }
            )
    
    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        with self._lock:
            self.state = CircuitState.HALF_OPEN
            self.success_count = 0
            
            logger.info(
                f"Circuit breaker '{self.config.name}' entering HALF_OPEN state",
                extra={
                    "circuit_name": self.config.name,
                    "state": "half_open",
                    "success_threshold": self.config.success_threshold
                }
            )
    
    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.failures_window = []
            self.opened_at = None
            
            logger.info(
                f"Circuit breaker '{self.config.name}' CLOSED - service recovered",
                extra={
                    "circuit_name": self.config.name,
                    "state": "closed"
                }
            )
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by func
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._transition_to_half_open()
        
        # If circuit is open, fail fast
        if self.state == CircuitState.OPEN:
            retry_after = None
            if self.opened_at:
                elapsed = (datetime.now() - self.opened_at).total_seconds()
                retry_after = int(self.config.recovery_timeout - elapsed)
                if retry_after < 0:
                    retry_after = 0
            
            # Try fallback if available
            if self.config.fallback is not None:
                logger.info(
                    f"Circuit '{self.config.name}' is OPEN, using fallback",
                    extra={"circuit_name": self.config.name, "state": "open"}
                )
                try:
                    return self.config.fallback(None, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Fallback function failed: {e}")
            
            raise CircuitBreakerOpenError(
                circuit_name=self.config.name,
                retry_after=retry_after
            )
        
        # Try to execute function
        try:
            result = func(*args, **kwargs)
            
            # Record success
            self._record_success()
            
            # If in HALF_OPEN state and enough successes, close circuit
            if self.state == CircuitState.HALF_OPEN:
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            
            return result
            
        except Exception as e:
            # Check if this exception should count as failure
            if self._should_count_as_failure(e):
                self._record_failure(e)
                
                # If in HALF_OPEN state, immediately open on failure
                if self.state == CircuitState.HALF_OPEN:
                    self._transition_to_open()
                
                # If in CLOSED state and threshold reached, open circuit
                elif self.state == CircuitState.CLOSED:
                    if self.failure_count >= self.config.failure_threshold:
                        self._transition_to_open()
            
            # Re-raise the exception
            raise
    
    async def async_call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by func
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._transition_to_half_open()
        
        # If circuit is open, fail fast
        if self.state == CircuitState.OPEN:
            retry_after = None
            if self.opened_at:
                elapsed = (datetime.now() - self.opened_at).total_seconds()
                retry_after = int(self.config.recovery_timeout - elapsed)
                if retry_after < 0:
                    retry_after = 0
            
            # Try fallback if available
            if self.config.fallback is not None:
                logger.info(
                    f"Circuit '{self.config.name}' is OPEN, using fallback",
                    extra={"circuit_name": self.config.name, "state": "open"}
                )
                try:
                    if asyncio.iscoroutinefunction(self.config.fallback):
                        return await self.config.fallback(None, *args, **kwargs)
                    else:
                        return self.config.fallback(None, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Fallback function failed: {e}")
            
            raise CircuitBreakerOpenError(
                circuit_name=self.config.name,
                retry_after=retry_after
            )
        
        # Try to execute function
        try:
            result = await func(*args, **kwargs)
            
            # Record success
            self._record_success()
            
            # If in HALF_OPEN state and enough successes, close circuit
            if self.state == CircuitState.HALF_OPEN:
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            
            return result
            
        except Exception as e:
            # Check if this exception should count as failure
            if self._should_count_as_failure(e):
                self._record_failure(e)
                
                # If in HALF_OPEN state, immediately open on failure
                if self.state == CircuitState.HALF_OPEN:
                    self._transition_to_open()
                
                # If in CLOSED state and threshold reached, open circuit
                elif self.state == CircuitState.CLOSED:
                    if self.failure_count >= self.config.failure_threshold:
                        self._transition_to_open()
            
            # Re-raise the exception
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.config.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            }


# Global registry of circuit breakers (one per config name)
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = Lock()


def _get_circuit_breaker(config: CircuitBreakerConfig) -> CircuitBreaker:
    """Get or create a circuit breaker for the given config."""
    with _registry_lock:
        if config.name not in _circuit_breakers:
            _circuit_breakers[config.name] = CircuitBreaker(config)
        return _circuit_breakers[config.name]


def circuit_breaker(config: Optional[CircuitBreakerConfig] = None) -> Callable:
    """
    Decorator for synchronous functions to add circuit breaker protection.
    
    Args:
        config: Circuit breaker configuration. If None, uses default config.
        
    Example:
        @circuit_breaker(CircuitBreakerConfig(
            name="external_api",
            failure_threshold=5,
            recovery_timeout=30.0
        ))
        def call_external_api(url: str) -> dict:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """
    if config is None:
        config = CircuitBreakerConfig()
    
    breaker = _get_circuit_breaker(config)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def async_circuit_breaker(config: Optional[CircuitBreakerConfig] = None) -> Callable:
    """
    Decorator for asynchronous functions to add circuit breaker protection.
    
    Args:
        config: Circuit breaker configuration. If None, uses default config.
        
    Example:
        @async_circuit_breaker(CircuitBreakerConfig(
            name="external_api",
            failure_threshold=5,
            recovery_timeout=30.0
        ))
        async def call_external_api(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
    """
    if config is None:
        config = CircuitBreakerConfig()
    
    breaker = _get_circuit_breaker(config)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await breaker.async_call(func, *args, **kwargs)
        return wrapper
    return decorator


def get_circuit_breaker_stats(name: str) -> Optional[Dict[str, Any]]:
    """Get statistics for a named circuit breaker."""
    with _registry_lock:
        breaker = _circuit_breakers.get(name)
        if breaker:
            return breaker.get_stats()
        return None


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers."""
    with _registry_lock:
        return {
            name: breaker.get_stats()
            for name, breaker in _circuit_breakers.items()
        }
