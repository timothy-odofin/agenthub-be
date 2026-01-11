"""
Unit tests for resilience patterns (retry, circuit breaker, timeout).

Tests all three resilience modules:
1. Retry decorator with exponential backoff
2. Circuit breaker pattern
3. Timeout enforcement
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.core.resilience import (
    # Retry
    retry,
    async_retry,
    RetryConfig,
    RetryStrategy,
    exponential_backoff,
    linear_backoff,
    constant_backoff,
    
    # Circuit Breaker
    circuit_breaker,
    async_circuit_breaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
    get_circuit_breaker_stats,
    get_all_circuit_breaker_stats,
    
    # Timeout
    async_timeout,
    TimeoutConfig,
)

from app.core.exceptions import (
    TimeoutError as AppTimeoutError,
    ThirdPartyAPIError,
    ServiceUnavailableError,
)


# ==================== RETRY TESTS ====================

class TestRetryBackoffStrategies:
    """Test backoff calculation strategies."""
    
    def test_exponential_backoff_no_jitter(self):
        """Test exponential backoff without jitter."""
        delay = exponential_backoff(0, 1.0, 60.0, jitter=False)
        assert delay == 1.0  # 2^0 * 1.0
        
        delay = exponential_backoff(1, 1.0, 60.0, jitter=False)
        assert delay == 2.0  # 2^1 * 1.0
        
        delay = exponential_backoff(3, 1.0, 60.0, jitter=False)
        assert delay == 8.0  # 2^3 * 1.0
    
    def test_exponential_backoff_with_max_delay(self):
        """Test exponential backoff respects max_delay."""
        delay = exponential_backoff(10, 1.0, 5.0, jitter=False)
        assert delay == 5.0  # Capped at max_delay
    
    def test_exponential_backoff_with_jitter(self):
        """Test exponential backoff adds jitter."""
        delay = exponential_backoff(2, 1.0, 60.0, jitter=True)
        # 2^2 * 1.0 = 4.0, jitter makes it 4.0 * random(0.5, 1.5)
        assert 2.0 <= delay <= 6.0
    
    def test_linear_backoff_no_jitter(self):
        """Test linear backoff without jitter."""
        delay = linear_backoff(0, 1.0, 60.0, jitter=False)
        assert delay == 1.0  # (0 + 1) * 1.0
        
        delay = linear_backoff(2, 1.0, 60.0, jitter=False)
        assert delay == 3.0  # (2 + 1) * 1.0
    
    def test_constant_backoff_no_jitter(self):
        """Test constant backoff without jitter."""
        delay = constant_backoff(0, 2.5, 60.0, jitter=False)
        assert delay == 2.5
        
        delay = constant_backoff(5, 2.5, 60.0, jitter=False)
        assert delay == 2.5  # Always constant


class TestRetryDecorator:
    """Test retry decorator for synchronous functions."""
    
    def test_retry_succeeds_first_attempt(self):
        """Test function succeeds on first attempt (no retries)."""
        mock_func = Mock(return_value="success")
        
        @retry(RetryConfig(max_attempts=3))
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_succeeds_after_retries(self):
        """Test function succeeds after some retries."""
        call_count = 0
        
        @retry(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False))
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = test_func()
        
        assert result == "success"
        assert call_count == 3  # Failed twice, succeeded third time
    
    def test_retry_exhausts_attempts(self):
        """Test retry exhausts all attempts and raises exception."""
        @retry(RetryConfig(max_attempts=2, base_delay=0.01))
        def test_func():
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError, match="Persistent failure"):
            test_func()
    
    def test_retry_non_retryable_exception(self):
        """Test non-retryable exceptions are not retried."""
        mock_func = Mock(side_effect=ValueError("Invalid input"))
        
        @retry(RetryConfig(max_attempts=3))
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError, match="Invalid input"):
            test_func()
        
        assert mock_func.call_count == 1  # No retries
    
    def test_retry_custom_condition(self):
        """Test custom retry condition."""
        def should_retry(exc):
            # Only retry if message contains "please"
            return "please" in str(exc).lower()
        
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.01,
            retry_condition=should_retry
        )
        
        call_count = 0
        
        @retry(config)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Please retry this")
            else:
                raise Exception("Do not retry")  # Won't be retried (no "please")
        
        with pytest.raises(Exception, match="Do not retry"):
            test_func()
        
        assert call_count == 2  # Retried once, then failed without more retries


class TestAsyncRetryDecorator:
    """Test async retry decorator."""
    
    @pytest.mark.asyncio
    async def test_async_retry_succeeds_first_attempt(self):
        """Test async function succeeds on first attempt."""
        @async_retry(RetryConfig(max_attempts=3))
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_retry_succeeds_after_retries(self):
        """Test async function succeeds after retries."""
        call_count = 0
        
        @async_retry(RetryConfig(max_attempts=3, base_delay=0.01, jitter=False))
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_retry_exhausts_attempts(self):
        """Test async retry exhausts all attempts."""
        @async_retry(RetryConfig(max_attempts=2, base_delay=0.01))
        async def test_func():
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError):
            await test_func()


# ==================== CIRCUIT BREAKER TESTS ====================

class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator."""
    
    def test_circuit_breaker_closed_state_success(self):
        """Test circuit breaker allows requests in CLOSED state."""
        config = CircuitBreakerConfig(name="test_circuit_1", failure_threshold=3)
        
        @circuit_breaker(config)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
        
        stats = get_circuit_breaker_stats("test_circuit_1")
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        config = CircuitBreakerConfig(
            name="test_circuit_2",
            failure_threshold=3,
            recovery_timeout=60.0
        )
        
        call_count = 0
        
        @circuit_breaker(config)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Service unavailable")
        
        # Make failures to reach threshold
        for i in range(3):
            with pytest.raises(ConnectionError):
                test_func()
        
        stats = get_circuit_breaker_stats("test_circuit_2")
        assert stats["state"] == "open"
        assert stats["failure_count"] >= 3
        
        # Next call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            test_func()
        
        # Total calls should be 3 (failures) + 0 (blocked by circuit)
        # The blocked call doesn't reach the function
        assert call_count == 3
    
    def test_circuit_breaker_half_open_transition(self):
        """Test circuit breaker transitions to HALF_OPEN after recovery timeout."""
        config = CircuitBreakerConfig(
            name="test_circuit_3",
            failure_threshold=2,
            recovery_timeout=0.1,  # Short timeout for testing
            success_threshold=1
        )
        
        call_count = 0
        should_fail = True
        
        @circuit_breaker(config)
        def test_func():
            nonlocal call_count, should_fail
            call_count += 1
            if should_fail:
                raise ConnectionError("Service unavailable")
            return "success"
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(ConnectionError):
                test_func()
        
        stats = get_circuit_breaker_stats("test_circuit_3")
        assert stats["state"] == "open"
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should trigger HALF_OPEN state
        should_fail = False
        result = test_func()
        
        assert result == "success"
        stats = get_circuit_breaker_stats("test_circuit_3")
        assert stats["state"] == "closed"  # Closed after success in HALF_OPEN
    
    def test_circuit_breaker_ignores_non_failure_exceptions(self):
        """Test circuit breaker ignores exceptions not in failure_exceptions."""
        config = CircuitBreakerConfig(
            name="test_circuit_4",
            failure_threshold=2,
            failure_exceptions={ConnectionError},
            ignored_exceptions={ValueError}
        )
        
        @circuit_breaker(config)
        def test_func():
            raise ValueError("Invalid input")
        
        # ValueError should not count as failure
        for i in range(5):
            with pytest.raises(ValueError):
                test_func()
        
        stats = get_circuit_breaker_stats("test_circuit_4")
        assert stats["state"] == "closed"  # Still closed
        assert stats["failure_count"] == 0
    
    def test_circuit_breaker_with_fallback(self):
        """Test circuit breaker uses fallback when open."""
        def fallback(exc, *args, **kwargs):
            return "fallback_result"
        
        config = CircuitBreakerConfig(
            name="test_circuit_5",
            failure_threshold=2,
            fallback=fallback
        )
        
        @circuit_breaker(config)
        def test_func():
            raise ConnectionError("Service unavailable")
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(ConnectionError):
                test_func()
        
        # Next call should use fallback
        result = test_func()
        assert result == "fallback_result"


