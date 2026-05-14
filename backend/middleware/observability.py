"""Request-level observability middleware.

This middleware creates request-scoped OpenTelemetry spans, attaches stable
request metadata, and records high-value attributes without leaking secrets.
"""

from __future__ import annotations

import json
import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.security.prompt_injection_classifier import classifier
from backend.services.observability.tracing import annotate_span, hash_text, trace_async


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Attach OpenTelemetry spans and request metadata to every request."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = getattr(request.state, "request_id", None) or hash_text(str(time.time_ns()))[:12]
        request.state.request_id = request_id

        raw_body = b""
        try:
            raw_body = await request.body()
        except Exception:
            raw_body = b""

        body_text = raw_body.decode("utf-8", errors="ignore") if raw_body else ""
        report = classifier.analyze(body_text) if body_text else None

        async with trace_async(
            "http.request",
            request_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
            prompt_risk_score=report.risk_score if report else 0.0,
            prompt_max_severity=report.max_severity.value if report else "none",
        ):
            annotate_span(
                request_id=request_id,
                http_route=request.url.path,
                http_method=request.method,
                user_agent=request.headers.get("user-agent", ""),
            )

            if report and report.is_suspicious:
                annotate_span(
                    prompt_suspicious=True,
                    prompt_findings=json.dumps(
                        [
                            {
                                "category": finding.category,
                                "severity": finding.severity.value,
                                "score": finding.score,
                            }
                            for finding in report.findings
                        ],
                        separators=(",", ":"),
                    ),
                )

            response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Prompt-Risk"] = str(report.risk_score if report else 0.0)
        return response
