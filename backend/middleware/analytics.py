"""Analytics middleware for tracking API usage."""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.services.analytics.analytics_service import AnalyticsService

SKIP_PATHS = ["/api/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks API usage for analytics."""

    def __init__(self, app, analytics_service: AnalyticsService | None = None):
        super().__init__(app)
        self.analytics = analytics_service or AnalyticsService()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request and track analytics."""
        path = request.url.path

        if path in SKIP_PATHS or path.startswith("/api/auth/oauth"):
            return await call_next(request)

        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        user_id = getattr(request.state, "user_id", None)
        if user_id and path.startswith("/api/"):
            event_type = "api_call"
            if "/chat" in path:
                event_type = "chat_request"
            elif "/memory" in path:
                event_type = "memory_operation"
            elif "/agents" in path:
                event_type = "agent_execution"

            try:
                await self.analytics.track_event(
                    user_id=str(user_id),
                    event_type=event_type,
                    metadata={
                        "method": request.method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                    },
                    value=duration_ms,
                )
            except Exception:
                pass

        return response
