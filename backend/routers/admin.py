"""Admin router for analytics, user management, and feature flags."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from backend.security.admin_rbac import require_admin, require_superuser
from backend.services.analytics.analytics_service import AnalyticsService
from backend.services.audit.audit_service import AuditService
from backend.services.features.flag_service import FeatureFlagService, feature_flags

router = APIRouter(prefix="/admin", tags=["admin"])

analytics_service = AnalyticsService()
flag_service = feature_flags
audit_service = AuditService()


class AdminResponse(BaseModel):
    status: str
    data: dict | list | None = None


class FlagUpdateRequest(BaseModel):
    enabled: bool
    value: str | bool | int | float | dict | None = None
    rollout_percentage: int | None = None


@router.get("/analytics/system")
async def get_system_metrics(
    days: int = Query(default=30, ge=1, le=365),
    admin: dict = Depends(require_admin),
):
    """Get system-wide analytics metrics. Requires enterprise+ tier."""
    metrics = await analytics_service.get_system_metrics(days=days)
    return {"status": "success", "data": metrics}


@router.get("/analytics/users/{user_id}")
async def get_user_analytics(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    admin: dict = Depends(require_admin),
):
    """Get analytics for a specific user. Requires enterprise+ tier."""
    usage = await analytics_service.get_user_usage(user_id=user_id, days=days)
    return {"status": "success", "data": usage}


@router.get("/analytics/top-users")
async def get_top_users(
    limit: int = Query(default=10, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
    admin: dict = Depends(require_admin),
):
    """Get users with highest activity. Requires enterprise+ tier."""
    top = await analytics_service.get_top_users(limit=limit, days=days)
    return {"status": "success", "data": top}


@router.get("/flags")
async def get_all_flags(admin: dict = Depends(require_admin)):
    """Get all feature flags. Requires enterprise+ tier."""
    return {"status": "success", "data": flag_service.get_all_flags()}


@router.get("/flags/{flag_name}")
async def get_flag(
    flag_name: str,
    admin: dict = Depends(require_admin),
):
    """Get a specific feature flag. Requires enterprise+ tier."""
    flag = flag_service._flags.get(flag_name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")
    return {"status": "success", "data": flag}


@router.put("/flags/{flag_name}")
async def update_flag(
    flag_name: str,
    request: FlagUpdateRequest,
    superuser: dict = Depends(require_superuser),
):
    """Update a feature flag. Requires defense tier."""
    flag = flag_service._flags.get(flag_name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")

    old_value = {"enabled": flag["enabled"], "value": flag["value"]}

    flag_service.set_flag(
        flag_name,
        value=request.value if request.value is not None else flag["value"],
        enabled=request.enabled,
    )

    if request.rollout_percentage is not None:
        flag["rollout_percentage"] = request.rollout_percentage

    await audit_service.log(
        user_id=superuser["user_id"],
        action="flag_updated",
        resource_type="feature_flag",
        resource_id=flag_name,
        details={
            "old": old_value,
            "new": {"enabled": request.enabled, "value": request.value},
        },
    )

    return {"status": "success", "data": flag_service._flags[flag_name]}


@router.get("/flags/stats")
async def get_flag_stats(admin: dict = Depends(require_admin)):
    """Get feature flag statistics. Requires enterprise+ tier."""
    return {"status": "success", "data": flag_service.get_stats()}


@router.get("/audit/logs")
async def get_audit_logs(
    user_id: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=1000),
    admin: dict = Depends(require_admin),
):
    """Query audit logs. Requires enterprise+ tier."""
    logs = await audit_service.get_logs(
        user_id=user_id,
        resource_type=resource_type,
        days=days,
        limit=limit,
    )
    return {"status": "success", "data": logs}


@router.get("/audit/stats")
async def get_audit_stats(
    days: int = Query(default=30, ge=1, le=365),
    admin: dict = Depends(require_admin),
):
    """Get audit log statistics. Requires enterprise+ tier."""
    stats = await audit_service.get_stats(days=days)
    return {"status": "success", "data": stats}
