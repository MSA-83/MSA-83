"""ARQ worker configuration and task definitions."""

import asyncio
import logging
import os
from datetime import datetime

import httpx
from arq import ArqRedis, cron
from arq.connections import RedisSettings

from backend.services.export import CSVExporter, JSONExporter, MarkdownExporter, PDFExporter

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_QUEUE_DB", "1"))

logger = logging.getLogger("titanium.worker")


async def dispatch_webhook(
    ctx: dict,
    webhook_url: str,
    event_type: str,
    payload: dict,
    secret: str = "",
) -> dict:
    """Dispatch a webhook payload to an external endpoint."""
    import hashlib
    import hmac
    import json
    import uuid

    body = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": payload,
    }

    body_json = json.dumps(body, separators=(",", ":"))
    headers = {"Content-Type": "application/json"}

    if secret:
        signature = hmac.new(
            secret.encode(),
            body_json.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    headers["X-Webhook-Event"] = event_type
    headers["X-Request-ID"] = body["id"]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(webhook_url, content=body_json, headers=headers)
            success = 200 <= response.status_code < 300

            if success:
                logger.info("Webhook dispatched: %s -> %s", event_type, webhook_url)
            else:
                logger.warning(
                    "Webhook failed: %s -> %s (HTTP %d)",
                    event_type, webhook_url, response.status_code,
                )

            return {
                "success": success,
                "status_code": response.status_code,
                "event_type": event_type,
            }

    except httpx.TimeoutException:
        logger.error("Webhook timeout: %s -> %s", event_type, webhook_url)
        raise
    except Exception as e:
        logger.error("Webhook error: %s -> %s: %s", event_type, webhook_url, str(e))
        raise


async def generate_pdf_export(
    ctx: dict,
    conversation_id: str,
    title: str,
    messages: list[dict],
    include_metadata: bool = False,
) -> dict:
    """Generate a PDF export asynchronously."""
    try:
        content = PDFExporter.export_conversation(title, messages, include_metadata)

        logger.info("PDF export generated: %s", conversation_id)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "size_bytes": len(content),
            "format": "pdf",
        }
    except Exception as e:
        logger.error("PDF export failed: %s: %s", conversation_id, str(e))
        raise


async def generate_csv_export(
    ctx: dict,
    conversation_id: str,
    messages: list[dict],
) -> dict:
    """Generate a CSV export asynchronously."""
    try:
        content = CSVExporter.export_conversation(messages)

        logger.info("CSV export generated: %s", conversation_id)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "size_bytes": len(content),
            "format": "csv",
        }
    except Exception as e:
        logger.error("CSV export failed: %s: %s", conversation_id, str(e))
        raise


async def generate_json_export(
    ctx: dict,
    conversation_id: str,
    title: str,
    messages: list[dict],
) -> dict:
    """Generate a JSON export asynchronously."""
    try:
        content = JSONExporter.export_conversation(conversation_id, title, messages)

        logger.info("JSON export generated: %s", conversation_id)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "size_bytes": len(content),
            "format": "json",
        }
    except Exception as e:
        logger.error("JSON export failed: %s: %s", conversation_id, str(e))
        raise


async def send_email_notification(
    ctx: dict,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = "",
) -> dict:
    """Send an email notification (stub for future SMTP/SendGrid integration)."""
    api_key = os.getenv("SENDGRID_API_KEY") or os.getenv("SMTP_API_KEY")

    if not api_key:
        logger.info("Email notification (demo mode): %s - %s", to_email, subject)
        return {
            "success": True,
            "demo": True,
            "to": to_email,
            "subject": subject,
        }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": os.getenv("NOTIFICATION_FROM", "noreply@titanium.ai")},
                    "subject": subject,
                    "content": [
                        {"type": "text/plain", "value": body_text or subject},
                        {"type": "text/html", "value": body_html},
                    ],
                },
            )

            success = 200 <= response.status_code < 300
            logger.info(
                "Email %s: %s - %s",
                "sent" if success else "failed",
                to_email,
                subject,
            )

            return {"success": success, "to": to_email, "subject": subject}

    except Exception as e:
        logger.error("Email failed: %s: %s", to_email, str(e))
        raise


async def cleanup_old_exports(ctx: dict) -> dict:
    """Clean up export files older than 7 days."""
    import glob
    import time

    export_dir = os.getenv("EXPORT_DIR", "/tmp/exports")
    if not os.path.exists(export_dir):
        return {"success": True, "cleaned": 0, "message": "No export directory"}

    cutoff = time.time() - (7 * 24 * 3600)
    cleaned = 0

    for filepath in glob.glob(os.path.join(export_dir, "*")):
        try:
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                cleaned += 1
        except OSError:
            pass

    logger.info("Cleaned %d old export files", cleaned)
    return {"success": True, "cleaned": cleaned}


async def refresh_llm_models(ctx: dict) -> dict:
    """Refresh available LLM models from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/tags",
            )

            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                logger.info("Refreshed %d Ollama models: %s", len(model_names), model_names)
                return {"success": True, "models": model_names, "count": len(model_names)}
            else:
                logger.warning("Failed to refresh models: HTTP %d", response.status_code)
                return {"success": False, "status_code": response.status_code}

    except Exception as e:
        logger.error("Model refresh failed: %s", str(e))
        return {"success": False, "error": str(e)}


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [
        "dispatch_webhook",
        "generate_pdf_export",
        "generate_csv_export",
        "generate_json_export",
        "send_email_notification",
        "cleanup_old_exports",
        "refresh_llm_models",
    ]
    cron_jobs = [
        cron("backend.services.worker.tasks.cleanup_old_exports", hour=3, minute=0),
        cron("backend.services.worker.tasks.refresh_llm_models", hour=0, minute=0),
    ]
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT, database=REDIS_DB)
    max_tries = 3
    job_timeout = 300
    retry_jobs = True
    health_check_interval = 10
