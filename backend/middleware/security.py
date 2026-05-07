"""Security middleware for the backend."""

import re
import time

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class PromptInjectionMiddleware(BaseHTTPMiddleware):
    """Detect and block potential prompt injection attacks."""

    INJECTION_PATTERNS = [
        re.compile(r"(?i)ignore\s+(previous|all|above)\s+(instruction|prompt|rule)"),
        re.compile(r"(?i)system:\s*"),
        re.compile(r"(?i)<\|.*?\|>"),
        re.compile(r"(?i)\\x[0-9a-fA-F]{2}"),
        re.compile(r"(?i)\b(new\s+role|act\s+as|pretend\s+to)\b"),
        re.compile(r"(?i)\b(disregard|forget)\s+(all\s+)?(previous|prior)\b"),
    ]

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and "/chat" in request.url.path:
            body = await request.body()

            try:
                import json

                body_str = body.decode()
                data = json.loads(body_str)

                message = data.get("message", "")
                if isinstance(message, str) and self._check_injection(message):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Potentially harmful input detected",
                            "code": "PROMPT_INJECTION_BLOCKED",
                        },
                    )

            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        response = await call_next(request)
        return response

    def _check_injection(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in self.INJECTION_PATTERNS)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit trail."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(id(request))

        return response


def setup_security_middleware(app: FastAPI):
    """Configure security-focused middleware."""
    allowed_hosts = ["*"]

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(PromptInjectionMiddleware)
