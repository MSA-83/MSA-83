"""Stripe service for billing and subscription management."""

import os

from backend.services.billing.pricing import get_all_tiers, get_tier


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
        """Handle Stripe webhook events."""
        if not self._initialized:
            return {"status": "demo", "event": "none"}

        import stripe

        stripe.api_key = self.api_key

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)

            event_type = event["type"]

            if event_type == "checkout.session.completed":
                session = event["data"]["object"]
                return {
                    "status": "success",
                    "event": "checkout_completed",
                    "customer_email": session.get("customer_email"),
                    "tier_id": session.get("metadata", {}).get("tier_id"),
                }

            elif event_type == "customer.subscription.deleted":
                subscription = event["data"]["object"]
                return {
                    "status": "success",
                    "event": "subscription_cancelled",
                    "customer_id": subscription.get("customer"),
                }

            elif event_type == "invoice.payment_failed":
                invoice = event["data"]["object"]
                return {
                    "status": "success",
                    "event": "payment_failed",
                    "customer_id": invoice.get("customer"),
                }

            return {"status": "success", "event": event_type}

        except ValueError as e:
            raise ValueError(f"Invalid payload: {e}")
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid signature: {e}")

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
