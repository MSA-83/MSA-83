"""Task queue service for enqueuing background jobs."""

import os
from typing import Any

from arq.connections import ArqRedis, create_pool, RedisSettings


class QueueConfig:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    QUEUE_NAME = os.getenv("ARQ_QUEUE_NAME", "titanium")


class TaskQueue:
    """Service for enqueueing background tasks."""

    def __init__(self):
        self._pool: ArqRedis | None = None

    async def get_pool(self) -> ArqRedis:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await create_pool(
                RedisSettings(
                    host=QueueConfig.REDIS_HOST,
                    port=QueueConfig.REDIS_PORT,
                    password=QueueConfig.REDIS_PASSWORD if QueueConfig.REDIS_PASSWORD else None,
                )
            )
        return self._pool

    @property
    def is_available(self) -> bool:
        return os.getenv("REDIS_URL") is not None

    async def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> str | None:
        """Enqueue a background task."""
        if not self.is_available:
            return None

        try:
            pool = await self.get_pool()
            job = await pool.enqueue_job(task_name, *args, **kwargs)
            return job.job_id
        except Exception:
            return None

    async def process_document(self, document_id: str, user_id: str) -> str | None:
        """Queue document processing for memory storage."""
        return await self.enqueue("process_memory_document", document_id, user_id)

    async def notify_user(self, user_id: str, title: str, message: str, notification_type: str = "info") -> str | None:
        """Queue a user notification."""
        return await self.enqueue("send_notification", user_id, title, message, notification_type)

    async def generate_report(self, user_id: str, days: int = 30) -> str | None:
        """Queue a usage report generation."""
        return await self.enqueue("generate_usage_report", user_id, days)


task_queue = TaskQueue()
