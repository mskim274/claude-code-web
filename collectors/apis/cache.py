"""
API response caching system with TTL support.

This module provides caching functionality to reduce redundant API calls
and improve performance.
"""
from typing import Optional, Any, Dict, Callable
from datetime import datetime, timedelta
import hashlib
import json
import functools
import threading
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """Single cache entry with value and expiration"""
    value: Any
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return datetime.now() >= self.expires_at

    def is_valid(self) -> bool:
        """Check if entry is valid (not expired)"""
        return not self.is_expired()


class APICache:
    """
    API response caching with TTL support.

    Features:
    - TTL-based expiration
    - Thread-safe operations
    - Automatic cleanup of expired entries
    - Cache statistics
    """

    def __init__(self, ttl_seconds: int = 60, max_size: int = 1000):
        """
        Initialize cache

        Args:
            ttl_seconds: Time to live for cache entries in seconds
            max_size: Maximum number of entries in cache
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_valid():
                    entry.hit_count += 1
                    self._stats["hits"] += 1
                    return entry.value
                else:
                    # Remove expired entry
                    del self._cache[key]

            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Override default TTL for this entry
        """
        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
            expires_at = datetime.now() + timedelta(seconds=ttl)

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=expires_at
            )
            self._stats["sets"] += 1

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats["evictions"] += len(self._cache)

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]

            count = len(expired_keys)
            self._stats["evictions"] += count
            return count

    def _evict_oldest(self) -> None:
        """Evict oldest entry based on creation time"""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]
        self._stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests
                if total_requests > 0
                else 0.0
            )

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "evictions": self._stats["evictions"],
                "hit_rate": round(hit_rate * 100, 2),
                "total_requests": total_requests,
            }

    def reset_stats(self) -> None:
        """Reset cache statistics"""
        with self._lock:
            self._stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "evictions": 0,
            }

    @staticmethod
    def make_key(func_name: str, **kwargs) -> str:
        """
        Generate cache key from function name and arguments

        Args:
            func_name: Function name
            **kwargs: Function arguments

        Returns:
            Cache key (MD5 hash)
        """
        # Sort kwargs for consistent hashing
        params = json.dumps(kwargs, sort_keys=True, default=str)
        key_string = f"{func_name}:{params}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def __len__(self) -> int:
        """Get number of entries in cache"""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache and is valid"""
        return self.get(key) is not None


def cache_response(ttl_seconds: int = 60):
    """
    Decorator to cache function responses

    Args:
        ttl_seconds: Time to live for cached responses

    Usage:
        @cache_response(ttl_seconds=300)
        def get_stock_price(code: str) -> dict:
            return api.get_price(code)
    """
    def decorator(func: Callable) -> Callable:
        cache = APICache(ttl_seconds=ttl_seconds)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = APICache.make_key(
                func.__name__,
                args=args,
                **kwargs
            )

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        # Add cache management methods to wrapper
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        wrapper.get_cache_stats = cache.get_stats

        return wrapper

    return decorator


class MultiLevelCache:
    """
    Multi-level caching system with L1 (memory) and optional L2 (file/db)

    Currently implements L1 only. L2 can be added later for persistence.
    """

    def __init__(
        self,
        l1_ttl: int = 60,
        l1_max_size: int = 1000
    ):
        """
        Initialize multi-level cache

        Args:
            l1_ttl: L1 cache TTL in seconds
            l1_max_size: L1 cache max size
        """
        self.l1 = APICache(ttl_seconds=l1_ttl, max_size=l1_max_size)

    def get(self, key: str) -> Optional[Any]:
        """Get from L1 cache"""
        return self.l1.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set in L1 cache"""
        self.l1.set(key, value)

    def clear(self) -> None:
        """Clear all caches"""
        self.l1.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics"""
        return {
            "l1": self.l1.get_stats(),
        }
