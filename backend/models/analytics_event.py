"""Analytics event model for tracking usage."""

from datetime import datetime

from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.database import Base


class AnalyticsEvent(Base):
    """Model for tracking analytics events."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
