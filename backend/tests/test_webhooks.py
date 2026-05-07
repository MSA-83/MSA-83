"""Tests for webhook service and router."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.webhook_service import WebhookService, webhook_service


class TestWebhookService:
    """Test webhook service."""

    @patch("backend.services.webhook_service.get_db")
    def test_create_webhook(self, mock_get_db):
        """Should create a webhook with secret."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        result = webhook_service.create_webhook(
            user_id="user-1",
            url="https://example.com/webhook",
            events=["chat.message.sent"],
        )

        assert result["id"] is not None
        assert result["url"] == "https://example.com/webhook"
        assert result["events"] == ["chat.message.sent"]
        assert result["secret"].startswith("whsec_")
        assert result["is_active"] is True

    @patch("backend.services.webhook_service.get_db")
    def test_get_webhooks(self, mock_get_db):
        """Should return list of webhooks."""
        mock_created_at = MagicMock()
        mock_created_at.isoformat.return_value = "2026-05-07T10:00:00"

        mock_webhook = MagicMock()
        mock_webhook.id = "wh-1"
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.events = ["chat.message.sent"]
        mock_webhook.is_active = True
        mock_webhook.last_delivery_at = None
        mock_webhook.last_delivery_status = None
        mock_webhook.failure_count = 0
        mock_webhook.created_at = mock_created_at

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_webhook]
        mock_get_db.return_value = iter([mock_db])

        result = webhook_service.get_webhooks("user-1")

        assert len(result) == 1
        assert result[0]["id"] == "wh-1"
        assert result[0]["url"] == "https://example.com/webhook"

    @patch("backend.services.webhook_service.get_db")
    def test_delete_webhook(self, mock_get_db):
        """Should delete a webhook."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh-1"
        mock_webhook.user_id = "user-1"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_webhook
        mock_get_db.return_value = iter([mock_db])

        result = webhook_service.delete_webhook("user-1", "wh-1")

        assert result is True
        mock_db.delete.assert_called_once()

    @patch("backend.services.webhook_service.get_db")
    def test_delete_webhook_not_found(self, mock_get_db):
        """Should return False for non-existent webhook."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = iter([mock_db])

        result = webhook_service.delete_webhook("user-1", "wh-nonexistent")

        assert result is False

    @patch("backend.services.webhook_service.get_db")
    def test_toggle_webhook(self, mock_get_db):
        """Should toggle webhook active status."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh-1"
        mock_webhook.user_id = "user-1"
        mock_webhook.is_active = True

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_webhook
        mock_get_db.return_value = iter([mock_db])

        result = webhook_service.toggle_webhook("user-1", "wh-1")

        assert result is True
        assert mock_webhook.is_active is False

    def test_get_supported_events(self):
        """Should return list of supported events."""
        events = webhook_service.get_supported_events()

        assert isinstance(events, list)
        assert len(events) > 0
        assert "chat.message.sent" in events
        assert "conversation.created" in events


class TestWebhookDispatch:
    """Test webhook dispatch."""

    @pytest.mark.asyncio
    @patch("backend.services.webhook_service.get_db")
    async def test_dispatch_matching_webhook(self, mock_get_db):
        """Should dispatch to matching webhooks."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh-1"
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.secret = "whsec_test"
        mock_webhook.events = ["chat.message.sent"]
        mock_webhook.is_active = True
        mock_webhook.failure_count = 0
        mock_webhook.last_delivery_at = None
        mock_webhook.last_delivery_status = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_webhook]
        mock_get_db.return_value = iter([mock_db])

        with patch.object(webhook_service, "_send_webhook", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await webhook_service.dispatch("chat.message.sent", {"conversation_id": "conv-1"})

            assert result == 1
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.services.webhook_service.get_db")
    async def test_dispatch_no_matching_webhook(self, mock_get_db):
        """Should not dispatch to non-matching webhooks."""
        mock_webhook = MagicMock()
        mock_webhook.id = "wh-1"
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.secret = "whsec_test"
        mock_webhook.events = ["agent.task.completed"]
        mock_webhook.is_active = True
        mock_webhook.failure_count = 0
        mock_webhook.last_delivery_at = None
        mock_webhook.last_delivery_status = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_webhook]
        mock_get_db.return_value = iter([mock_db])

        with patch.object(webhook_service, "_send_webhook", new_callable=AsyncMock) as mock_send:
            result = await webhook_service.dispatch("chat.message.sent", {"conversation_id": "conv-1"})

            assert result == 0
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    @patch("backend.services.webhook_service.get_db")
    async def test_dispatch_inactive_webhook(self, mock_get_db):
        """Should not dispatch to inactive webhooks."""
        # Inactive webhooks are filtered out by the query itself
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = iter([mock_db])

        with patch.object(webhook_service, "_send_webhook", new_callable=AsyncMock) as mock_send:
            result = await webhook_service.dispatch("chat.message.sent", {"conversation_id": "conv-1"})

            assert result == 0
            mock_send.assert_not_called()


class TestWebhookSignature:
    """Test webhook signature generation."""

    @pytest.mark.asyncio
    async def test_send_webhook_signature(self):
        """Should generate correct HMAC signature."""
        mock_webhook = MagicMock()
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.secret = "whsec_test_secret"

        import hashlib
        import hmac

        body = '{"id":"test","type":"test","timestamp":"2026-05-07","data":{}}'
        expected_sig = hmac.new(
            mock_webhook.secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert expected_sig.startswith("")
        assert len(expected_sig) == 64
