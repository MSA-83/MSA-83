"""Analytics service for tracking usage and system metrics."""

from datetime import UTC, datetime, timedelta

from backend.models.analytics_event import AnalyticsEvent
from backend.models.database import get_db
from backend.models.user import User


class AnalyticsService:
    """Service for collecting and querying analytics data."""

    async def track_event(
        self,
        user_id: str,
        event_type: str,
        metadata: dict | None = None,
        value: float | None = None,
    ) -> None:
        """Track an analytics event."""
        db = next(get_db())
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                metadata=metadata or {},
                value=value,
                occurred_at=datetime.now(UTC),
            )
            db.add(event)
            db.commit()
        finally:
            db.close()

    async def get_user_usage(self, user_id: str, days: int = 30) -> dict:
        """Get usage statistics for a user over the past N days."""
        db = next(get_db())
        try:
            cutoff = datetime.now(UTC) - timedelta(days=days)

            events = (
                db.query(AnalyticsEvent)
                .filter(
                    AnalyticsEvent.user_id == user_id,
                    AnalyticsEvent.occurred_at >= cutoff,
                )
                .all()
            )

            total_requests = len(events)
            total_tokens = sum(e.value or 0 for e in events if e.event_type == "llm_call")

            by_type = {}
            for e in events:
                by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

            daily_breakdown = {}
            for e in events:
                day_key = e.occurred_at.strftime("%Y-%m-%d")
                daily_breakdown[day_key] = daily_breakdown.get(day_key, 0) + 1

            return {
                "user_id": user_id,
                "period_days": days,
                "total_requests": total_requests,
                "total_tokens_estimated": total_tokens,
                "by_event_type": by_type,
                "daily_breakdown": daily_breakdown,
            }
        finally:
            db.close()

    async def get_system_metrics(self, days: int = 30) -> dict:
        """Get system-wide metrics."""
        db = next(get_db())
        try:
            cutoff = datetime.now(UTC) - timedelta(days=days)

            total_users = db.query(User).count()
            active_users = (
                db.query(AnalyticsEvent.user_id).filter(AnalyticsEvent.occurred_at >= cutoff).distinct().count()
            )

            total_events = db.query(AnalyticsEvent).filter(AnalyticsEvent.occurred_at >= cutoff).count()

            events_by_type = (
                db.query(AnalyticsEvent.event_type, db.func.count(AnalyticsEvent.id))
                .filter(AnalyticsEvent.occurred_at >= cutoff)
                .group_by(AnalyticsEvent.event_type)
                .all()
            )

            daily_active = (
                db.query(
                    db.func.date(AnalyticsEvent.occurred_at),
                    db.func.count(db.distinct(AnalyticsEvent.user_id)),
                )
                .filter(AnalyticsEvent.occurred_at >= cutoff)
                .group_by(db.func.date(AnalyticsEvent.occurred_at))
                .all()
            )

            return {
                "period_days": days,
                "total_users": total_users,
                "active_users": active_users,
                "total_events": total_events,
                "events_by_type": {t: c for t, c in events_by_type},
                "daily_active_users": {str(d): c for d, c in daily_active},
            }
        finally:
            db.close()

    async def get_top_users(self, limit: int = 10, days: int = 30) -> list[dict]:
        """Get users with highest activity."""
        db = next(get_db())
        try:
            cutoff = datetime.now(UTC) - timedelta(days=days)

            top = (
                db.query(
                    AnalyticsEvent.user_id,
                    db.func.count(AnalyticsEvent.id).label("event_count"),
                )
                .filter(AnalyticsEvent.occurred_at >= cutoff)
                .group_by(AnalyticsEvent.user_id)
                .order_by(db.func.count(AnalyticsEvent.id).desc())
                .limit(limit)
                .all()
            )

            results = []
            for user_id, count in top:
                user = db.query(User).filter(User.id == user_id).first()
                results.append(
                    {
                        "user_id": user_id,
                        "email": user.email if user else "unknown",
                        "event_count": count,
                    }
                )

            return results
        finally:
            db.close()
