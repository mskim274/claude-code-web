"""
Unit tests for KIS API rate limiter.

TDD Red Phase: Write failing tests first.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

# Import will fail initially - this is expected in TDD Red phase
try:
    from collectors.apis.kis.rate_limiter import (
        RateLimiter,
        TokenBucketRateLimiter,
        RateLimitExceeded
    )
except ImportError:
    pytest.skip("Rate limiter not implemented yet", allow_module_level=True)


class TestTokenBucketRateLimiter:
    """Test Token Bucket rate limiter implementation."""

    def test_initialization_with_default_params(self):
        """Test rate limiter initialization with default parameters."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        assert limiter.rate == 5
        assert limiter.per_seconds == 1
        assert limiter.tokens == 5  # Should start full

    def test_initialization_with_custom_params(self):
        """Test rate limiter initialization with custom parameters."""
        limiter = TokenBucketRateLimiter(rate=10, per_seconds=60)

        assert limiter.rate == 10
        assert limiter.per_seconds == 60

    def test_acquire_single_token_success(self):
        """Test acquiring a single token successfully."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        result = limiter.acquire()
        assert result is True

    def test_acquire_multiple_tokens_within_limit(self):
        """Test acquiring multiple tokens within rate limit."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        # Should be able to acquire 5 tokens immediately
        for _ in range(5):
            assert limiter.acquire() is True

    def test_acquire_exceeding_limit_blocks(self):
        """Test that acquiring beyond limit blocks/waits."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        # Consume all tokens
        for _ in range(5):
            limiter.acquire()

        # Next acquire should take time (wait for refill)
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start

        # Should have waited approximately the refill time
        assert elapsed >= 0.15  # Allow some tolerance

    def test_acquire_with_timeout(self):
        """Test acquire with timeout parameter."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        # Consume all tokens
        for _ in range(5):
            limiter.acquire()

        # Try to acquire with short timeout
        result = limiter.acquire(timeout=0.1)
        assert result is False  # Should timeout

    def test_try_acquire_returns_false_when_no_tokens(self):
        """Test try_acquire returns False without waiting."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        # Consume all tokens
        for _ in range(5):
            limiter.acquire()

        # try_acquire should immediately return False
        start = time.time()
        result = limiter.try_acquire()
        elapsed = time.time() - start

        assert result is False
        assert elapsed < 0.05  # Should be nearly instant

    def test_token_refill_over_time(self):
        """Test that tokens refill over time."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        # Consume all tokens
        for _ in range(5):
            limiter.acquire()

        # Wait for partial refill
        time.sleep(0.4)

        # Should have refilled approximately 2 tokens (0.4s * 5 tokens/s)
        count = 0
        while limiter.try_acquire():
            count += 1
            if count > 3:  # Safety limit
                break

        assert count >= 1  # At least 1 token should have refilled

    def test_get_available_tokens(self):
        """Test getting available token count."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        assert limiter.get_available_tokens() == 5

        # Acquire 3 tokens
        for _ in range(3):
            limiter.acquire()

        assert limiter.get_available_tokens() == 2

    def test_reset_tokens(self):
        """Test resetting tokens to full capacity."""
        limiter = TokenBucketRateLimiter(rate=5, per_seconds=1)

        # Consume some tokens
        for _ in range(3):
            limiter.acquire()

        assert limiter.get_available_tokens() < 5

        # Reset
        limiter.reset()

        assert limiter.get_available_tokens() == 5

    def test_concurrent_access_thread_safety(self):
        """Test thread-safe token acquisition."""
        import threading

        limiter = TokenBucketRateLimiter(rate=10, per_seconds=1)
        results = []

        def acquire_tokens():
            for _ in range(5):
                result = limiter.try_acquire()
                results.append(result)

        # Create multiple threads
        threads = [threading.Thread(target=acquire_tokens) for _ in range(3)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Only 10 should succeed (rate limit)
        assert sum(results) <= 10


class TestRateLimiterDecorator:
    """Test rate limiter as a decorator."""

    def test_decorator_on_function(self):
        """Test using rate limiter as decorator on function."""
        limiter = TokenBucketRateLimiter(rate=3, per_seconds=1)

        @limiter.limit
        def test_function():
            return "success"

        # Should work for rate-limited calls
        results = []
        for _ in range(3):
            results.append(test_function())

        assert len(results) == 3
        assert all(r == "success" for r in results)

    def test_decorator_enforces_rate_limit(self):
        """Test that decorator enforces rate limiting."""
        limiter = TokenBucketRateLimiter(rate=2, per_seconds=1)

        call_count = 0

        @limiter.limit
        def test_function():
            nonlocal call_count
            call_count += 1
            return call_count

        # Call twice (should work)
        test_function()
        test_function()

        # Third call should block briefly
        start = time.time()
        test_function()
        elapsed = time.time() - start

        assert call_count == 3
        assert elapsed >= 0.1  # Should have waited


class TestRateLimitExceeded:
    """Test RateLimitExceeded exception."""

    def test_exception_raised_when_limit_exceeded(self):
        """Test that exception is raised when limit exceeded."""
        limiter = TokenBucketRateLimiter(rate=2, per_seconds=1)

        # Consume all tokens
        limiter.acquire()
        limiter.acquire()

        # Trying to acquire with raise_on_limit should raise exception
        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.acquire(timeout=0.05, raise_on_limit=True)

        assert "Rate limit exceeded" in str(exc_info.value)

    def test_exception_contains_retry_after(self):
        """Test that exception contains retry_after information."""
        limiter = TokenBucketRateLimiter(rate=2, per_seconds=1)

        # Consume all tokens
        limiter.acquire()
        limiter.acquire()

        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.acquire(timeout=0, raise_on_limit=True)

        exception = exc_info.value
        assert hasattr(exception, 'retry_after')
        assert exception.retry_after > 0


class TestMultipleRateLimiters:
    """Test using multiple rate limiters."""

    def test_different_rate_limiters_are_independent(self):
        """Test that different rate limiters don't interfere."""
        limiter1 = TokenBucketRateLimiter(rate=5, per_seconds=1)
        limiter2 = TokenBucketRateLimiter(rate=10, per_seconds=1)

        # Exhaust limiter1
        for _ in range(5):
            limiter1.acquire()

        # limiter2 should still have tokens
        assert limiter2.get_available_tokens() == 10
        assert limiter2.try_acquire() is True
