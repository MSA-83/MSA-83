"""Authentication router for user registration, login, and token management."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.services.auth.auth_service import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    auth_service,
    get_current_user,
)
from backend.services.limiter import rate_limit_service

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user and return tokens."""
    user = auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        tier=user_data.tier,
    )

    tokens = auth_service.login(user_data.email, user_data.password)

    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Authenticate a user and return tokens."""
    return auth_service.login(
        email=user_data.email,
        password=user_data.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh an access token."""
    return auth_service.refresh_access_token(request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    user = auth_service.get_user(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout (client should discard tokens)."""
    return {"message": "Logged out successfully. Discard your tokens."}


@router.get("/rate-limit")
async def get_rate_limit_status(current_user: dict = Depends(get_current_user)):
    """Get current rate limit status for the authenticated user."""
    user_id = current_user["user_id"]
    tier = current_user.get("tier", "free")

    stats = rate_limit_service.get_usage_stats(user_id, tier)

    return {
        "tier": tier,
        "limits": stats["limits"],
        "usage": stats["usage"],
        "utilization": {
            "minute_pct": round((stats["usage"]["requests_this_minute"] / max(stats["limits"]["requests_per_minute"], 1)) * 100, 1) if stats["limits"]["requests_per_minute"] != -1 else 0,
            "hour_pct": round((stats["usage"]["requests_this_hour"] / max(stats["limits"]["requests_per_hour"], 1)) * 100, 1) if stats["limits"]["requests_per_hour"] != -1 else 0,
            "day_pct": round((stats["usage"]["requests_today"] / max(stats["limits"]["requests_per_day"], 1)) * 100, 1) if stats["limits"]["requests_per_day"] != -1 else 0,
        },
    }
