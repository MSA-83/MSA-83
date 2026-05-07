"""Tests for the RAG pipeline."""

import pytest

from memory.chunkers.chunker import FixedSizeChunker
from memory.embeddings.embedder import EmbeddingResult
from memory.pipelines.rag_pipeline import RAGPipeline, create_rag_pipeline
from memory.stores.vector_store import InMemoryStore


class MockEmbedder:
    """Mock embedder for testing."""

    def __init__(self, dimensions: int = 5):
        self._dimensions = dimensions

    async def embed(self, text: str) -> EmbeddingResult:
        import hashlib

        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        vector = [(hash_val % (10 ** (i + 1))) / (10 ** (i + 1)) for i in range(self._dimensions)]

        return EmbeddingResult(
            vector=vector,
            model="mock",
            dimensions=self._dimensions,
            input_text=text,
            text_hash=hashlib.sha256(text.encode()).hexdigest()[:16],
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [await self.embed(t) for t in texts]

    def get_dimensions(self) -> int:
        return self._dimensions


@pytest.fixture
def pipeline():
    chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
    embedder = MockEmbedder()
    store = InMemoryStore()

    return RAGPipeline(
        chunker=chunker,
        embedder=embedder,
        vector_store=store,
    )


class TestRAGPipeline:
    @pytest.mark.asyncio
    async def test_ingest(self, pipeline):
        result = await pipeline.ingest(
            text="This is a test document about artificial intelligence and machine learning.",
            metadata={"source": "test"},
        )

        assert result.document_id is not None
        assert result.chunks_processed > 0
        assert result.chunks_stored > 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_ingest_empty(self, pipeline):
        result = await pipeline.ingest(text="")

        assert result.chunks_processed == 0
        assert result.chunks_stored == 0
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_ingest_with_metadata(self, pipeline):
        result = await pipeline.ingest(
            text="Test content with metadata.",
            metadata={"source": "test.pdf", "author": "test"},
        )

        assert result.document_id is not None

    @pytest.mark.asyncio
    async def test_retrieve(self, pipeline):
        await pipeline.ingest(
            text="Titanium is an enterprise AI platform with RAG memory and multi-agent orchestration.",
            metadata={"source": "test"},
        )

        result = await pipeline.retrieve(
            query="What is Titanium?",
            top_k=5,
        )

        assert result.query == "What is Titanium?"
        assert result.total_results >= 0

    @pytest.mark.asyncio
    async def test_retrieve_empty(self, pipeline):
        result = await pipeline.retrieve(
            query="nonexistent query",
            top_k=5,
        )

        assert result.total_results == 0
        assert result.context_text == ""

    @pytest.mark.asyncio
    async def test_retrieve_and_format(self, pipeline):
        await pipeline.ingest(
            text="The quick brown fox jumps over the lazy dog.",
            metadata={"source": "test"},
        )

        formatted = await pipeline.retrieve_and_format(
            query="What does the fox do?",
            top_k=5,
        )

        assert "Based on the following context" in formatted
        assert "What does the fox do?" in formatted

    @pytest.mark.asyncio
    async def test_delete_document(self, pipeline):
        result = await pipeline.ingest(
            text="Document to be deleted.",
            metadata={"source": "test"},
        )

        deleted = await pipeline.delete_document(result.document_id)
        assert deleted > 0

    @pytest.mark.asyncio
    async def test_get_stats(self, pipeline):
        stats = await pipeline.get_stats()

        assert "chunker" in stats
        assert "embedder" in stats
        assert "vector_store" in stats

    @pytest.mark.asyncio
    async def test_ingest_batch(self, pipeline):
        documents = [
            {"text": "First document content.", "metadata": {"source": "doc1"}},
            {"text": "Second document content.", "metadata": {"source": "doc2"}},
            {"text": "Third document content.", "metadata": {"source": "doc3"}},
        ]

        results = await pipeline.ingest_batch(documents)

        assert len(results) == 3
        assert all(r.chunks_stored > 0 for r in results)


class TestCreateRAGPipeline:
    def test_default_creation(self):
        pipeline = create_rag_pipeline()
        assert isinstance(pipeline, RAGPipeline)

    def test_custom_config(self):
        pipeline = create_rag_pipeline(
            chunker_strategy="semantic",
            embedder_provider="ollama",
            store_type="memory",
        )
        assert isinstance(pipeline, RAGPipeline)

    def test_invalid_config(self):
        with pytest.raises(ValueError):
            create_rag_pipeline(chunker_strategy="invalid")
