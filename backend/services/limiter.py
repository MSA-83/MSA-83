"""Rate limiting service with per-tier and per-endpoint configuration."""

import os
import time

TIER_LIMITS = {
    "free": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 500,
        "max_tokens_per_request": 2048,
        "max_file_size_mb": 5,
        "max_concurrent_tasks": 1,
    },
    "pro": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000,
        "max_tokens_per_request": 8192,
        "max_file_size_mb": 25,
        "max_concurrent_tasks": 5,
    },
    "enterprise": {
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
        "requests_per_day": -1,
        "max_tokens_per_request": 32768,
        "max_file_size_mb": 50,
        "max_concurrent_tasks": -1,
    },
    "defense": {
        "requests_per_minute": -1,
        "requests_per_hour": -1,
        "requests_per_day": -1,
        "max_tokens_per_request": -1,
        "max_file_size_mb": -1,
        "max_concurrent_tasks": -1,
    },
}

ENDPOINT_MULTIPLIERS = {
    "/api/chat": 2.0,
    "/api/agents": 3.0,
    "/api/memory": 1.5,
    "/api/export": 0.5,
    "/api/health": 0.1,
    "/api/auth": 0.5,
}

USE_REDIS = os.getenv("REDIS_URL") is not None


class RateLimitService:
    """Per-user, per-tier rate limiting with Redis support."""

    def __init__(self):
        self._request_log: dict[str, list[float]] = {}
        self._task_counts: dict[str, int] = {}
        self._redis_client = None

    def _get_redis_client(self):
        if self._redis_client is None and USE_REDIS:
            import redis

            self._redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
                socket_connect_timeout=2,
            )
        return self._redis_client

    def _get_effective_limit(self, tier: str, window: str, path: str = "") -> int:
        """Get rate limit adjusted for endpoint."""
        limits = self._get_limits(tier)

        if window == "minute":
            base_limit = limits["requests_per_minute"]
        elif window == "hour":
            base_limit = limits["requests_per_hour"]
        elif window == "day":
            base_limit = limits["requests_per_day"]
        else:
            return -1

        if base_limit == -1:
            return -1

        multiplier = 1.0
        for endpoint_prefix, mult in ENDPOINT_MULTIPLIERS.items():
            if path.startswith(endpoint_prefix):
                multiplier = mult
                break

        return max(1, int(base_limit * multiplier))

    def _get_limits(self, tier: str) -> dict:
        """Get rate limits for a tier."""
        return TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    def _cleanup_old_requests(self, user_id: str, window_seconds: int):
        """Remove requests outside the time window."""
        if user_id not in self._request_log:
            return

        cutoff = time.time() - window_seconds
        self._request_log[user_id] = [t for t in self._request_log[user_id] if t > cutoff]

    def check_rate_limit(
        self,
        user_id: str,
        tier: str = "free",
        window: str = "minute",
        path: str = "",
    ) -> dict:
        """Check if a user has exceeded their rate limit."""
        limit = self._get_effective_limit(tier, window, path)

        if limit == -1:
            return {"allowed": True, "remaining": -1, "limit": -1, "current": 0, "reset_in": 0}

        if window == "minute":
            window_seconds = 60
        elif window == "hour":
            window_seconds = 3600
        elif window == "day":
            window_seconds = 86400
        else:
            return {"allowed": True, "remaining": -1, "limit": -1, "current": 0, "reset_in": 0}

        redis_client = self._get_redis_client()
        if redis_client:
            return self._check_redis_rate_limit(redis_client, user_id, window_seconds, limit)

        self._cleanup_old_requests(user_id, window_seconds)
        current_count = len(self._request_log.get(user_id, []))
        remaining = max(0, limit - current_count)

        return {
            "allowed": current_count < limit,
            "remaining": remaining,
            "limit": limit,
            "current": current_count,
            "reset_in": window_seconds,
        }

    def _check_redis_rate_limit(self, redis_client, user_id: str, window_seconds: int, limit: int) -> dict:
        """Check rate limit using Redis sliding window."""
        key = f"ratelimit:{user_id}"
        now = time.time()
        cutoff = now - window_seconds

        redis_client.zremrangebyscore(key, 0, cutoff)
        current_count = redis_client.zcard(key)
        remaining = max(0, limit - current_count)

        return {
            "allowed": current_count < limit,
            "remaining": remaining,
            "limit": limit,
            "current": current_count,
            "reset_in": window_seconds,
        }

    def record_request(self, user_id: str):
        """Record a request for rate limiting."""
        redis_client = self._get_redis_client()
        if redis_client:
            key = f"ratelimit:{user_id}"
            redis_client.zadd(key, {str(time.time()): time.time()})
            redis_client.expire(key, 86400)
            return

        if user_id not in self._request_log:
            self._request_log[user_id] = []
        self._request_log[user_id].append(time.time())

    def check_concurrent_tasks(
        self,
        user_id: str,
        tier: str = "free",
    ) -> dict:
        """Check concurrent task limit."""
        limits = self._get_limits(tier)
        max_tasks = limits["max_concurrent_tasks"]

        if max_tasks == -1:
            return {"allowed": True, "remaining": -1}

        current = self._task_counts.get(user_id, 0)
        remaining = max(0, max_tasks - current)

        return {
            "allowed": current < max_tasks,
            "remaining": remaining,
            "limit": max_tasks,
            "current": current,
        }

    def start_task(self, user_id: str):
        """Increment concurrent task count."""
        self._task_counts[user_id] = self._task_counts.get(user_id, 0) + 1

    def end_task(self, user_id: str):
        """Decrement concurrent task count."""
        if user_id in self._task_counts:
            self._task_counts[user_id] = max(0, self._task_counts[user_id] - 1)

    def get_usage_stats(self, user_id: str, tier: str = "free") -> dict:
        """Get rate limit usage stats for a user."""
        limits = self._get_limits(tier)

        self._cleanup_old_requests(user_id, 86400)

        minute_count = len([t for t in self._request_log.get(user_id, []) if time.time() - t < 60])

        hour_count = len([t for t in self._request_log.get(user_id, []) if time.time() - t < 3600])

        day_count = len(self._request_log.get(user_id, []))

        return {
            "tier": tier,
            "limits": limits,
            "usage": {
                "requests_this_minute": minute_count,
                "requests_this_hour": hour_count,
                "requests_today": day_count,
                "concurrent_tasks": self._task_counts.get(user_id, 0),
            },
        }

    def reset_user(self, user_id: str):
        """Reset all rate limits for a user."""
        if user_id in self._request_log:
            del self._request_log[user_id]
        if user_id in self._task_counts:
            del self._task_counts[user_id]


rate_limit_service = RateLimitService()
