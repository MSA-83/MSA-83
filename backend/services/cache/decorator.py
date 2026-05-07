"""Cache decorator for FastAPI endpoints."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Request

from backend.services.cache.redis_cache import RedisCache

cache = RedisCache()


def cached(key_prefix: str, ttl: int = 300):
    """Decorator to cache endpoint responses.

    Usage:
        @router.get("/pricing")
        @cached("pricing", ttl=600)
        async def get_pricing():
            return await stripe_service.get_pricing()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, request: Request = None, **kwargs: Any) -> Any:
            cache_key = f"{key_prefix}:{hash(str(kwargs))}"

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = await func(*args, request=request, **kwargs) if request else await func(*args, **kwargs)

            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
