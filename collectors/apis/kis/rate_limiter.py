"""
Rate limiter implementation for KIS API.

Uses Token Bucket algorithm to enforce rate limits.
"""

import time
import threading
from typing import Optional, Callable
from functools import wraps


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float):
        """
        Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message)
        self.retry_after = retry_after


class TokenBucketRateLimiter:
    """
    Token Bucket rate limiter implementation.

    Thread-safe rate limiter that allows burst traffic up to a limit.
    """

    def __init__(self, rate: int, per_seconds: float = 1.0):
        """
        Initialize token bucket rate limiter.

        Args:
            rate: Maximum number of requests per time period
            per_seconds: Time period in seconds
        """
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = float(rate)  # Start with full bucket
        self.last_update = time.time()
        self._lock = threading.Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Calculate how many tokens to add
        tokens_to_add = elapsed * (self.rate / self.per_seconds)

        # Update tokens (cap at max rate)
        self.tokens = min(self.rate, self.tokens + tokens_to_add)
        self.last_update = now

    def acquire(
        self,
        tokens: int = 1,
        timeout: Optional[float] = None,
        raise_on_limit: bool = False
    ) -> bool:
        """
        Acquire tokens from the bucket, blocking if necessary.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = wait forever)
            raise_on_limit: Raise exception instead of returning False

        Returns:
            True if tokens acquired, False if timeout

        Raises:
            RateLimitExceeded: If raise_on_limit=True and timeout occurs
        """
        start_time = time.time()

        while True:
            with self._lock:
                self._refill_tokens()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed * (self.per_seconds / self.rate)

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    if raise_on_limit:
                        raise RateLimitExceeded(
                            f"Rate limit exceeded: {self.rate} requests per {self.per_seconds}s",
                            retry_after=wait_time
                        )
                    return False

                # Sleep for minimum of wait_time or remaining timeout
                sleep_time = min(wait_time, timeout - elapsed)
            else:
                sleep_time = wait_time

            # Sleep and retry
            time.sleep(sleep_time)

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        with self._lock:
            self._refill_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_available_tokens(self) -> int:
        """
        Get current number of available tokens.

        Returns:
            Number of available tokens
        """
        with self._lock:
            self._refill_tokens()
            return int(self.tokens)

    def reset(self) -> None:
        """Reset bucket to full capacity."""
        with self._lock:
            self.tokens = float(self.rate)
            self.last_update = time.time()

    def limit(self, func: Callable) -> Callable:
        """
        Decorator to rate limit a function.

        Args:
            func: Function to rate limit

        Returns:
            Rate-limited function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class RateLimiter:
    """
    Simple rate limiter interface.

    Alias for TokenBucketRateLimiter for backward compatibility.
    """

    def __init__(self, rate: int, per_seconds: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            rate: Maximum number of requests per time period
            per_seconds: Time period in seconds
        """
        self._limiter = TokenBucketRateLimiter(rate, per_seconds)

    def __getattr__(self, name):
        """Delegate all attributes to underlying limiter."""
        return getattr(self._limiter, name)


class AdaptiveRateLimiter(TokenBucketRateLimiter):
    """
    Adaptive rate limiter that adjusts based on 429 responses.

    Automatically backs off when rate limit errors are encountered.
    """

    def __init__(self, rate: int, per_seconds: float = 1.0, backoff_factor: float = 0.5):
        """
        Initialize adaptive rate limiter.

        Args:
            rate: Initial maximum requests per time period
            per_seconds: Time period in seconds
            backoff_factor: Factor to reduce rate by on 429 (0.5 = 50% reduction)
        """
        super().__init__(rate, per_seconds)
        self.initial_rate = rate
        self.backoff_factor = backoff_factor
        self.backoff_until = 0.0

    def on_rate_limit_error(self, retry_after: Optional[float] = None) -> None:
        """
        Called when a 429 rate limit error is encountered.

        Args:
            retry_after: Seconds to wait before retrying (from Retry-After header)
        """
        with self._lock:
            if retry_after:
                self.backoff_until = time.time() + retry_after
            else:
                # Reduce rate temporarily
                self.rate = max(1, int(self.rate * self.backoff_factor))
                self.backoff_until = time.time() + 60  # Back off for 60 seconds

    def _refill_tokens(self) -> None:
        """Refill tokens, considering backoff period."""
        now = time.time()

        # Check if backoff period is over
        if now >= self.backoff_until and self.rate != self.initial_rate:
            # Gradually restore rate
            self.rate = min(self.initial_rate, self.rate + 1)

        super()._refill_tokens()
