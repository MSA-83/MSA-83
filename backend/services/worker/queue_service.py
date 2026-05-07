"""Queue service for async task execution via ARQ."""

import os

from arq.connections import ArqRedis, RedisSettings

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_QUEUE_DB", "1"))

_queue: ArqRedis | None = None


async def get_queue() -> ArqRedis:
    """Get or create the ARQ Redis connection."""
    global _queue
    if _queue is None:
        settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT, database=REDIS_DB)
        _queue = await ArqRedis.from_settings(settings)
    return _queue


async def close_queue():
    """Close the ARQ Redis connection."""
    global _queue
    if _queue:
        await _queue.close()
        _queue = None


async def enqueue_webhook(
    webhook_url: str,
    event_type: str,
    payload: dict,
    secret: str = "",
) -> str | None:
    """Enqueue a webhook dispatch task."""
    try:
        queue = await get_queue()
        job = await queue.enqueue(
            "dispatch_webhook",
            webhook_url=webhook_url,
            event_type=event_type,
            payload=payload,
            secret=secret,
        )
        return job.job_id if job else None
    except Exception:
        return None


async def enqueue_export(
    export_type: str,
    conversation_id: str,
    title: str = "",
    messages: list | None = None,
    include_metadata: bool = False,
) -> str | None:
    """Enqueue an export generation task."""
    messages = messages or []
    try:
        queue = await get_queue()

        task_map = {
            "pdf": "generate_pdf_export",
            "csv": "generate_csv_export",
            "json": "generate_json_export",
        }

        task_name = task_map.get(export_type)
        if not task_name:
            return None

        kwargs = {
            "conversation_id": conversation_id,
            "messages": messages,
        }

        if export_type == "pdf":
            kwargs["title"] = title
            kwargs["include_metadata"] = include_metadata
        elif export_type == "json":
            kwargs["title"] = title

        job = await queue.enqueue(task_name, **kwargs)
        return job.job_id if job else None
    except Exception:
        return None


async def enqueue_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = "",
) -> str | None:
    """Enqueue an email notification task."""
    try:
        queue = await get_queue()
        job = await queue.enqueue(
            "send_email_notification",
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )
        return job.job_id if job else None
    except Exception:
        return None
