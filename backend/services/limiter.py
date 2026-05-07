"""Rate limiting service with per-tier configuration."""

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


class RateLimitService:
    """Per-user, per-tier rate limiting."""

    def __init__(self):
        self._request_log: dict[str, list[float]] = {}
        self._task_counts: dict[str, int] = {}

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
    ) -> dict:
        """Check if a user has exceeded their rate limit."""
        limits = self._get_limits(tier)

        if window == "minute":
            limit = limits["requests_per_minute"]
            window_seconds = 60
        elif window == "hour":
            limit = limits["requests_per_hour"]
            window_seconds = 3600
        elif window == "day":
            limit = limits["requests_per_day"]
            window_seconds = 86400
        else:
            return {"allowed": True, "remaining": -1}

        if limit == -1:
            return {"allowed": True, "remaining": -1}

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

    def record_request(self, user_id: str):
        """Record a request for rate limiting."""
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
