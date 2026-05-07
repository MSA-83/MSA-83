"""Tests for Stripe webhook handling."""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.billing.stripe_service import StripeService


class TestStripeWebhookDemo:
    """Test webhook handling in demo mode."""

    def test_demo_webhook_checkout(self):
        service = StripeService(api_key="", webhook_secret="")
        payload = json.dumps({"type": "checkout.session.completed", "id": "evt_demo"}).encode()
        result = asyncio.get_event_loop().run_until_complete(service.handle_webhook(payload, ""))
        assert result["status"] == "demo"
        assert result["event"] == "checkout.session.completed"

    def test_demo_webhook_invalid_json(self):
        service = StripeService(api_key="", webhook_secret="")
        result = asyncio.get_event_loop().run_until_complete(service.handle_webhook(b"not json", ""))
        assert result["status"] == "demo"
        assert result["event"] == "unknown"


class TestStripeWebhookLive:
    """Test webhook handling with real Stripe (mocked)."""

    def _run_async(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def test_checkout_session_completed(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "mode": "subscription",
                    "subscription": "sub_abc123",
                    "customer_email": "test@example.com",
                    "metadata": {"tier_id": "pro", "user_id": "user-1"},
                }
            },
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_webhook = MagicMock()
        mock_webhook.dispatch = AsyncMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch("backend.services.billing.stripe_service.webhook_service", mock_webhook):
                with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                    result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "success"
        assert result["event"] == "checkout_completed"
        assert result["tier_id"] == "pro"

    def test_subscription_deleted(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_456",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "customer": "cus_123",
                    "id": "sub_abc123",
                    "metadata": {"user_id": "user-1"},
                }
            },
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_webhook = MagicMock()
        mock_webhook.dispatch = AsyncMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch("backend.services.billing.stripe_service.webhook_service", mock_webhook):
                with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                    result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "success"
        assert result["event"] == "subscription_deleted"

    def test_invoice_paid(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_789",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "amount_paid": 2900,
                    "currency": "usd",
                    "subscription": "sub_abc123",
                    "customer": "cus_123",
                    "metadata": {"user_id": "user-1"},
                }
            },
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_webhook = MagicMock()
        mock_webhook.dispatch = AsyncMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch("backend.services.billing.stripe_service.webhook_service", mock_webhook):
                with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                    result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "success"
        assert result["event"] == "invoice_paid"
        assert result["amount"] == 2900

    def test_subscription_created(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_create",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_new",
                    "status": "active",
                    "metadata": {"tier_id": "enterprise", "user_id": "user-2"},
                }
            },
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_webhook = MagicMock()
        mock_webhook.dispatch = AsyncMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch("backend.services.billing.stripe_service.webhook_service", mock_webhook):
                with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                    result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "success"
        assert result["tier_id"] == "enterprise"

    def test_duplicate_event_ignored(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_dup",
            "type": "invoice.paid",
            "data": {"object": {}},
        }

        existing_event = MagicMock()
        existing_event.id = "existing"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_event

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "ignored"
        assert result["reason"] == "duplicate"

    def test_invalid_signature_raises(self):
        import stripe
        from stripe._error import SignatureVerificationError
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        mock_db = MagicMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch.object(
                stripe.Webhook,
                "construct_event",
                side_effect=SignatureVerificationError("Bad sig", "sig"),
            ):
                with pytest.raises(ValueError, match="Invalid signature"):
                    self._run_async(service.handle_webhook(b"payload", "bad_sig"))

    def test_invoice_payment_failed(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_fail",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "amount_due": 2900,
                    "subscription": "sub_abc123",
                    "customer": "cus_123",
                }
            },
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_webhook = MagicMock()
        mock_webhook.dispatch = AsyncMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch("backend.services.billing.stripe_service.webhook_service", mock_webhook):
                with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                    result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "success"
        assert result["event"] == "invoice_failed"
        assert result["amount"] == 2900

    def test_subscription_updated(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_update",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_abc123",
                    "status": "active",
                    "cancel_at_period_end": False,
                    "metadata": {"tier_id": "pro", "user_id": "user-1"},
                }
            },
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_webhook = MagicMock()
        mock_webhook.dispatch = AsyncMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch("backend.services.billing.stripe_service.webhook_service", mock_webhook):
                with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                    result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "success"
        assert result["event"] == "subscription_updated"

    def test_trial_will_end(self):
        import stripe
        service = StripeService(api_key="sk_test_real_key", webhook_secret="whsec_test")

        event_data = {
            "id": "evt_trial",
            "type": "customer.subscription.trial_will_end",
            "data": {
                "object": {
                    "trial_end": 1715000000,
                    "metadata": {"user_id": "user-1"},
                }
            },
        }

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_webhook = MagicMock()
        mock_webhook.dispatch = AsyncMock()

        with patch("backend.services.billing.stripe_service.get_db", return_value=iter([mock_db])):
            with patch("backend.services.billing.stripe_service.webhook_service", mock_webhook):
                with patch.object(stripe.Webhook, "construct_event", return_value=event_data):
                    result = self._run_async(service.handle_webhook(b"payload", "sig_header"))

        assert result["status"] == "success"
        assert result["event"] == "trial_will_end"
