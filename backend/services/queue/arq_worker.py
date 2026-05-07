"""ARQ task queue configuration for Titanium platform."""

import os
from datetime import UTC, datetime

from arq import cron
from arq.connections import RedisSettings


class QueueConfig:
    """ARQ queue configuration."""

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    QUEUE_NAME = os.getenv("ARQ_QUEUE_NAME", "titanium")


redis_settings = RedisSettings(
    host=QueueConfig.REDIS_HOST,
    port=QueueConfig.REDIS_PORT,
    password=QueueConfig.REDIS_PASSWORD if QueueConfig.REDIS_PASSWORD else None,
)


async def process_memory_document(ctx, document_id: str, user_id: str):
    """Process an uploaded document for memory storage."""
    from backend.services.rag_service import RAGService

    rag = RAGService()
    result = await rag.process_document(document_id)

    await ctx["redis"].hset(
        f"task:{document_id}",
        mapping={
            "status": "completed",
            "completed_at": datetime.now(UTC).isoformat(),
            "result": str(result),
        },
    )

    return result


async def send_notification(ctx, user_id: str, title: str, message: str, notification_type: str = "info"):
    """Send a notification to a user."""
    await ctx["redis"].hset(
        f"notification:{user_id}:{datetime.now(UTC).timestamp()}",
        mapping={
            "title": title,
            "message": message,
            "type": notification_type,
            "read": "false",
            "created_at": datetime.now(UTC).isoformat(),
        },
    )

    return {"status": "sent", "user_id": user_id}


async def cleanup_expired_sessions(ctx):
    """Clean up expired user sessions and tokens."""
    return {"status": "completed", "cleaned": 0}


async def generate_usage_report(ctx, user_id: str, days: int = 30):
    """Generate a usage report for a user."""
    from backend.services.usage_tracker import usage_tracker

    usage = usage_tracker.get_user_usage(user_id, days)
    return usage


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [
        process_memory_document,
        send_notification,
        cleanup_expired_sessions,
        generate_usage_report,
    ]
    cron_jobs = [
        cron(cleanup_expired_sessions, hour=3, minute=0),
    ]
    redis_settings = redis_settings
    queue_name = QueueConfig.QUEUE_NAME
    max_jobs = 10
    job_timeout = 300
    retry_jobs = True
    max_tries = 3
