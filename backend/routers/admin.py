"""Admin router for analytics and user management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.services.analytics.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin", tags=["admin"])

analytics_service = AnalyticsService()


class AdminResponse(BaseModel):
    status: str
    data: dict | list | None = None


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
