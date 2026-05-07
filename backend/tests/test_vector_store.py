"""Tests for the vector store module."""

import pytest

from memory.stores.vector_store import (
    InMemoryStore,
    SearchResult,
    VectorDocument,
)


@pytest.fixture
def store():
    return InMemoryStore()


@pytest.fixture
def sample_document():
    return VectorDocument(
        id="test-doc-1",
        vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        text="This is a test document about AI",
        metadata={"source": "test", "category": "ai"},
    )


@pytest.fixture
def sample_documents():
    return [
        VectorDocument(
            id=f"doc-{i}",
            vector=[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i, 0.5 * i],
            text=f"Document number {i} about topic {i % 3}",
            metadata={"topic": str(i % 3)},
        )
        for i in range(1, 6)
    ]


class TestInMemoryStore:
    @pytest.mark.asyncio
    async def test_upsert(self, store, sample_document):
        doc_id = await store.upsert(sample_document)
        assert doc_id == "test-doc-1"

    @pytest.mark.asyncio
    async def test_upsert_batch(self, store, sample_documents):
        ids = await store.upsert_batch(sample_documents)
        assert len(ids) == 5

    @pytest.mark.asyncio
    async def test_get_existing(self, store, sample_document):
        await store.upsert(sample_document)
        retrieved = await store.get("test-doc-1")

        assert retrieved is not None
        assert retrieved.text == sample_document.text
        assert retrieved.metadata == sample_document.metadata

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        result = await store.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, store, sample_document):
        await store.upsert(sample_document)
        deleted = await store.delete("test-doc-1")
        assert deleted is True

        result = await store.get("test-doc-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        deleted = await store.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_search(self, store, sample_documents):
        await store.upsert_batch(sample_documents)

        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = await store.search(query_vector, top_k=3)

        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].rank == 1

    @pytest.mark.asyncio
    async def test_search_with_filter(self, store, sample_documents):
        await store.upsert_batch(sample_documents)

        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = await store.search(
            query_vector,
            top_k=5,
            filter_metadata={"topic": "1"},
        )

        assert all(r.document.metadata.get("topic") == "1" for r in results)

    @pytest.mark.asyncio
    async def test_search_empty_store(self, store):
        results = await store.search([0.1, 0.2, 0.3], top_k=5)
        assert len(results) == 0
