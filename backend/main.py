"""Titanium Enterprise AI Platform - FastAPI Backend."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.middleware.analytics import AnalyticsMiddleware
from backend.middleware.errors import setup_error_handlers
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.middleware.security import setup_security_middleware
from backend.routers import admin, agents, api_keys, auth, billing, chat, conversations, export, health, memory, oauth, templates, webhooks, websocket
from backend.services.analytics.analytics_service import AnalyticsService
from backend.services.openapi import customize_openapi
from backend.utils.api_versioning import API_V1_PREFIX


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    from backend.models.database import engine, init_db
    from backend.services.logging.logger import titanium_logger
    from backend.services.observability.otel import setup_opentelemetry
    from backend.services.template_service import template_service

    init_db()
    template_service.ensure_system_templates()
    setup_opentelemetry(app, engine=engine)
    titanium_logger.info("Titanium backend started", version="0.1.0")
    yield


app = FastAPI(
    title="Titanium Enterprise AI Platform",
    version="0.1.0",
    description="Autonomous AI-driven platform with RAG memory and multi-agent orchestration",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

customize_openapi(app)

setup_security_middleware(app)
setup_error_handlers(app)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AnalyticsMiddleware, analytics_service=AnalyticsService())

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to every request."""
    request.state.request_id = str(uuid.uuid4())[:12]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(oauth.router, prefix="/api/auth/oauth", tags=["oauth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(api_keys.router, tags=["api-keys"])
app.include_router(templates.router, tags=["templates"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])

app.include_router(health.router, prefix=f"{API_V1_PREFIX}", tags=["health-v1"])
app.include_router(admin.router, prefix=f"{API_V1_PREFIX}", tags=["admin-v1"])
app.include_router(auth.router, prefix=f"{API_V1_PREFIX}/auth", tags=["auth-v1"])
app.include_router(oauth.router, prefix=f"{API_V1_PREFIX}/auth/oauth", tags=["oauth-v1"])
app.include_router(chat.router, prefix=f"{API_V1_PREFIX}/chat", tags=["chat-v1"])
app.include_router(memory.router, prefix=f"{API_V1_PREFIX}/memory", tags=["memory-v1"])
app.include_router(agents.router, prefix=f"{API_V1_PREFIX}/agents", tags=["agents-v1"])
app.include_router(billing.router, prefix=f"{API_V1_PREFIX}/billing", tags=["billing-v1"])
app.include_router(conversations.router, prefix=f"{API_V1_PREFIX}/conversations", tags=["conversations-v1"])
app.include_router(export.router, prefix=f"{API_V1_PREFIX}/export", tags=["export-v1"])
app.include_router(webhooks.router, prefix=f"{API_V1_PREFIX}", tags=["webhooks-v1"])


@app.get("/")
async def root():
    return {
        "name": "Titanium Enterprise AI Platform",
        "version": "0.1.0",
        "status": "running",
        "api_versions": ["v1"],
        "docs": "/docs",
        "api_v1": "/api/v1",
    }


@app.get("/api/version")
async def get_api_version():
    """Get API version information."""
    return {
        "current": "v1",
        "available": ["v1"],
        "deprecated": [],
        "base_url_v1": "/api/v1",
    }
