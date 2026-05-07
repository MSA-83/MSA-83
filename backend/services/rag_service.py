"""RAG service for document management and retrieval."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from memory.pipelines.rag_pipeline import create_rag_pipeline


class RAGService:
    """High-level RAG service for the backend."""

    def __init__(self):
        self.pipeline = create_rag_pipeline(
            chunker_strategy="fixed",
            embedder_provider=os.getenv("EMBEDDER_PROVIDER", "ollama"),
            store_type=os.getenv("VECTOR_STORE", "memory"),
        )

    async def ingest(
        self,
        text: str,
        source: str | None = None,
        metadata: dict | None = None,
        chunker_strategy: str = "fixed",
    ) -> dict:
        """Ingest text into the memory system."""
        meta = metadata or {}
        if source:
            meta["source"] = source

        result = await self.pipeline.ingest(text=text, metadata=meta)

        return {
            "document_id": result.document_id,
            "chunks_processed": result.chunks_processed,
            "chunks_stored": result.chunks_stored,
            "errors": result.errors,
        }

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        filter_metadata: dict | None = None,
    ) -> dict | None:
        """Retrieve relevant context for a query."""
        result = await self.pipeline.retrieve(
            query=query,
            top_k=top_k,
            min_score=min_score,
            filter_metadata=filter_metadata,
        )

        if not result.chunks:
            return None

        return {
            "context_text": result.context_text,
            "chunks": result.chunks,
            "total_results": result.total_results,
        }

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[dict]:
        """Search the memory system."""
        result = await self.pipeline.retrieve(
            query=query,
            top_k=top_k,
            min_score=min_score,
        )

        return result.chunks

    async def delete_document(self, document_id: str) -> int:
        """Delete a document from memory."""
        return await self.pipeline.delete_document(document_id)

    async def get_stats(self) -> dict:
        """Get RAG system statistics."""
        return await self.pipeline.get_stats()
