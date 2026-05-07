"""Rate limiting middleware for FastAPI."""

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.services.limiter import rate_limit_service

TESTING = os.getenv("TITANIUM_TESTING", "false").lower() == "true"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply per-tier rate limiting to all requests."""

    async def dispatch(self, request: Request, call_next):
        if TESTING:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        path = request.url.path
        if path.startswith("/metrics") or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        user_id = client_ip
        tier = "free"

        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from backend.services.auth.auth_service import auth_service

                token = auth_header.split(" ", 1)[1]
                payload = auth_service.decode_token(token)
                user_id = payload.get("sub", client_ip)
                tier = payload.get("tier", "free")
            except Exception:
                pass

        limit_check = rate_limit_service.check_rate_limit(user_id, tier, "minute")

        if not limit_check["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {limit_check['reset_in']}s",
                        "details": {
                            "limit": limit_check["limit"],
                            "remaining": 0,
                            "retry_after": limit_check["reset_in"],
                        },
                    }
                },
                headers={
                    "Retry-After": str(limit_check["reset_in"]),
                    "X-RateLimit-Limit": str(limit_check["limit"]),
                    "X-RateLimit-Remaining": "0",
                },
            )

        rate_limit_service.record_request(user_id)

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit_check["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_check["remaining"] - 1)

        return response
