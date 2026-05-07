"""API keys router for programmatic access management."""

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel

from backend.services.auth.api_key_service import api_key_service, require_api_key
from backend.services.auth.auth_service import get_current_user

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class CreateApiKeyRequest(BaseModel):
    name: str
    expires_days: int | None = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key: str | None = None
    prefix: str
    is_active: bool | None = None
    expires_at: str | None = None
    created_at: str | None = None
    last_used_at: str | None = None


@router.post("/", response_model=ApiKeyResponse)
async def create_api_key(
    request: CreateApiKeyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new API key. Key is only shown once."""
    if len(request.name) > 100:
        raise HTTPException(status_code=400, detail="Name must be under 100 characters")

    result = api_key_service.create_key(
        user_id=current_user["user_id"],
        name=request.name,
        expires_days=request.expires_days,
    )

    return result


@router.get("/")
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """List all API keys for the current user (without secret values)."""
    keys = api_key_service.get_user_keys(current_user["user_id"])
    return {"keys": keys, "count": len(keys)}


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke an API key."""
    success = api_key_service.revoke_key(current_user["user_id"], key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked", "key_id": key_id}


@router.get("/me")
async def get_api_key_user(info: dict = Depends(require_api_key)):
    """Get user info for the authenticated API key."""
    return {
        "user_id": info["user_id"],
        "key_name": info["key_name"],
    }
