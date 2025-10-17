"""
Simple in-memory cache utility for API responses
"""
import time
from typing import Dict, Any, Optional
from logger_config import get_logger

logger = get_logger(__name__)


class SimpleCache:
    """In-memory cache with TTL support"""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self._cache:
            self.misses += 1
            logger.debug("cache_miss", context={"key": key})
            return None

        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            # Expired
            del self._cache[key]
            self.misses += 1
            logger.debug("cache_expired", context={"key": key})
            return None

        self.hits += 1
        logger.debug("cache_hit", context={"key": key})
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
        logger.debug(
            "cache_set",
            context={"key": key, "ttl": ttl}
        )

    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_delete", context={"key": key})

    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("cache_cleared", context={"entries_cleared": count})

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry["expires_at"]
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(
                "cache_cleanup",
                context={"expired_entries": len(expired_keys)}
            )

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2)
        }
