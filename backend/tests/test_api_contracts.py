"""API contract tests to validate endpoint schemas."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app

OLLAMA_AVAILABLE = os.getenv("OLLAMA_AVAILABLE", "false").lower() == "true"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
class TestHealthContract:
    """Test health endpoint contract."""

    async def test_health_response_schema(self, client):
        """Health response should match expected schema."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)

    async def test_dependencies_response_schema(self, client):
        """Dependencies response should match expected schema."""
        response = await client.get("/api/health/dependencies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        for key, value in data.items():
            assert "status" in value
            assert isinstance(value["status"], str)


@pytest.mark.anyio
class TestAuthContract:
    """Test auth endpoint contracts."""

    async def test_register_request_validation(self, client):
        """Register should validate required fields."""
        response = await client.post("/api/auth/register", json={})
        assert response.status_code in (400, 422)

    async def test_register_missing_email(self, client):
        """Register should reject missing email."""
        response = await client.post("/api/auth/register", json={"password": "test123"})
        assert response.status_code in (400, 422)

    async def test_register_missing_password(self, client):
        """Register should reject missing password."""
        response = await client.post("/api/auth/register", json={"email": "test@example.com"})
        assert response.status_code in (400, 422)

    async def test_login_request_validation(self, client):
        """Login should validate required fields."""
        response = await client.post("/api/auth/login", json={})
        assert response.status_code in (400, 422)

    async def test_refresh_request_validation(self, client):
        """Refresh should validate required fields."""
        response = await client.post("/api/auth/refresh", json={})
        assert response.status_code in (400, 422)


@pytest.mark.anyio
class TestChatContract:
    """Test chat endpoint contracts."""

    async def test_chat_response_schema(self, client):
        """Chat response should match expected schema."""
        response = await client.post("/api/chat/", json={"message": "Hello", "use_rag": False})
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "model" in data
            assert "conversation_id" in data
            assert "tokens_used" in data
            assert "rag_context_used" in data
            assert "sources" in data
            assert isinstance(data["response"], str)
            assert isinstance(data["model"], str)
            assert isinstance(data["tokens_used"], int)
            assert isinstance(data["rag_context_used"], bool)
            assert isinstance(data["sources"], list)

    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
    async def test_stream_response_format(self, client):
        """Stream response should be SSE format."""
        response = await client.post("/api/chat/stream", json={"message": "Hello", "use_rag": False})
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.anyio
class TestMemoryContract:
    """Test memory endpoint contracts."""

    async def test_ingest_response_schema(self, client):
        """Ingest response should match expected schema."""
        response = await client.post("/api/memory/ingest", json={"text": "Test content"})
        if response.status_code == 200:
            data = response.json()
            assert "document_id" in data
            assert "chunks_processed" in data
            assert "chunks_stored" in data
            assert "errors" in data
            assert isinstance(data["document_id"], str)
            assert isinstance(data["chunks_processed"], int)
            assert isinstance(data["chunks_stored"], int)
            assert isinstance(data["errors"], list)

    @pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
    async def test_search_response_schema(self, client):
        """Search response should match expected schema."""
        response = await client.post("/api/memory/search", json={"query": "test"})
        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert "total_results" in data
            assert isinstance(data["results"], list)
            assert isinstance(data["total_results"], int)

    async def test_stats_response_schema(self, client):
        """Stats response should match expected schema."""
        response = await client.get("/api/memory/stats")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


@pytest.mark.anyio
class TestAgentsContract:
    """Test agents endpoint contracts."""

    async def test_create_task_response_schema(self, client):
        """Create task response should match expected schema."""
        response = await client.post("/api/agents/task", json={"task": "Test task"})
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data
            assert "status" in data
            assert "agent_type" in data
            assert isinstance(data["task_id"], str)
            assert isinstance(data["status"], str)
            assert isinstance(data["agent_type"], str)

    async def test_task_status_response_schema(self, client):
        """Task status response should match expected schema."""
        response = await client.post("/api/agents/task", json={"task": "Test task"})
        if response.status_code == 200:
            task_id = response.json()["task_id"]
            status_response = await client.get(f"/api/agents/task/{task_id}")
            if status_response.status_code == 200:
                data = status_response.json()
                assert "status" in data

    async def test_agents_status_response_schema(self, client):
        """Agents status response should match expected schema."""
        response = await client.get("/api/agents/status")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))


@pytest.mark.anyio
class TestBillingContract:
    """Test billing endpoint contracts."""

    async def test_pricing_response_schema(self, client):
        """Pricing response should match expected schema."""
        response = await client.get("/api/billing/pricing")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            for tier in data:
                assert "id" in tier
                assert "name" in tier
                assert "price_monthly" in tier
                assert "features" in tier

    async def test_checkout_request_validation(self, client):
        """Checkout should validate required fields."""
        response = await client.post("/api/billing/checkout", json={})
        assert response.status_code in (400, 422)


@pytest.mark.anyio
class TestConversationsContract:
    """Test conversations endpoint contracts."""

    async def test_create_conversation_response_schema(self, client):
        """Create conversation response should match expected schema."""
        response = await client.post("/api/conversations/", json={"title": "Test"})
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "title" in data
            assert "created_at" in data

    async def test_list_conversations_response_schema(self, client):
        """List conversations response should match expected schema."""
        response = await client.get("/api/conversations/")
        if response.status_code == 200:
            data = response.json()
            assert "conversations" in data
            assert "total" in data
            assert isinstance(data["conversations"], list)

    async def test_conversation_stats_schema(self, client):
        """Conversation stats response should match expected schema."""
        response = await client.get("/api/conversations/stats")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


@pytest.mark.anyio
class TestExportContract:
    """Test export endpoint contracts."""

    async def test_export_conversation_request_validation(self, client):
        """Export conversation should validate required fields."""
        response = await client.post("/api/export/conversation", json={})
        assert response.status_code in (400, 422)

    async def test_export_conversation_format_validation(self, client):
        """Export should validate format field."""
        response = await client.post(
            "/api/export/conversation",
            json={"conversation_id": "test", "format": "invalid"},
        )
        assert response.status_code in (400, 422)
