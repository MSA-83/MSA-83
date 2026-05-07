"""OAuth router for social login (GitHub, Google)."""

import os
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.services.oauth import oauth_provider

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class OAuthCallbackResponse(BaseModel):
    user: dict
    tokens: dict


@router.get("/{provider}")
async def oauth_authorize(
    provider: str,
    state: str | None = Query(None, description="Optional state parameter for CSRF protection"),
):
    """Redirect user to OAuth provider authorization page."""
    if provider not in oauth_provider.PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    auth_url = oauth_provider.get_auth_url(provider, state)
    return RedirectResponse(url=auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(..., description="Authorization code from provider"),
    state: str | None = Query(None, description="State parameter returned from provider"),
):
    """Handle OAuth callback and redirect to frontend with tokens."""
    if provider not in oauth_provider.PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    try:
        result = await oauth_provider.handle_callback(provider, code)
        params = {
            "access_token": result["tokens"]["access_token"],
            "refresh_token": result["tokens"]["refresh_token"],
            "token_type": result["tokens"]["token_type"],
            "user_email": result["user"].get("email", ""),
            "provider": provider,
        }
        if state:
            params["state"] = state
        redirect_url = f"{FRONTEND_URL}/auth/callback?{urlencode(params)}"
        return RedirectResponse(url=redirect_url)
    except ValueError as e:
        error_url = f"{FRONTEND_URL}/login?error={urlencode({str(e)})}"
        return RedirectResponse(url=error_url)
    except Exception as e:
        error_url = f"{FRONTEND_URL}/login?error={urlencode({'OAuth error': str(e)})}"
        return RedirectResponse(url=error_url)
