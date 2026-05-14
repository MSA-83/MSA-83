"""Tracing helpers for Titanium / MSA-83.

This module provides small, reusable OpenTelemetry helpers that can be used by
FastAPI handlers, LangGraph orchestration nodes, and LLM provider adapters.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from hashlib import sha256
from typing import Any, AsyncIterator, Callable, Iterable

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

TRACER_NAME = "titanium-platform"


def get_tracer(name: str = TRACER_NAME):
    """Return a tracer for the given component name."""
    return trace.get_tracer(name)


def hash_text(value: str | None) -> str:
    """Hash sensitive text so spans can correlate without leaking content."""
    return sha256((value or "").encode("utf-8")).hexdigest()


def annotate_span(**attributes: Any) -> None:
    """Attach attributes to the currently active span if one exists."""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


@contextmanager
def trace_sync(name: str, **attributes: Any):
    """Context manager for synchronous traced sections."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:  # pragma: no cover - traced in runtime
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


@asynccontextmanager
async def trace_async(name: str, **attributes: Any) -> AsyncIterator[Span]:
    """Context manager for asynchronous traced sections."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:  # pragma: no cover - traced in runtime
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def traced_async(name: str, attr_builder: Callable[..., dict[str, Any]] | None = None):
    """Decorator for traced async functions.

    Args:
        name: Span name.
        attr_builder: Optional callable returning span attributes from args.
    """

    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attrs = attr_builder(*args, **kwargs) if attr_builder else {}
            async with trace_async(name, **attrs):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def set_list_attribute(key: str, values: Iterable[Any]) -> None:
    """Attach a comma-joined list attribute to the current span."""
    annotate_span(**{key: ",".join(str(v) for v in values)})
