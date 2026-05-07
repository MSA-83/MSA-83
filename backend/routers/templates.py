"""Conversation templates router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.services.auth.auth_service import get_current_user
from backend.services.template_service import template_service

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/")
async def list_templates(category: str | None = Query(default=None)):
    """List all conversation templates."""
    templates = template_service.get_all_templates(category=category)
    return {"templates": templates, "count": len(templates)}


@router.get("/categories")
async def get_categories():
    """Get all template categories."""
    categories = template_service.get_categories()
    return {"categories": categories}


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get a specific template."""
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/{template_id}/use")
async def use_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Use a template (increments usage count and returns template data)."""
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template_service.increment_usage(template_id)
    return template
