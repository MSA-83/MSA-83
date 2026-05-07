"""Redis caching service for Titanium platform."""

import json
import os
from typing import Any

import redis


class CacheConfig:
    """Redis configuration."""

    URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    TOKEN = os.getenv("REDIS_TOKEN", "")
    DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
    PREFIX = "titanium"


class RedisCache:
    """Redis-based caching layer."""

    def __init__(self, prefix: str = CacheConfig.PREFIX, default_ttl: int = CacheConfig.DEFAULT_TTL):
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                CacheConfig.URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        return self._client

    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.client.ping()
        except (redis.ConnectionError, redis.TimeoutError, Exception):
            return False

    def _key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        if not self.is_available:
            return None

        try:
            value = self.client.get(self._key(key))
            if value is None:
                return None
            return json.loads(value)
        except (redis.RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in cache."""
        if not self.is_available:
            return False

        try:
            serialized = json.dumps(value, default=str)
            expiry = ttl if ttl is not None else self.default_ttl
            self.client.setex(self._key(key), expiry, serialized)
            return True
        except (redis.RedisError, TypeError):
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self.is_available:
            return False

        try:
            self.client.delete(self._key(key))
            return True
        except redis.RedisError:
            return False

    def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching a pattern."""
        if not self.is_available:
            return False

        try:
            keys = self.client.keys(self._key(pattern))
            if keys:
                self.client.delete(*keys)
            return True
        except redis.RedisError:
            return False

    def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all cached data for a user."""
        return self.delete_pattern(f"user:{user_id}:*")

    def get_cached_or_compute(
        self,
        key: str,
        compute_fn,
        ttl: int | None = None,
    ) -> Any:
        """Get from cache or compute and cache the result."""
        cached = self.get(key)
        if cached is not None:
            return cached

        result = compute_fn()
        self.set(key, result, ttl)
        return result