class TestAsyncCircuitBreaker:
    """Test async circuit breaker."""
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker_success(self):
        """Test async circuit breaker with successful calls."""
        config = CircuitBreakerConfig(name="test_async_circuit_1")
        
        @async_circuit_breaker(config)
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker_opens(self):
        """Test async circuit breaker opens after failures."""
        config = CircuitBreakerConfig(
            name="test_async_circuit_2",
            failure_threshold=3
        )
        
        @async_circuit_breaker(config)
        async def test_func():
            raise ConnectionError("Service unavailable")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(ConnectionError):
                await test_func()
        
        # Should fail fast now
        with pytest.raises(CircuitBreakerOpenError):
            await test_func()


class TestCircuitBreakerStats:
    """Test circuit breaker statistics."""
    
    def test_get_circuit_breaker_stats(self):
        """Test getting stats for specific circuit."""
        config = CircuitBreakerConfig(name="test_stats_circuit")
        
        @circuit_breaker(config)
        def test_func():
            return "success"
        
        test_func()
        
        stats = get_circuit_breaker_stats("test_stats_circuit")
        assert stats is not None
        assert stats["name"] == "test_stats_circuit"
        assert stats["state"] == "closed"
        assert "failure_count" in stats
        assert "success_count" in stats
    
    def test_get_all_circuit_breaker_stats(self):
        """Test getting stats for all circuits."""
        # Create multiple circuits
        for i in range(3):
            config = CircuitBreakerConfig(name=f"test_all_stats_{i}")
            
            @circuit_breaker(config)
            def test_func():
                return "success"
            
            test_func()
        
        all_stats = get_all_circuit_breaker_stats()
        assert isinstance(all_stats, dict)
        assert len(all_stats) >= 3  # At least our 3 circuits


