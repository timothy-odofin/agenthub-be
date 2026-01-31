"""
Resilience patterns for handling transient failures and service degradation.

This module provides decorators and utilities for:
- Retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Timeout management
- Fallback strategies
"""

from .retry import (
    retry,
    async_retry,
    RetryConfig,
    RetryStrategy,
    exponential_backoff,
    linear_backoff,
    constant_backoff
)

from .circuit_breaker import (
    circuit_breaker,
    async_circuit_breaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerOpenError,
    get_circuit_breaker_stats,
    get_all_circuit_breaker_stats
)

from .timeout import (
    timeout,
    async_timeout,
    TimeoutConfig
)

__all__ = [
    # Retry
    'retry',
    'async_retry',
    'RetryConfig',
    'RetryStrategy',
    'exponential_backoff',
    'linear_backoff',
    'constant_backoff',
    
    # Circuit Breaker
    'circuit_breaker',
    'async_circuit_breaker',
    'CircuitBreakerConfig',
    'CircuitState',
    'CircuitBreakerError',
    'CircuitBreakerOpenError',
    'get_circuit_breaker_stats',
    'get_all_circuit_breaker_stats',
    
    # Timeout
    'timeout',
    'async_timeout',
    'TimeoutConfig',
]
