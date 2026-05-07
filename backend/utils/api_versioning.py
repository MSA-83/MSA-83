"""API versioning utilities for Titanium platform."""

from fastapi import APIRouter

API_V1_PREFIX = "/api/v1"


def create_v1_router(**kwargs) -> APIRouter:
    """Create a router with v1 prefix.

    Usage:
        router = create_v1_router(prefix="/chat", tags=["chat"])
        # Routes will be at /api/v1/chat
    """
    prefix = kwargs.pop("prefix", "")
    full_prefix = f"{API_V1_PREFIX}{prefix}" if prefix else API_V1_PREFIX
    return APIRouter(prefix=full_prefix, **kwargs)
