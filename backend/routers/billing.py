"""Billing router for subscription management."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.services.billing.stripe_service import StripeService
from backend.services.cache.decorator import cached

router = APIRouter()
stripe_service = StripeService()


class CheckoutRequest(BaseModel):
    tier_id: str
    billing_cycle: str = "monthly"
    success_url: str | None = None
    cancel_url: str | None = None


class CheckoutResponse(BaseModel):
    tier_id: str
    status: str
    checkout_url: str | None = None
    message: str | None = None


@router.get("/pricing")
@cached("pricing", ttl=600)
async def get_pricing():
    """Get all pricing tiers. Cached for 10 minutes."""
    return await stripe_service.get_pricing()


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(request: CheckoutRequest):
    """Create a Stripe checkout session."""
    try:
        result = await stripe_service.create_checkout_session(
            customer_email="user@example.com",
            tier_id=request.tier_id,
            billing_cycle=request.billing_cycle,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        return CheckoutResponse(
            tier_id=result["tier_id"],
            status=result["status"],
            checkout_url=result.get("checkout_url"),
            message=result.get("message"),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def handle_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = await stripe_service.handle_webhook(payload, sig_header)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscription/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str):
    """Cancel a subscription."""
    return await stripe_service.cancel_subscription(subscription_id)


@router.get("/usage/{user_id}")
async def get_usage(user_id: str):
    """Get current usage for a user."""
    return await stripe_service.get_usage(user_id, "free")
