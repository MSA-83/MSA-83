"""Custom OpenAPI/Swagger configuration for Titanium API."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def customize_openapi(app: FastAPI):
    """Customize the OpenAPI schema for better Swagger documentation."""

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["info"]["contact"] = {
        "name": "Titanium Support",
        "url": "https://github.com/titanium",
        "email": "support@titanium.ai",
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }

    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "https://api.titanium.ai",
            "description": "Production server",
        },
    ]

    security_scheme = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT access token",
        }
    }

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = security_scheme

    for path, methods in openapi_schema.get("paths", {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                tags = operation.get("tags", [])
                if "auth" in tags and method != "post":
                    operation.setdefault("security", [{"BearerAuth": []}])
                if "chat" in tags or "memory" in tags or "agents" in tags:
                    if method in ["post", "delete"]:
                        operation.setdefault("security", [{"BearerAuth": []}])

                if "summary" not in operation:
                    operation["summary"] = operation.get("operationId", "").replace("_", " ").title()

    tags_metadata = [
        {
            "name": "health",
            "description": "Health check and system status",
        },
        {
            "name": "auth",
            "description": "User authentication and token management",
        },
        {
            "name": "chat",
            "description": "AI chat with RAG context and streaming support",
        },
        {
            "name": "memory",
            "description": "Document ingestion, search, and RAG memory management",
        },
        {
            "name": "agents",
            "description": "Multi-agent task orchestration and status",
        },
        {
            "name": "billing",
            "description": "Subscription billing and pricing management",
        },
        {
            "name": "websocket",
            "description": "Real-time WebSocket connections for chat and agents",
        },
    ]

    openapi_schema["tags"] = tags_metadata

    app.openapi_schema = openapi_schema
    return app.openapi_schema
