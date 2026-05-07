"""Webhook model for event notifications."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.database import Base


class Webhook(Base):
    """User-configured webhook endpoints."""

    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    events: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_delivery_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    failure_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
