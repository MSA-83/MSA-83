"""Admin router for analytics, user management, and feature flags."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.analytics.analytics_service import AnalyticsService
from backend.services.features.flag_service import FeatureFlagService, feature_flags

router = APIRouter(prefix="/admin", tags=["admin"])

analytics_service = AnalyticsService()
flag_service = feature_flags


class AdminResponse(BaseModel):
    status: str
    data: dict | list | None = None


class FlagUpdateRequest(BaseModel):
    enabled: bool
    value: str | bool | int | float | dict | None = None
    rollout_percentage: int | None = None


@router.get("/analytics/system")
async def get_system_metrics(days: int = Query(default=30, ge=1, le=365)):
    """Get system-wide analytics metrics."""
    metrics = await analytics_service.get_system_metrics(days=days)
    return {"status": "success", "data": metrics}


@router.get("/analytics/users/{user_id}")
async def get_user_analytics(user_id: str, days: int = Query(default=30, ge=1, le=365)):
    """Get analytics for a specific user."""
    usage = await analytics_service.get_user_usage(user_id=user_id, days=days)
    return {"status": "success", "data": usage}


@router.get("/analytics/top-users")
async def get_top_users(
    limit: int = Query(default=10, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
):
    """Get users with highest activity."""
    top = await analytics_service.get_top_users(limit=limit, days=days)
    return {"status": "success", "data": top}


@router.get("/flags")
async def get_all_flags():
    """Get all feature flags."""
    return {"status": "success", "data": flag_service.get_all_flags()}


@router.get("/flags/{flag_name}")
async def get_flag(flag_name: str):
    """Get a specific feature flag."""
    flag = flag_service._flags.get(flag_name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")
    return {"status": "success", "data": flag}


@router.put("/flags/{flag_name}")
async def update_flag(flag_name: str, request: FlagUpdateRequest):
    """Update a feature flag."""
    flag = flag_service._flags.get(flag_name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")

    flag_service.set_flag(flag_name, value=request.value if request.value is not None else flag["value"], enabled=request.enabled)

    if request.rollout_percentage is not None:
        flag["rollout_percentage"] = request.rollout_percentage

    return {"status": "success", "data": flag_service._flags[flag_name]}


@router.get("/flags/stats")
async def get_flag_stats():
    """Get feature flag statistics."""
    return {"status": "success", "data": flag_service.get_stats()}
