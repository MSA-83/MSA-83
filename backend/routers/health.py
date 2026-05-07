"""Health check router with dependency monitoring."""

import os
import time

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

TESTING = os.getenv("TITANIUM_TESTING", "false").lower() == "true"


class ComponentHealth(BaseModel):
    status: str
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    uptime_seconds: float
    components: dict[str, ComponentHealth]


class DependencyStatus(BaseModel):
    name: str
    status: str
    details: dict


_start_time = time.time()


async def check_ollama() -> ComponentHealth:
    """Check Ollama inference service."""
    import aiohttp

    start = time.time()
    try:
        async with aiohttp.ClientSession() as session, session.get(
            "http://localhost:11434/api/tags",
            timeout=aiohttp.ClientTimeout(total=3),
        ) as response:
            latency = (time.time() - start) * 1000
            if response.status == 200:
                data = await response.json()
                models = [m["name"] for m in data.get("models", [])]
                return ComponentHealth(
                    status="healthy",
                    latency_ms=round(latency, 1),
                )
            return ComponentHealth(
                status="degraded",
                latency_ms=round(latency, 1),
                error=f"Status {response.status}",
            )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            status="unhealthy",
            latency_ms=round(latency, 1),
            error=str(e),
        )


async def check_redis() -> ComponentHealth:
    """Check Redis cache service."""
    start = time.time()
    try:
        import redis.asyncio as redis

        client = redis.from_url("redis://localhost:6379/0", socket_timeout=2)
        await client.ping()
        await client.close()
        latency = (time.time() - start) * 1000
        return ComponentHealth(status="healthy", latency_ms=round(latency, 1))
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            status="unhealthy",
            latency_ms=round(latency, 1),
            error=str(e),
        )


async def check_qdrant() -> ComponentHealth:
    """Check Qdrant vector store."""
    import aiohttp

    start = time.time()
    try:
        async with aiohttp.ClientSession() as session, session.get(
            "http://localhost:6333/",
            timeout=aiohttp.ClientTimeout(total=3),
        ) as response:
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                status="healthy" if response.status == 200 else "degraded",
                latency_ms=round(latency, 1),
            )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            status="unhealthy",
            latency_ms=round(latency, 1),
            error=str(e),
        )


async def check_database() -> ComponentHealth:
    """Check database connectivity."""
    start = time.time()
    try:
        from backend.models.database import engine

        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return ComponentHealth(status="healthy", latency_ms=round(latency, 1))
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            status="unhealthy",
            latency_ms=round(latency, 1),
            error=str(e),
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check with dependency monitoring."""
    ollama = await check_ollama()
    redis_check = await check_redis()
    qdrant = await check_qdrant()
    database = await check_database()

    components = {
        "api": ComponentHealth(status="healthy"),
        "database": database,
        "ollama": ollama,
        "redis": redis_check,
        "qdrant": qdrant,
    }

    unhealthy = sum(1 for c in components.values() if c.status == "unhealthy")

    if TESTING:
        overall = "healthy"
    else:
        critical_unhealthy = sum(
            1 for name, c in components.items() if c.status == "unhealthy" and name in ("api", "database")
        )
        overall = "unhealthy" if critical_unhealthy > 0 else "healthy"

    return HealthResponse(
        status=overall,
        version="0.1.0",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        uptime_seconds=round(time.time() - _start_time, 1),
        components={k: v for k, v in components.items()},
    )


@router.get("/health/dependencies")
async def dependency_status():
    """Detailed dependency status report."""
    ollama = await check_ollama()
    redis_check = await check_redis()
    qdrant = await check_qdrant()
    database = await check_database()

    return {
        "ollama": {"status": ollama.status, "latency_ms": ollama.latency_ms, "error": ollama.error},
        "redis": {"status": redis_check.status, "latency_ms": redis_check.latency_ms, "error": redis_check.error},
        "qdrant": {"status": qdrant.status, "latency_ms": qdrant.latency_ms, "error": qdrant.error},
        "database": {"status": database.status, "latency_ms": database.latency_ms, "error": database.error},
    }
