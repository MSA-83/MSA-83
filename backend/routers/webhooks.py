"""Webhooks router for managing event subscriptions."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.services.auth.auth_service import get_current_user
from backend.services.webhook_service import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class CreateWebhookRequest(BaseModel):
    url: str
    events: list[str]


@router.post("/")
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: dict = Depends(get_current_user),
):
    """Register a new webhook endpoint."""
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    if len(request.url) > 500:
        raise HTTPException(status_code=400, detail="URL too long")

    result = webhook_service.create_webhook(
        user_id=current_user["user_id"],
        url=request.url,
        events=request.events,
    )
    return result


@router.get("/")
async def list_webhooks(current_user: dict = Depends(get_current_user)):
    """List all webhooks for the current user."""
    webhooks = webhook_service.get_webhooks(current_user["user_id"])
    return {"webhooks": webhooks, "count": len(webhooks)}


@router.get("/events")
async def get_supported_events():
    """Get list of supported webhook events."""
    return {"events": webhook_service.get_supported_events()}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a webhook."""
    success = webhook_service.delete_webhook(current_user["user_id"], webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "deleted", "webhook_id": webhook_id}


@router.post("/{webhook_id}/toggle")
async def toggle_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Toggle a webhook active/inactive."""
    success = webhook_service.toggle_webhook(current_user["user_id"], webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "toggled", "webhook_id": webhook_id}
