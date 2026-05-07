"""Admin RBAC dependencies for protecting admin endpoints."""

from fastapi import Depends, HTTPException, status

from backend.services.auth.auth_service import get_current_user

TIER_LEVELS = {"free": 0, "pro": 1, "enterprise": 2, "defense": 3}


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require enterprise or defense tier to access admin endpoints."""
    user_tier = current_user.get("tier", "free")

    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS["enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access requires enterprise tier or higher",
        )

    return current_user


async def require_superuser(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require defense tier for superuser operations."""
    user_tier = current_user.get("tier", "free")

    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS["defense"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires defense tier access",
        )

    return current_user
