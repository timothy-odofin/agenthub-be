"""
Resilience patterns for handling transient failures and service degradation.

This module provides decorators and utilities for:
- Retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Timeout management
- Fallback strategies
"""

from .circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerOpenError,
    CircuitState,
    async_circuit_breaker,
    circuit_breaker,
    get_all_circuit_breaker_stats,
    get_circuit_breaker_stats,
)
from .retry import (
    RetryConfig,
    RetryStrategy,
    async_retry,
    constant_backoff,
    exponential_backoff,
    linear_backoff,
    retry,
)
from .timeout import TimeoutConfig, async_timeout, timeout

__all__ = [
    # Retry
    "retry",
    "async_retry",
    "RetryConfig",
    "RetryStrategy",
    "exponential_backoff",
    "linear_backoff",
    "constant_backoff",
    # Circuit Breaker
    "circuit_breaker",
    "async_circuit_breaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitBreakerError",
    "CircuitBreakerOpenError",
    "get_circuit_breaker_stats",
    "get_all_circuit_breaker_stats",
    # Timeout
    "timeout",
    "async_timeout",
    "TimeoutConfig",
]
