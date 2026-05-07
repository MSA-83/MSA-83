"""Tests for the FastAPI backend endpoints."""

import os

import pytest
from fastapi.testclient import TestClient

from backend.main import app

OLLAMA_AVAILABLE = os.getenv("OLLAMA_AVAILABLE", "false").lower() == "true"


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data

    def test_root(self, client):
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Titanium Enterprise AI Platform"
        assert data["status"] == "running"


class TestChatEndpoint:
    def test_chat_post(self, client):
        response = client.post(
            "/api/chat/",
            json={
                "message": "Hello, what can you do?",
                "use_rag": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "model" in data

    def test_chat_validation(self, client):
        response = client.post(
            "/api/chat/",
            json={},
        )

        assert response.status_code == 422


class TestMemoryEndpoint:
    def test_ingest(self, client):
        response = client.post(
            "/api/memory/ingest",
            json={
                "text": "This is test content for the memory system.",
                "source": "test",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["chunks_processed"] > 0

    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
    def test_search(self, client):
        client.post(
            "/api/memory/ingest",
            json={"text": "Titanium is an AI platform.", "source": "test"},
        )

        response = client.post(
            "/api/memory/search",
            json={"query": "AI platform", "top_k": 5},
        )

        assert response.status_code == 200

    def test_stats(self, client):
        response = client.get("/api/memory/stats")

        assert response.status_code == 200
        data = response.json()
        assert "chunker" in data or "embedder" in data


class TestAgentsEndpoint:
    def test_create_task(self, client):
        response = client.post(
            "/api/agents/task",
            json={
                "task": "Analyze this data",
                "agent_type": "general",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "completed"

    def test_invalid_agent_type(self, client):
        response = client.post(
            "/api/agents/task",
            json={
                "task": "Test task",
                "agent_type": "invalid",
            },
        )

        assert response.status_code == 500

    def test_agents_status(self, client):
        response = client.get("/api/agents/status")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data


class TestAuthEndpoint:
    def test_register(self, client):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
                "tier": "free",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login(self, client):
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )

        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_invalid(self, client):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401


class TestBillingEndpoint:
    def test_get_pricing(self, client):
        response = client.get("/api/billing/pricing")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 4

    def test_checkout_free_tier(self, client):
        response = client.post(
            "/api/billing/checkout",
            json={"tier_id": "free"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "free"
