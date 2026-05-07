"""Tests for export service."""

import json

from backend.services.export import CSVExporter, JSONExporter, MarkdownExporter


class TestMarkdownExporter:
    """Test Markdown export."""

    def test_export_conversation_basic(self):
        """Should export conversation as Markdown."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = MarkdownExporter.export_conversation("Test Chat", messages)
        assert "# Test Chat" in result
        assert "## You" in result
        assert "## Titanium" in result
        assert "Hello" in result
        assert "Hi there!" in result

    def test_export_conversation_with_metadata(self):
        """Should include metadata when requested."""
        messages = [
            {"role": "user", "content": "Hello", "created_at": "2026-05-07T10:00:00Z"},
        ]
        result = MarkdownExporter.export_conversation("Test", messages, include_metadata=True)
        assert "2026-05-07T10:00:00Z" in result

    def test_export_conversation_without_metadata(self):
        """Should not include metadata by default."""
        messages = [
            {"role": "user", "content": "Hello", "created_at": "2026-05-07T10:00:00Z"},
        ]
        result = MarkdownExporter.export_conversation("Test", messages)
        assert "2026-05-07T10:00:00Z" not in result

    def test_export_conversation_empty(self):
        """Should handle empty conversation."""
        result = MarkdownExporter.export_conversation("Empty", [])
        assert "# Empty" in result

    def test_export_conversation_unknown_role(self):
        """Should handle unknown roles."""
        messages = [{"role": "system", "content": "System message"}]
        result = MarkdownExporter.export_conversation("Test", messages)
        assert "## System" in result

    def test_export_memory_chunks(self):
        """Should export memory chunks."""
        chunks = [
            {"text": "Chunk 1 content", "metadata": {"source": "doc1", "document_id": "id1"}},
            {"text": "Chunk 2 content", "metadata": {"source": "doc2"}},
        ]
        result = MarkdownExporter.export_memory_chunks(chunks)
        assert "# Memory Export" in result
        assert "Total chunks: 2" in result
        assert "## Chunk 1" in result
        assert "**Source:** doc1" in result
        assert "Chunk 1 content" in result
        assert "Chunk 2 content" in result

    def test_export_memory_chunks_no_metadata(self):
        """Should handle chunks without metadata."""
        chunks = [{"text": "Just text"}]
        result = MarkdownExporter.export_memory_chunks(chunks)
        assert "Chunk 1" in result
        assert "Just text" in result

    def test_export_memory_chunks_empty(self):
        """Should handle empty chunks."""
        result = MarkdownExporter.export_memory_chunks([])
        assert "Total chunks: 0" in result


class TestJSONExporter:
    """Test JSON export."""

    def test_export_conversation(self):
        """Should export conversation as valid JSON."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        result = JSONExporter.export_conversation("conv-1", "Test", messages)
        data = json.loads(result)
        assert data["conversation_id"] == "conv-1"
        assert data["title"] == "Test"
        assert data["message_count"] == 2
        assert len(data["messages"]) == 2

    def test_export_usage_report(self):
        """Should export usage as valid JSON."""
        usage = {"total_queries": 100, "tokens_used": 5000}
        result = JSONExporter.export_usage_report("user-1", usage)
        data = json.loads(result)
        assert data["user_id"] == "user-1"
        assert data["usage"]["total_queries"] == 100

    def test_export_conversation_unicode(self):
        """Should handle Unicode content."""
        messages = [{"role": "user", "content": "Hello 世界"}]
        result = JSONExporter.export_conversation("conv-1", "Test", messages)
        data = json.loads(result)
        assert "世界" in data["messages"][0]["content"]


class TestCSVExporter:
    """Test CSV export."""

    def test_export_conversation(self):
        """Should export conversation as CSV."""
        messages = [
            {"role": "user", "content": "Hello", "created_at": "2026-05-07"},
            {"role": "assistant", "content": "Hi!", "created_at": "2026-05-08"},
        ]
        result = CSVExporter.export_conversation(messages)
        lines = result.split("\n")
        assert lines[0] == "role,content,created_at"
        assert len(lines) == 3

    def test_export_conversation_escapes_quotes(self):
        """Should escape quotes in CSV."""
        messages = [{"role": "user", "content": 'He said "hello"', "created_at": "2026-05-07"}]
        result = CSVExporter.export_conversation(messages)
        assert '""' in result

    def test_export_conversation_escapes_newlines(self):
        """Should escape newlines in CSV."""
        messages = [{"role": "user", "content": "Line 1\nLine 2", "created_at": "2026-05-07"}]
        result = CSVExporter.export_conversation(messages)
        assert "\\n" in result

    def test_export_conversation_empty(self):
        """Should export header only for empty conversation."""
        result = CSVExporter.export_conversation([])
        assert result == "role,content,created_at"
