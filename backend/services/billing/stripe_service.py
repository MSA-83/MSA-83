"""Stripe service for billing and subscription management."""

import os
import uuid
from datetime import UTC, datetime

from backend.models.database import get_db
from backend.models.stripe_event import StripeEvent
from backend.models.subscription import Subscription
from backend.services.billing.pricing import get_all_tiers, get_tier
from backend.services.webhook_service import webhook_service

TIER_MAP = {
    "price_free": "free",
    "price_pro_monthly": "pro",
    "price_pro_yearly": "pro",
    "price_enterprise_monthly": "enterprise",
    "price_enterprise_yearly": "enterprise",
}

TIER_LIMITS = {
    "free": {"queries_per_month": 100, "documents": 10, "agents": 1, "storage_mb": 50},
    "pro": {"queries_per_month": 5000, "documents": 500, "agents": 5, "storage_mb": 2000},
    "enterprise": {"queries_per_month": -1, "documents": -1, "agents": -1, "storage_mb": -1},
}


class StripeService:
    """Service for Stripe billing operations."""

    def __init__(self, api_key: str | None = None, webhook_secret: str | None = None):
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = webhook_secret or os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self._initialized = bool(self.api_key and self.api_key != "sk_test_")

    async def create_checkout_session(
        self,
        customer_email: str,
        tier_id: str,
        billing_cycle: str = "monthly",
        success_url: str = "http://localhost:3000/billing/success",
        cancel_url: str = "http://localhost:3000/billing/cancel",
    ) -> dict:
        """Create a Stripe checkout session."""
        tier = get_tier(tier_id)
        if not tier:
            raise ValueError(f"Unknown tier: {tier_id}")

        if tier.price_monthly == 0:
            return {
                "tier_id": tier_id,
                "status": "free",
                "message": "Free tier activated",
            }

        price_id = tier.stripe_price_id if billing_cycle == "yearly" else tier.stripe_price_id

        if not self._initialized:
            return {
                "tier_id": tier_id,
                "status": "demo",
                "message": "Stripe not configured, running in demo mode",
                "checkout_url": None,
            }

        import stripe

        stripe.api_key = self.api_key

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=customer_email,
            line_items=[
                {
                    "price": price_id or f"price_{tier_id}_{billing_cycle}",
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "tier_id": tier_id,
                "billing_cycle": billing_cycle,
            },
        )

        return {
            "tier_id": tier_id,
            "status": "created",
            "checkout_url": session.url,
            "session_id": session.id,
        }

    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Handle Stripe webhook events with full event processing."""
        if not self._initialized:
            return self._handle_demo_webhook(payload)

        import stripe

        stripe.api_key = self.api_key

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        except ValueError as e:
            raise ValueError(f"Invalid payload: {e}")
        except Exception as e:
            if "SignatureVerification" in type(e).__name__:
                raise ValueError(f"Invalid signature: {e}")
            raise

        event_id = event.get("id", "")
        event_type = event.get("type", "")

        db = next(get_db())
        try:
            existing = db.query(StripeEvent).filter(StripeEvent.stripe_event_id == event_id).first()
            if existing:
                return {"status": "ignored", "reason": "duplicate", "event_id": event_id}

            stripe_event = StripeEvent(
                id=str(uuid.uuid4()),
                stripe_event_id=event_id,
                event_type=event_type,
                payload=event,
                status="received",
            )
            db.add(stripe_event)
            db.commit()

            result = await self._process_event(db, event)

            stripe_event.status = "processed"
            stripe_event.processed_at = datetime.now(UTC)
            db.commit()

            return result

        except Exception as e:
            if stripe_event.id:
                stripe_event.status = "failed"
                stripe_event.payload["error"] = str(e)
                db.commit()
            return {"status": "error", "message": str(e)}
        finally:
            db.close()

    async def _process_event(self, db, event: dict) -> dict:
        """Process a Stripe webhook event."""
        event_type = event["type"]
        data = event["data"]["object"]

        customer_id = data.get("customer")
        subscription_id = data.get("id") or data.get("subscription")
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")

        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_invoice_failed,
            "customer.subscription.trial_will_end": self._handle_trial_will_end,
            "charge.refunded": self._handle_charge_refunded,
        }

        handler = handlers.get(event_type, self._handle_unknown_event)
        result = await handler(db, data, user_id)

        if not user_id and customer_id:
            user_id = self._find_user_by_customer(db, customer_id)

        event_record = db.query(StripeEvent).filter(StripeEvent.stripe_event_id == event["id"]).first()
        if event_record:
            event_record.customer_id = customer_id
            event_record.user_id = user_id
            event_record.subscription_id = subscription_id
            event_record.invoice_id = data.get("id") if "invoice" in event_type else None

        return result

    async def _handle_checkout_completed(self, db, session: dict, user_id: str | None) -> dict:
        mode = session.get("mode", "payment")
        if mode == "subscription":
            sub_id = session.get("subscription")
            customer_email = session.get("customer_email")
            tier_id = session.get("metadata", {}).get("tier_id", "pro")

            if sub_id:
                self._update_subscription_tier(db, sub_id, tier_id, customer_email)

            await webhook_service.dispatch("user.subscription.changed", {
                "event": "checkout.completed",
                "tier_id": tier_id,
                "subscription_id": sub_id,
                "customer_email": customer_email,
            })

            return {
                "status": "success",
                "event": "checkout_completed",
                "tier_id": tier_id,
                "subscription_id": sub_id,
            }

        return {"status": "success", "event": "payment_completed"}

    async def _handle_subscription_created(self, db, sub: dict, user_id: str | None) -> dict:
        tier_id = sub.get("metadata", {}).get("tier_id", "pro")
        status = sub.get("status", "active")
        current_period_end = sub.get("current_period_end")

        if status in ("active", "trialing"):
            self._update_subscription_tier(db, sub["id"], tier_id)

            await webhook_service.dispatch("user.subscription.changed", {
                "event": "subscription.created",
                "tier_id": tier_id,
                "status": status,
                "subscription_id": sub["id"],
            })

        return {
            "status": "success",
            "event": "subscription_created",
            "tier_id": tier_id,
            "subscription_status": status,
        }

    async def _handle_subscription_updated(self, db, sub: dict, user_id: str | None) -> dict:
        status = sub.get("status", "active")
        cancel_at_period_end = sub.get("cancel_at_period_end", False)
        tier_id = sub.get("metadata", {}).get("tier_id")

        if status == "active" and tier_id:
            self._update_subscription_tier(db, sub["id"], tier_id)
        elif status == "past_due":
            self._downgrade_to_free(db, sub.get("customer"))

        await webhook_service.dispatch("user.subscription.changed", {
            "event": "subscription.updated",
            "status": status,
            "cancel_at_period_end": cancel_at_period_end,
            "subscription_id": sub["id"],
        })

        return {
            "status": "success",
            "event": "subscription_updated",
            "status_change": status,
        }

    async def _handle_subscription_deleted(self, db, sub: dict, user_id: str | None) -> dict:
        customer_id = sub.get("customer")
        self._downgrade_to_free(db, customer_id)

        await webhook_service.dispatch("user.subscription.changed", {
            "event": "subscription.deleted",
            "customer_id": customer_id,
        })

        return {
            "status": "success",
            "event": "subscription_deleted",
            "customer_id": customer_id,
        }

    async def _handle_invoice_paid(self, db, invoice: dict, user_id: str | None) -> dict:
        amount = invoice.get("amount_paid", 0)
        currency = invoice.get("currency", "usd")
        subscription_id = invoice.get("subscription")

        event_record = db.query(StripeEvent).filter(StripeEvent.stripe_event_id == invoice.get("id")).first()
        if event_record:
            event_record.amount = amount
            event_record.currency = currency

        await webhook_service.dispatch("user.subscription.changed", {
            "event": "invoice.paid",
            "amount": amount,
            "currency": currency,
            "subscription_id": subscription_id,
        })

        return {
            "status": "success",
            "event": "invoice_paid",
            "amount": amount,
            "currency": currency,
        }

    async def _handle_invoice_failed(self, db, invoice: dict, user_id: str | None) -> dict:
        amount = invoice.get("amount_due", 0)
        subscription_id = invoice.get("subscription")
        customer_id = invoice.get("customer")

        event_record = db.query(StripeEvent).filter(StripeEvent.stripe_event_id == invoice.get("id")).first()
        if event_record:
            event_record.amount = amount

        await webhook_service.dispatch("user.subscription.changed", {
            "event": "invoice.payment_failed",
            "amount": amount,
            "subscription_id": subscription_id,
            "customer_id": customer_id,
        })

        return {
            "status": "success",
            "event": "invoice_failed",
            "amount": amount,
        }

    async def _handle_trial_will_end(self, db, sub: dict, user_id: str | None) -> dict:
        trial_end = sub.get("trial_end")
        return {
            "status": "success",
            "event": "trial_will_end",
            "trial_end": trial_end,
        }

    async def _handle_charge_refunded(self, db, charge: dict, user_id: str | None) -> dict:
        amount = charge.get("amount_refunded", 0)
        return {
            "status": "success",
            "event": "charge_refunded",
            "amount": amount,
        }

    async def _handle_unknown_event(self, db, data: dict, user_id: str | None) -> dict:
        return {"status": "success", "event": "unknown", "message": "Event logged but not processed"}

    def _handle_demo_webhook(self, payload: bytes) -> dict:
        import json

        try:
            event = json.loads(payload)
            return {"status": "demo", "event": event.get("type", "unknown"), "message": "Demo mode - not processed"}
        except json.JSONDecodeError:
            return {"status": "demo", "event": "unknown", "message": "Invalid JSON payload"}

    def _find_user_by_customer(self, db, customer_id: str) -> str | None:
        sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
        return sub.user_id if sub else None

    def _update_subscription_tier(self, db, subscription_id: str, tier_id: str, email: str | None = None):
        sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == subscription_id).first()
        if sub:
            sub.tier = tier_id
            sub.is_active = True
        else:
            new_sub = Subscription(
                id=str(uuid.uuid4()),
                user_id=email or "unknown",
                stripe_subscription_id=subscription_id,
                stripe_customer_id="",
                tier=tier_id,
                is_active=True,
            )
            db.add(new_sub)
        db.commit()

    def _downgrade_to_free(self, db, customer_id: str | None):
        if not customer_id:
            return
        subs = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).all()
        for sub in subs:
            sub.tier = "free"
            sub.is_active = False
        db.commit()

    async def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a subscription."""
        if not self._initialized:
            return {"status": "demo", "message": "Subscription cancelled (demo)"}

        import stripe

        stripe.api_key = self.api_key

        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )

        return {
            "status": "success",
            "message": "Subscription will cancel at end of period",
        }

    async def get_pricing(self) -> list[dict]:
        """Get all pricing tiers."""
        tiers = get_all_tiers()
        return [
            {
                "id": tier.id,
                "name": tier.name,
                "price_monthly": tier.price_monthly / 100,
                "price_yearly": tier.price_yearly / 100,
                "description": tier.description,
                "features": tier.features,
                "limits": tier.limits,
            }
            for tier in tiers
        ]

    async def get_usage(self, user_id: str, tier_id: str) -> dict:
        """Get current usage vs limits for a user."""
        tier = get_tier(tier_id)
        if not tier:
            raise ValueError(f"Unknown tier: {tier_id}")

        return {
            "tier_id": tier_id,
            "tier_name": tier.name,
            "limits": tier.limits,
            "usage": {
                "queries_this_month": 0,
                "documents_stored": 0,
                "active_agents": 0,
            },
        }
