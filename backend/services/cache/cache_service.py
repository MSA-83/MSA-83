"""Redis caching service for Titanium platform."""

import hashlib
import json
import os
from typing import Any


class CacheConfig:
    """Cache configuration."""

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
    CHAT_TTL = int(os.getenv("CACHE_CHAT_TTL", "600"))
    MEMORY_TTL = int(os.getenv("CACHE_MEMORY_TTL", "3600"))
    PRICING_TTL = int(os.getenv("CACHE_PRICING_TTL", "86400"))


class CacheService:
    """Redis-based caching service."""

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or CacheConfig.REDIS_URL
        self._client = None
        self._use_memory_fallback = True
        self._memory_cache: dict[str, tuple[Any, float]] = {}

    async def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                )
                await self._client.ping()
                self._use_memory_fallback = False
            except Exception:
                self._use_memory_fallback = True
        return self._client

    def _make_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments."""
        key_parts = [prefix] + [str(a) for a in args]
        raw_key = ":".join(key_parts)
        if len(raw_key) > 200:
            hashed = hashlib.md5(raw_key.encode()).hexdigest()[:16]
            return f"{prefix}:{hashed}"
        return raw_key

    async def get(self, prefix: str, *args) -> Any | None:
        """Get a cached value."""
        key = self._make_key(prefix, *args)

        if self._use_memory_fallback:
            import time

            if key in self._memory_cache:
                value, expiry = self._memory_cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self._memory_cache[key]
            return None

        client = await self._get_client()
        try:
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception:
            return None

    async def set(
        self,
        prefix: str,
        value: Any,
        ttl: int | None = None,
        *args,
    ) -> bool:
        """Set a cached value."""
        key = self._make_key(prefix, *args)
        ttl = ttl or CacheConfig.DEFAULT_TTL

        if self._use_memory_fallback:
            import time

            self._memory_cache[key] = (value, time.time() + ttl)
            return True

        try:
            client = await self._get_client()
            serialized = json.dumps(value, default=str)
            await client.setex(key, ttl, serialized)
            return True
        except Exception:
            return False

    async def delete(self, prefix: str, *args) -> bool:
        """Delete a cached value."""
        key = self._make_key(prefix, *args)

        if self._use_memory_fallback:
            if key in self._memory_cache:
                del self._memory_cache[key]
            return True

        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception:
            return False

    async def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys matching a prefix."""
        if self._use_memory_fallback:
            import time

            now = time.time()
            count = 0
            expired = []
            for key, (value, expiry) in self._memory_cache.items():
                if key.startswith(prefix) and expiry < now:
                    expired.append(key)
                    count += 1
            for key in expired:
                del self._memory_cache[key]
            return count

        try:
            client = await self._get_client()
            keys = await client.keys(f"{prefix}:*")
            if keys:
                await client.delete(*keys)
            return len(keys)
        except Exception:
            return 0

    async def get_or_set(
        self,
        prefix: str,
        func,
        ttl: int | None = None,
        *args,
    ) -> Any:
        """Get from cache or compute and cache the result."""
        cached = await self.get(prefix, *args)
        if cached is not None:
            return cached

        result = await func()
        await self.set(prefix, result, ttl, *args)
        return result

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if self._use_memory_fallback:
            import time

            now = time.time()
            active = sum(1 for _, (_, exp) in self._memory_cache.items() if exp > now)
            return {
                "backend": "memory",
                "active_entries": active,
                "total_entries": len(self._memory_cache),
            }

        try:
            client = await self._get_client()
            info = await client.info("memory")
            return {
                "backend": "redis",
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception:
            return {"backend": "error", "status": "unavailable"}


cache_service = CacheService()


class CacheDecorator:
    """Decorator for caching function results."""

    def __init__(self, ttl: int | None = None, prefix: str = "func"):
        self.ttl = ttl
        self.prefix = prefix

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{self.prefix}:{func.__name__}"

            cached = await cache_service.get(cache_key, *args, str(kwargs))
            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            await cache_service.set(
                cache_key,
                result,
                self.ttl,
                *args,
                str(kwargs),
            )
            return result

        return wrapper
