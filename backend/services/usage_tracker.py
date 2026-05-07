"""Token usage tracking service."""

from datetime import datetime, timedelta


class UsageTracker:
    """Track API usage metrics per user."""

    def __init__(self):
        self._requests: dict[str, list[dict]] = {}
        self._tokens: dict[str, int] = {}
        self._daily_usage: dict[str, dict] = {}

    def _get_today_key(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d")

    def record_request(
        self,
        user_id: str,
        endpoint: str,
        tokens_used: int = 0,
        response_time_ms: float = 0,
        model: str = "",
    ):
        """Record an API request."""
        if user_id not in self._requests:
            self._requests[user_id] = []

        self._requests[user_id].append(
            {
                "endpoint": endpoint,
                "tokens_used": tokens_used,
                "response_time_ms": response_time_ms,
                "model": model,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        if tokens_used > 0:
            self._tokens[user_id] = self._tokens.get(user_id, 0) + tokens_used

        today = self._get_today_key()
        if user_id not in self._daily_usage:
            self._daily_usage[user_id] = {}

        if today not in self._daily_usage[user_id]:
            self._daily_usage[user_id][today] = {
                "requests": 0,
                "tokens": 0,
                "total_response_time_ms": 0,
            }

        self._daily_usage[user_id][today]["requests"] += 1
        self._daily_usage[user_id][today]["tokens"] += tokens_used
        self._daily_usage[user_id][today]["total_response_time_ms"] += response_time_ms

        self._cleanup_old_data(user_id)

    def get_user_usage(self, user_id: str, days: int = 30) -> dict:
        """Get usage statistics for a user."""
        today = datetime.utcnow()
        usage = self._daily_usage.get(user_id, {})

        total_requests = 0
        total_tokens = 0
        daily_breakdown = []

        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = usage.get(date, {})

            total_requests += day_data.get("requests", 0)
            total_tokens += day_data.get("tokens", 0)

            daily_breakdown.append(
                {
                    "date": date,
                    "requests": day_data.get("requests", 0),
                    "tokens": day_data.get("tokens", 0),
                    "avg_response_time_ms": (
                        day_data.get("total_response_time_ms", 0) / max(day_data.get("requests", 1), 1)
                    ),
                }
            )

        return {
            "user_id": user_id,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "period_days": days,
            "daily_breakdown": list(reversed(daily_breakdown)),
            "all_time_tokens": self._tokens.get(user_id, 0),
        }

    def get_endpoint_stats(self, user_id: str) -> dict:
        """Get per-endpoint usage statistics."""
        requests = self._requests.get(user_id, [])

        endpoint_stats: dict[str, dict] = {}

        for req in requests:
            endpoint = req["endpoint"]
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "count": 0,
                    "total_tokens": 0,
                    "total_response_time_ms": 0,
                    "models": {},
                }

            endpoint_stats[endpoint]["count"] += 1
            endpoint_stats[endpoint]["total_tokens"] += req.get("tokens_used", 0)
            endpoint_stats[endpoint]["total_response_time_ms"] += req.get("response_time_ms", 0)

            model = req.get("model", "unknown")
            if model not in endpoint_stats[endpoint]["models"]:
                endpoint_stats[endpoint]["models"][model] = 0
            endpoint_stats[endpoint]["models"][model] += 1

        for stats in endpoint_stats.values():
            stats["avg_response_time_ms"] = stats["total_response_time_ms"] / max(stats["count"], 1)

        return endpoint_stats

    def get_model_usage(self, user_id: str) -> dict:
        """Get per-model usage statistics."""
        requests = self._requests.get(user_id, [])

        model_stats: dict[str, dict] = {}

        for req in requests:
            model = req.get("model", "unknown")
            if model not in model_stats:
                model_stats[model] = {
                    "count": 0,
                    "total_tokens": 0,
                    "total_response_time_ms": 0,
                }

            model_stats[model]["count"] += 1
            model_stats[model]["total_tokens"] += req.get("tokens_used", 0)
            model_stats[model]["total_response_time_ms"] += req.get("response_time_ms", 0)

        for stats in model_stats.values():
            stats["avg_tokens_per_request"] = stats["total_tokens"] / max(stats["count"], 1)

        return model_stats

    def check_usage_limit(
        self,
        user_id: str,
        tier: str,
        limit_type: str = "requests",
    ) -> dict:
        """Check if user has exceeded usage limits."""
        limits = {
            "free": {"requests_per_day": 500, "tokens_per_day": 50000},
            "pro": {"requests_per_day": 10000, "tokens_per_day": 1000000},
            "enterprise": {"requests_per_day": -1, "tokens_per_day": -1},
            "defense": {"requests_per_day": -1, "tokens_per_day": -1},
        }

        user_limits = limits.get(tier, limits["free"])
        today = self._get_today_key()
        today_usage = self._daily_usage.get(user_id, {}).get(today, {})

        if limit_type == "requests":
            limit = user_limits["requests_per_day"]
            current = today_usage.get("requests", 0)
        else:
            limit = user_limits["tokens_per_day"]
            current = today_usage.get("tokens", 0)

        if limit == -1:
            return {"exceeded": False, "current": current, "limit": -1}

        return {
            "exceeded": current >= limit,
            "current": current,
            "limit": limit,
            "remaining": max(0, limit - current),
        }

    def _cleanup_old_data(self, user_id: str, keep_days: int = 90):
        """Remove usage data older than keep_days."""
        if user_id not in self._daily_usage:
            return

        cutoff = (datetime.utcnow() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
        self._daily_usage[user_id] = {date: data for date, data in self._daily_usage[user_id].items() if date >= cutoff}

        if user_id in self._requests:
            cutoff_dt = datetime.utcnow() - timedelta(days=keep_days)
            self._requests[user_id] = [
                r for r in self._requests[user_id] if datetime.fromisoformat(r["timestamp"]) > cutoff_dt
            ]

    def reset_user(self, user_id: str):
        """Reset all usage data for a user."""
        self._requests.pop(user_id, None)
        self._tokens.pop(user_id, None)
        self._daily_usage.pop(user_id, None)


usage_tracker = UsageTracker()
