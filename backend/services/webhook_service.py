"""Webhook service for managing and dispatching event webhooks."""

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import UTC, datetime

import httpx

from backend.models.database import get_db
from backend.models.webhook import Webhook

SUPPORTED_EVENTS = [
    "chat.message.sent",
    "chat.message.received",
    "agent.task.completed",
    "agent.task.failed",
    "memory.document.processed",
    "user.subscription.changed",
    "conversation.created",
]


class WebhookService:
    """Service for managing and dispatching webhooks."""

    def create_webhook(self, user_id: str, url: str, events: list[str]) -> dict:
        """Register a new webhook endpoint."""
        secret = f"whsec_{secrets.token_hex(32)}"
        webhook_id = str(uuid.uuid4())

        db = next(get_db())
        try:
            webhook = Webhook(
                id=webhook_id,
                user_id=user_id,
                url=url,
                secret=secret,
                events=events,
            )
            db.add(webhook)
            db.commit()
        finally:
            db.close()

        return {
            "id": webhook_id,
            "url": url,
            "events": events,
            "secret": secret,
            "is_active": True,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def get_webhooks(self, user_id: str) -> list[dict]:
        """List all webhooks for a user."""
        db = next(get_db())
        try:
            webhooks = db.query(Webhook).filter(Webhook.user_id == user_id).all()
            return [
                {
                    "id": w.id,
                    "url": w.url,
                    "events": w.events,
                    "is_active": w.is_active,
                    "last_delivery_at": w.last_delivery_at.isoformat() if w.last_delivery_at else None,
                    "last_delivery_status": w.last_delivery_status,
                    "failure_count": w.failure_count,
                    "created_at": w.created_at.isoformat(),
                }
                for w in webhooks
            ]
        finally:
            db.close()

    def delete_webhook(self, user_id: str, webhook_id: str) -> bool:
        """Delete a webhook."""
        db = next(get_db())
        try:
            webhook = db.query(Webhook).filter(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id,
            ).first()
            if not webhook:
                return False
            db.delete(webhook)
            db.commit()
            return True
        finally:
            db.close()

    def toggle_webhook(self, user_id: str, webhook_id: str) -> bool:
        """Toggle a webhook active/inactive."""
        db = next(get_db())
        try:
            webhook = db.query(Webhook).filter(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id,
            ).first()
            if not webhook:
                return False
            webhook.is_active = not webhook.is_active
            db.commit()
            return True
        finally:
            db.close()

    async def dispatch(self, event_type: str, payload: dict) -> int:
        """Dispatch an event to all matching webhooks."""
        db = next(get_db())
        try:
            webhooks = db.query(Webhook).filter(
                Webhook.is_active == True,
                Webhook.failure_count < 5,
            ).all()

            dispatched = 0
            for webhook in webhooks:
                if event_type not in webhook.events and "*" not in webhook.events:
                    continue

                success = await self._send_webhook(webhook, event_type, payload)
                if success:
                    webhook.last_delivery_at = datetime.now(UTC)
                    webhook.last_delivery_status = "success"
                    webhook.failure_count = 0
                    dispatched += 1
                else:
                    webhook.failure_count += 1
                    webhook.last_delivery_status = "failed"

            db.commit()
            return dispatched
        finally:
            db.close()

    async def _send_webhook(self, webhook: Webhook, event_type: str, payload: dict) -> bool:
        """Send a webhook payload to the endpoint."""
        body = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": payload,
        }

        body_json = json.dumps(body, separators=(",", ":"))
        signature = hmac.new(
            webhook.secret.encode(),
            body_json.encode(),
            hashlib.sha256,
        ).hexdigest()

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    webhook.url,
                    content=body_json,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": f"sha256={signature}",
                        "X-Webhook-Event": event_type,
                    },
                )
                return 200 <= response.status_code < 300
        except Exception:
            return False

    def get_supported_events(self) -> list[str]:
        """Get list of supported webhook events."""
        return SUPPORTED_EVENTS


webhook_service = WebhookService()
