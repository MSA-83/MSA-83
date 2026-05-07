"""Audit logging service for tracking administrative actions."""

from datetime import UTC, datetime, timedelta

from backend.models.audit_log import AuditLog
from backend.models.database import get_db


class AuditService:
    """Service for recording and querying audit logs."""

    async def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Record an audit log entry."""
        db = next(get_db())
        try:
            entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(UTC),
            )
            db.add(entry)
            db.commit()
        finally:
            db.close()

    async def get_logs(
        self,
        user_id: str | None = None,
        resource_type: str | None = None,
        days: int = 30,
        limit: int = 100,
    ) -> list[dict]:
        """Query audit logs with filters."""
        db = next(get_db())
        try:
            cutoff = datetime.now(UTC) - timedelta(days=days)
            query = db.query(AuditLog).filter(AuditLog.timestamp >= cutoff)

            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)

            logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

            return [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "timestamp": log.timestamp.isoformat(),
                }
                for log in logs
            ]
        finally:
            db.close()

    async def get_stats(self, days: int = 30) -> dict:
        """Get audit log statistics."""
        db = next(get_db())
        try:
            cutoff = datetime.now(UTC) - timedelta(days=days)

            total = (
                db.query(AuditLog)
                .filter(AuditLog.timestamp >= cutoff)
                .count()
            )

            by_action = (
                db.query(AuditLog.action, db.func.count(AuditLog.id))
                .filter(AuditLog.timestamp >= cutoff)
                .group_by(AuditLog.action)
                .all()
            )

            by_resource = (
                db.query(AuditLog.resource_type, db.func.count(AuditLog.id))
                .filter(AuditLog.timestamp >= cutoff)
                .group_by(AuditLog.resource_type)
                .all()
            )

            return {
                "period_days": days,
                "total_entries": total,
                "by_action": {action: count for action, count in by_action},
                "by_resource_type": {rt: count for rt, count in by_resource},
            }
        finally:
            db.close()
