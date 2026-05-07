"""Centralized API error handling middleware."""

from datetime import datetime

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class TitaniumError(Exception):
    """Base error for Titanium platform."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(TitaniumError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, 401, "AUTH_REQUIRED")


class AuthorizationError(TitaniumError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, 403, "INSUFFICIENT_PERMISSIONS")


class NotFoundError(TitaniumError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", 404, "NOT_FOUND")


class ValidationError(TitaniumError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 422, "VALIDATION_ERROR", details)


class RateLimitError(TitaniumError):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after}s",
            429,
            "RATE_LIMIT_EXCEEDED",
            {"retry_after": retry_after},
        )


class ServiceUnavailableError(TitaniumError):
    def __init__(self, service: str = "Service"):
        super().__init__(f"{service} is temporarily unavailable", 503, "SERVICE_UNAVAILABLE")


async def titanium_exception_handler(request: Request, exc: TitaniumError):
    """Handle Titanium custom errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None),
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
        headers={"X-Error-Code": exc.error_code},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors},
                "request_id": getattr(request.state, "request_id", None),
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    error_id = getattr(request.state, "request_id", "unknown")

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error_id": error_id},
                "request_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


def setup_error_handlers(app):
    """Register all error handlers with the FastAPI app."""
    app.add_exception_handler(TitaniumError, titanium_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
