"""Observability package for tracing and logging."""

from backend.services.observability.otel import setup_opentelemetry

__all__ = ["setup_opentelemetry"]
