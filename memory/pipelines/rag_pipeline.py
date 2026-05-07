"""RAG pipeline for document ingestion and retrieval."""

import uuid
from dataclasses import dataclass

from memory.chunkers.chunker import BaseChunker, create_chunker
from memory.embeddings.embedder import BaseEmbedder, create_embedder
from memory.stores.vector_store import BaseVectorStore, create_vector_store


@dataclass
class IngestionResult:
    """Result of document ingestion."""

    document_id: str
    chunks_processed: int
    chunks_stored: int
    errors: list[str]


@dataclass
class RetrievalResult:
    """Result of context retrieval."""

    query: str
    chunks: list[dict]
    total_results: int
    context_text: str


class RAGPipeline:
    """Main RAG pipeline connecting chunking, embedding, and vector storage."""

    def __init__(
        self,
        chunker: BaseChunker | None = None,
        embedder: BaseEmbedder | None = None,
        vector_store: BaseVectorStore | None = None,
    ):
        self.chunker = chunker or create_chunker(strategy="fixed")
        self.embedder = embedder or create_embedder(provider="ollama")
        self.vector_store = vector_store or create_vector_store(store_type="memory")

    async def ingest(
        self,
        text: str,
        metadata: dict | None = None,
        document_id: str | None = None,
    ) -> IngestionResult:
        """Ingest a document into the vector store."""
        doc_id = document_id or f"doc-{uuid.uuid4().hex[:12]}"
        errors = []

        chunks = self.chunker.chunk(text, metadata)

        if not chunks:
            return IngestionResult(
                document_id=doc_id,
                chunks_processed=0,
                chunks_stored=0,
                errors=["No chunks generated from input text"],
            )

        stored_count = 0

        for i, chunk in enumerate(chunks):
            chunk.chunk_id = f"{doc_id}-chunk-{i}"
            chunk.metadata["document_id"] = doc_id
            chunk.metadata["chunk_index"] = i
            chunk.metadata["source"] = metadata.get("source", "") if metadata else ""

            try:
                embedding = await self.embedder.embed(chunk.text)
                chunk.token_count = embedding.dimensions

                from memory.stores.vector_store import VectorDocument

                doc = VectorDocument(
                    id=chunk.chunk_id,
                    vector=embedding.vector,
                    text=chunk.text,
                    metadata={
                        **chunk.metadata,
                        "text_hash": embedding.text_hash,
                        "model": embedding.model,
                    },
                )

                await self.vector_store.upsert(doc)
                stored_count += 1

            except Exception as e:
                errors.append(f"Chunk {i} failed: {str(e)}")

        return IngestionResult(
            document_id=doc_id,
            chunks_processed=len(chunks),
            chunks_stored=stored_count,
            errors=errors,
        )

    async def ingest_batch(
        self,
        documents: list[dict],
    ) -> list[IngestionResult]:
        """Ingest multiple documents."""
        results = []

        for doc in documents:
            result = await self.ingest(
                text=doc["text"],
                metadata=doc.get("metadata"),
                document_id=doc.get("document_id"),
            )
            results.append(result)

        return results

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict | None = None,
        min_score: float = 0.0,
    ) -> RetrievalResult:
        """Retrieve relevant context for a query."""
        embedding = await self.embedder.embed(query)

        results = await self.vector_store.search(
            query_vector=embedding.vector,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        filtered_results = [r for r in results if r.score >= min_score]

        chunks = []
        context_parts = []

        for result in filtered_results:
            chunk_info = {
                "id": result.document.id,
                "text": result.document.text,
                "score": result.score,
                "rank": result.rank,
                "metadata": result.document.metadata,
            }
            chunks.append(chunk_info)
            context_parts.append(f"[{result.rank}] (score: {result.score:.3f})\n{result.document.text}")

        context_text = "\n\n---\n\n".join(context_parts)

        return RetrievalResult(
            query=query,
            chunks=chunks,
            total_results=len(filtered_results),
            context_text=context_text,
        )

    async def retrieve_and_format(
        self,
        query: str,
        top_k: int = 5,
        template: str | None = None,
        **kwargs,
    ) -> str:
        """Retrieve context and format it for LLM prompting."""
        result = await self.retrieve(query, top_k=top_k, **kwargs)

        if template:
            return template.format(
                query=query,
                context=result.context_text,
                num_chunks=result.total_results,
            )

        return (
            f"Based on the following context, answer the query.\n\n"
            f"Query: {query}\n\n"
            f"Context ({result.total_results} relevant passages):\n\n"
            f"{result.context_text}\n\n"
            f"Answer:"
        )

    async def delete_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a document."""
        deleted = 0

        results = await self.vector_store.search(
            query_vector=[0.0] * self.embedder.get_dimensions(),
            top_k=10000,
            filter_metadata={"document_id": document_id},
        )

        for result in results:
            await self.vector_store.delete(result.document.id)
            deleted += 1

        return deleted

    async def get_stats(self) -> dict:
        """Get pipeline statistics."""
        return {
            "chunker": self.chunker.__class__.__name__,
            "embedder": self.embedder.__class__.__name__,
            "vector_store": self.vector_store.__class__.__name__,
            "embedder_dimensions": self.embedder.get_dimensions(),
        }


def create_rag_pipeline(
    chunker_strategy: str = "fixed",
    embedder_provider: str = "ollama",
    store_type: str = "memory",
    **kwargs,
) -> RAGPipeline:
    """Factory function to create a fully configured RAG pipeline."""
    chunker = create_chunker(strategy=chunker_strategy)
    embedder = create_embedder(provider=embedder_provider, **kwargs)
    vector_store = create_vector_store(store_type=store_type, **kwargs)

    return RAGPipeline(
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )
