"""Stripe webhook event logging model."""

from datetime import datetime

from sqlalchemy import DateTime, JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.database import Base


class StripeEvent(Base):
    """Log of all Stripe webhook events for audit and replay."""

    __tablename__ = "stripe_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    stripe_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="received")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
