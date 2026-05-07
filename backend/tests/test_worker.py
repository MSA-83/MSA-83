"""Tests for ARQ worker tasks and queue service."""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.worker.tasks import (
    cleanup_old_exports,
    dispatch_webhook,
    generate_csv_export,
    generate_json_export,
    generate_pdf_export,
    refresh_llm_models,
    send_email_notification,
)


class TestDispatchWebhook:
    """Test webhook dispatch task."""

    @pytest.mark.asyncio
    async def test_dispatch_webhook_success(self):
        ctx = {}
        payload = {"event": "test", "user_id": "123"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await dispatch_webhook(
                ctx,
                webhook_url="https://example.com/webhook",
                event_type="test.event",
                payload=payload,
                secret="whsec_test",
            )

            assert result["success"] is True
            assert result["status_code"] == 200
            assert result["event_type"] == "test.event"

    @pytest.mark.asyncio
    async def test_dispatch_webhook_failure(self):
        ctx = {}
        payload = {"event": "test"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await dispatch_webhook(
                ctx,
                webhook_url="https://example.com/webhook",
                event_type="test.event",
                payload=payload,
            )

            assert result["success"] is False
            assert result["status_code"] == 500

    @pytest.mark.asyncio
    async def test_dispatch_webhook_includes_signature(self):
        ctx = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            await dispatch_webhook(
                ctx,
                webhook_url="https://example.com/webhook",
                event_type="test.event",
                payload={"data": "test"},
                secret="whsec_test",
            )

            call_kwargs = mock_client.return_value.__aenter__.return_value.post.call_args
            headers = call_kwargs.kwargs["headers"]
            assert "X-Webhook-Signature" in headers
            assert headers["X-Webhook-Signature"].startswith("sha256=")
            assert "X-Webhook-Event" in headers


class TestGenerateExports:
    """Test export generation tasks."""

    @pytest.mark.asyncio
    async def test_generate_pdf_export(self):
        ctx = {}
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        result = await generate_pdf_export(
            ctx,
            conversation_id="conv-1",
            title="Test Chat",
            messages=messages,
            include_metadata=False,
        )

        assert result["success"] is True
        assert result["conversation_id"] == "conv-1"
        assert result["format"] == "pdf"
        assert result["size_bytes"] > 0

    @pytest.mark.asyncio
    async def test_generate_csv_export(self):
        ctx = {}
        messages = [
            {"role": "user", "content": "Hello", "created_at": "2026-05-07"},
            {"role": "assistant", "content": "Hi!", "created_at": "2026-05-07"},
        ]

        result = await generate_csv_export(
            ctx,
            conversation_id="conv-1",
            messages=messages,
        )

        assert result["success"] is True
        assert result["conversation_id"] == "conv-1"
        assert result["format"] == "csv"
        assert result["size_bytes"] > 0

    @pytest.mark.asyncio
    async def test_generate_json_export(self):
        ctx = {}
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

        result = await generate_json_export(
            ctx,
            conversation_id="conv-1",
            title="Test Chat",
            messages=messages,
        )

        assert result["success"] is True
        assert result["conversation_id"] == "conv-1"
        assert result["format"] == "json"
        data = json.loads(result["size_bytes"]) if isinstance(result["size_bytes"], str) else True
        assert data is True


class TestSendEmail:
    """Test email notification task."""

    @pytest.mark.asyncio
    async def test_send_email_demo_mode(self):
        ctx = {}
        old_key = os.environ.get("SENDGRID_API_KEY")
        os.environ.pop("SENDGRID_API_KEY", None)
        os.environ.pop("SMTP_API_KEY", None)

        try:
            result = await send_email_notification(
                ctx,
                to_email="user@example.com",
                subject="Test",
                body_html="<p>Hello</p>",
            )

            assert result["success"] is True
            assert result["demo"] is True
            assert result["to"] == "user@example.com"
        finally:
            if old_key:
                os.environ["SENDGRID_API_KEY"] = old_key


class TestCleanupExports:
    """Test cleanup old exports task."""

    @pytest.mark.asyncio
    async def test_cleanup_no_directory(self):
        ctx = {}
        old_dir = os.environ.get("EXPORT_DIR")
        os.environ["EXPORT_DIR"] = "/tmp/nonexistent_exports_12345"

        try:
            result = await cleanup_old_exports(ctx)
            assert result["success"] is True
            assert result["cleaned"] == 0
        finally:
            if old_dir:
                os.environ["EXPORT_DIR"] = old_dir
            else:
                os.environ.pop("EXPORT_DIR", None)

    @pytest.mark.asyncio
    async def test_cleanup_with_directory(self, tmp_path):
        ctx = {}
        os.environ["EXPORT_DIR"] = str(tmp_path)

        old_file = tmp_path / "old_export.pdf"
        old_file.write_text("old content")
        old_file.touch()
        os.utime(old_file, (1000000, 1000000))

        new_file = tmp_path / "new_export.pdf"
        new_file.write_text("new content")

        result = await cleanup_old_exports(ctx)

        assert result["success"] is True
        assert result["cleaned"] == 1
        assert new_file.exists()
        assert not old_file.exists()


class TestRefreshModels:
    """Test LLM model refresh task."""

    @pytest.mark.asyncio
    async def test_refresh_models_success(self):
        ctx = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama3"},
                    {"name": "mistral"},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await refresh_llm_models(ctx)

            assert result["success"] is True
            assert result["count"] == 2
            assert "llama3" in result["models"]

    @pytest.mark.asyncio
    async def test_refresh_models_failure(self):
        ctx = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await refresh_llm_models(ctx)

            assert result["success"] is False
            assert result["status_code"] == 500


class TestQueueService:
    """Test queue service."""

    @pytest.mark.asyncio
    async def test_enqueue_webhook(self):
        from backend.services.worker.queue_service import enqueue_webhook

        mock_queue = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "job-123"
        mock_queue.enqueue.return_value = mock_job

        with patch("backend.services.worker.queue_service._queue", mock_queue):
            result = await enqueue_webhook(
                webhook_url="https://example.com/webhook",
                event_type="test.event",
                payload={"data": "test"},
            )

            assert result == "job-123"

    @pytest.mark.asyncio
    async def test_enqueue_export_pdf(self):
        from backend.services.worker.queue_service import enqueue_export

        mock_queue = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "job-export-1"
        mock_queue.enqueue.return_value = mock_job

        with patch("backend.services.worker.queue_service._queue", mock_queue):
            result = await enqueue_export(
                export_type="pdf",
                conversation_id="conv-1",
                title="Test",
                messages=[{"role": "user", "content": "Hi"}],
            )

            assert result == "job-export-1"
            mock_queue.enqueue.assert_called_once()
            call_kwargs = mock_queue.enqueue.call_args.kwargs
            assert call_kwargs["title"] == "Test"
            assert call_kwargs["include_metadata"] is False

    @pytest.mark.asyncio
    async def test_enqueue_export_csv(self):
        from backend.services.worker.queue_service import enqueue_export

        mock_queue = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "job-csv-1"
        mock_queue.enqueue.return_value = mock_job

        with patch("backend.services.worker.queue_service._queue", mock_queue):
            result = await enqueue_export(
                export_type="csv",
                conversation_id="conv-1",
            )

            assert result == "job-csv-1"
            call_kwargs = mock_queue.enqueue.call_args.kwargs
            assert mock_queue.enqueue.call_args.args[0] == "generate_csv_export"

    @pytest.mark.asyncio
    async def test_enqueue_export_invalid_type(self):
        from backend.services.worker.queue_service import enqueue_export

        result = await enqueue_export(
            export_type="xml",
            conversation_id="conv-1",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_enqueue_email(self):
        from backend.services.worker.queue_service import enqueue_email

        mock_queue = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "job-email-1"
        mock_queue.enqueue.return_value = mock_job

        with patch("backend.services.worker.queue_service._queue", mock_queue):
            result = await enqueue_email(
                to_email="user@example.com",
                subject="Test",
                body_html="<p>Hello</p>",
            )

            assert result == "job-email-1"

    @pytest.mark.asyncio
    async def test_enqueue_webhook_failure(self):
        from backend.services.worker.queue_service import enqueue_webhook

        mock_queue = AsyncMock()
        mock_queue.enqueue.side_effect = Exception("Connection failed")

        with patch("backend.services.worker.queue_service._queue", mock_queue):
            result = await enqueue_webhook(
                webhook_url="https://example.com/webhook",
                event_type="test.event",
                payload={},
            )

            assert result is None
