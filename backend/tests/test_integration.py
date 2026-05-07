"""Integration tests for Titanium platform."""

import os

import pytest
from fastapi.testclient import TestClient

from backend.main import app

OLLAMA_AVAILABLE = os.getenv("OLLAMA_AVAILABLE", "false").lower() == "true"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    """Register and return a user."""
    response = client.post(
        "/api/auth/register",
        json={"email": "integration@test.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(registered_user):
    """Get auth headers for authenticated requests."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


class TestFullAuthFlow:
    """Test complete authentication flow."""

    def test_register_login_logout(self, client):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "flow@test.com",
                "password": "flowpass123",
            },
        )
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        import time

        time.sleep(1.1)

        response = client.post(
            "/api/auth/login",
            json={
                "email": "flow@test.com",
                "password": "flowpass123",
            },
        )
        assert response.status_code == 200

        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200
        new_tokens = response.json()
        assert new_tokens["access_token"] != tokens["access_token"]


class TestAuthenticatedEndpoints:
    """Test endpoints with authentication."""

    def test_get_me(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "integration@test.com"

    def test_unauthorized_access(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code in [401, 403]


class TestMemoryIntegration:
    """Test memory ingestion and retrieval flow."""

    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
    def test_ingest_and_search(self, client):
        ingest_response = client.post(
            "/api/memory/ingest",
            json={
                "text": "Titanium is an enterprise AI platform with RAG memory.",
                "source": "integration_test",
                "metadata": {"test": True},
            },
        )
        assert ingest_response.status_code == 200
        ingest_data = ingest_response.json()
        assert ingest_data["document_id"] is not None

        search_response = client.post(
            "/api/memory/search",
            json={
                "query": "enterprise AI platform",
                "top_k": 5,
            },
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total_results"] >= 0

    def test_ingest_and_delete(self, client):
        ingest_response = client.post(
            "/api/memory/ingest",
            json={"text": "Temporary document for deletion test.", "source": "test"},
        )
        assert ingest_response.status_code == 200
        doc_id = ingest_response.json()["document_id"]

        delete_response = client.delete(f"/api/memory/documents/{doc_id}")
        assert delete_response.status_code == 200


class TestAgentIntegration:
    """Test agent task creation and status flow."""

    def test_create_task_and_check_status(self, client):
        response = client.post(
            "/api/agents/task",
            json={
                "task": "Analyze the security implications of JWT tokens",
                "agent_type": "security",
                "use_memory": False,
            },
        )
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["task_id"] is not None
        assert task_data["status"] in ["completed", "running"]

        status_response = client.get(f"/api/agents/task/{task_data['task_id']}")
        assert status_response.status_code == 200

    def test_agents_status(self, client):
        response = client.get("/api/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) > 0


class TestBillingIntegration:
    """Test billing and pricing flow."""

    def test_pricing_and_checkout(self, client):
        pricing_response = client.get("/api/billing/pricing")
        assert pricing_response.status_code == 200
        tiers = pricing_response.json()
        assert len(tiers) >= 4

        free_tier = next(t for t in tiers if t["id"] == "free")
        assert free_tier["price_monthly"] == 0

        checkout_response = client.post(
            "/api/billing/checkout",
            json={"tier_id": "free"},
        )
        assert checkout_response.status_code == 200
        checkout_data = checkout_response.json()
        assert checkout_data["status"] == "free"

    def test_invalid_tier_checkout(self, client):
        response = client.post(
            "/api/billing/checkout",
            json={"tier_id": "nonexistent"},
        )
        assert response.status_code in [400, 422]


class TestHealthAndMetrics:
    """Test health check and metrics endpoints."""

    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data

    def test_metrics(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text or "http_request" in response.text

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Titanium Enterprise AI Platform"


class TestChatIntegration:
    """Test chat endpoint flow."""

    def test_chat_without_rag(self, client):
        response = client.post(
            "/api/chat/",
            json={
                "message": "Hello, what is Titanium?",
                "use_rag": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["rag_context_used"] is False

    def test_chat_with_invalid_input(self, client):
        response = client.post(
            "/api/chat/",
            json={},
        )
        assert response.status_code == 422


class TestSecurityMiddleware:
    """Test security middleware functionality."""

    def test_security_headers(self, client):
        response = client.get("/api/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert "X-XSS-Protection" in response.headers

    def test_request_id_header(self, client):
        response = client.get("/api/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_gzip_compression(self, client):
        response = client.get(
            "/api/health",
            headers={"Accept-Encoding": "gzip"},
        )
        assert response.status_code == 200