# ==================== TIMEOUT TESTS ====================

class TestAsyncTimeout:
    """Test async timeout decorator."""
    
    @pytest.mark.asyncio
    async def test_async_timeout_succeeds_within_limit(self):
        """Test async function succeeds within timeout."""
        @async_timeout(timeout_seconds=1.0)
        async def test_func():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_timeout_exceeds_limit(self):
        """Test async function times out."""
        @async_timeout(timeout_seconds=0.1)
        async def test_func():
            await asyncio.sleep(1.0)
            return "should not reach here"
        
        with pytest.raises(AppTimeoutError):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_async_timeout_with_config(self):
        """Test async timeout with TimeoutConfig."""
        config = TimeoutConfig(
            timeout_seconds=0.1,
            operation_name="test_operation",
            error_message="Custom timeout message"
        )
        
        @async_timeout(config)
        async def test_func():
            await asyncio.sleep(1.0)
        
        with pytest.raises(AppTimeoutError, match="Custom timeout message"):
            await test_func()


# ==================== INTEGRATION TESTS ====================

class TestResiliencePatternIntegration:
    """Test combining multiple resilience patterns."""
    
    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self):
        """Test retry decorator combined with circuit breaker."""
        retry_config = RetryConfig(max_attempts=2, base_delay=0.01)
        cb_config = CircuitBreakerConfig(
            name="test_integration_1",
            failure_threshold=5
        )
        
        call_count = 0
        
        @async_retry(retry_config)
        @async_circuit_breaker(cb_config)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        # Retry will attempt 3 times (1 initial + 2 retries)
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_timeout_with_retry(self):
        """Test timeout decorator combined with retry."""
        retry_config = RetryConfig(max_attempts=2, base_delay=0.01)
        timeout_config = TimeoutConfig(timeout_seconds=0.5)
        
        @async_retry(retry_config)
        @async_timeout(timeout_config)
        async def test_func():
            await asyncio.sleep(1.0)  # Will timeout
            return "should not reach"
        
        with pytest.raises(AppTimeoutError):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_all_three_patterns(self):
        """Test all three resilience patterns together."""
        retry_config = RetryConfig(max_attempts=2, base_delay=0.01)
        cb_config = CircuitBreakerConfig(
            name="test_integration_all",
            failure_threshold=10  # High threshold for this test
        )
        timeout_config = TimeoutConfig(timeout_seconds=1.0)
        
        call_count = 0
        
        @async_retry(retry_config)
        @async_circuit_breaker(cb_config)
        @async_timeout(timeout_config)
        async def test_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 2  # Failed once, succeeded second time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
