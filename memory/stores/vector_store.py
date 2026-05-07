"""Vector store implementations for RAG memory system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class VectorDocument:
    """A document stored in the vector database."""

    id: str
    vector: list[float]
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """A search result from the vector store."""

    document: VectorDocument
    score: float
    rank: int


class BaseVectorStore(ABC):
    """Base vector store interface."""

    @abstractmethod
    async def upsert(self, document: VectorDocument) -> str:
        """Insert or update a document."""

    @abstractmethod
    async def upsert_batch(self, documents: list[VectorDocument]) -> list[str]:
        """Insert or update multiple documents."""

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar vectors."""

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document by ID."""

    @abstractmethod
    async def get(self, document_id: str) -> VectorDocument | None:
        """Retrieve a document by ID."""


class QdrantStore(BaseVectorStore):
    """Vector store using Qdrant (self-hosted free)."""

    def __init__(
        self,
        collection_name: str = "titanium-memory",
        host: str = "localhost",
        port: int = 6333,
        api_key: str | None = None,
        vector_size: int = 768,
    ):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.api_key = api_key
        self.vector_size = vector_size
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
            )

            collections = [c.name for c in self._client.get_collections().collections]
            if self.collection_name not in collections:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )

        return self._client

    async def upsert(self, document: VectorDocument) -> str:
        from qdrant_client import models

        client = await self._get_client()
        payload = {"text": document.text, **document.metadata}

        client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=document.id,
                    vector=document.vector,
                    payload=payload,
                )
            ],
        )

        return document.id

    async def upsert_batch(self, documents: list[VectorDocument]) -> list[str]:
        from qdrant_client import models

        client = await self._get_client()
        points = [
            models.PointStruct(
                id=doc.id,
                vector=doc.vector,
                payload={"text": doc.text, **doc.metadata},
            )
            for doc in documents
        ]

        client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return [doc.id for doc in documents]

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        from qdrant_client import models

        client = await self._get_client()

        qdrant_filter = None
        if filter_metadata:
            conditions = [models.MatchValue(key=k, value=v) for k, v in filter_metadata.items()]
            qdrant_filter = models.Filter(must=conditions)

        results = client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
        )

        return [
            SearchResult(
                document=VectorDocument(
                    id=str(r.id),
                    vector=r.vector,
                    text=r.payload.get("text", ""),
                    metadata={k: v for k, v in r.payload.items() if k != "text"},
                ),
                score=r.score,
                rank=i + 1,
            )
            for i, r in enumerate(results)
        ]

    async def delete(self, document_id: str) -> bool:
        client = await self._get_client()
        client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[document_id]),
        )
        return True

    async def get(self, document_id: str) -> VectorDocument | None:
        client = await self._get_client()
        points = client.retrieve(
            collection_name=self.collection_name,
            ids=[document_id],
            with_payload=True,
            with_vectors=True,
        )

        if not points:
            return None

        point = points[0]
        return VectorDocument(
            id=str(point.id),
            vector=point.vector,
            text=point.payload.get("text", ""),
            metadata={k: v for k, v in point.payload.items() if k != "text"},
        )


class ChromaStore(BaseVectorStore):
    """Vector store using Chroma (local, no server needed)."""

    def __init__(
        self,
        collection_name: str = "titanium-memory",
        persist_directory: str = "./chroma_db",
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._collection = None

    async def _get_collection(self):
        if self._collection is None:
            import chromadb

            client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        return self._collection

    async def upsert(self, document: VectorDocument) -> str:
        collection = await self._get_collection()
        collection.upsert(
            ids=[document.id],
            embeddings=[document.vector],
            documents=[document.text],
            metadatas=[document.metadata],
        )
        return document.id

    async def upsert_batch(self, documents: list[VectorDocument]) -> list[str]:
        collection = await self._get_collection()
        collection.upsert(
            ids=[doc.id for doc in documents],
            embeddings=[doc.vector for doc in documents],
            documents=[doc.text for doc in documents],
            metadatas=[doc.metadata for doc in documents],
        )
        return [doc.id for doc in documents]

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        collection = await self._get_collection()

        where_clause = None
        if filter_metadata:
            where_clause = {"$and": [{k: {"$eq": v}} for k, v in filter_metadata.items()]}

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        for i in range(len(results["ids"][0])):
            doc_id = results["ids"][0][i]
            distance = results["distances"][0][i] if results["distances"] else 0
            score = 1 - distance if distance else 1

            search_results.append(
                SearchResult(
                    document=VectorDocument(
                        id=doc_id,
                        vector=query_vector,
                        text=results["documents"][0][i] or "",
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    ),
                    score=score,
                    rank=i + 1,
                )
            )

        return search_results

    async def delete(self, document_id: str) -> bool:
        collection = await self._get_collection()
        collection.delete(ids=[document_id])
        return True

    async def get(self, document_id: str) -> VectorDocument | None:
        collection = await self._get_collection()
        result = collection.get(ids=[document_id], include=["documents", "metadatas", "embeddings"])

        if not result["ids"]:
            return None

        return VectorDocument(
            id=result["ids"][0],
            vector=result["embeddings"][0] if result["embeddings"] else [],
            text=result["documents"][0] or "",
            metadata=result["metadatas"][0] if result["metadatas"] else {},
        )


class InMemoryStore(BaseVectorStore):
    """In-memory vector store for testing and development."""

    def __init__(self):
        self._documents: dict[str, VectorDocument] = {}

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(a * a for a in v2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def upsert(self, document: VectorDocument) -> str:
        self._documents[document.id] = document
        return document.id

    async def upsert_batch(self, documents: list[VectorDocument]) -> list[str]:
        for doc in documents:
            self._documents[doc.id] = doc
        return [doc.id for doc in documents]

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        results = []

        for doc_id, doc in self._documents.items():
            if filter_metadata:
                match = all(doc.metadata.get(k) == v for k, v in filter_metadata.items())
                if not match:
                    continue

            score = self._cosine_similarity(query_vector, doc.vector)
            results.append(
                SearchResult(
                    document=doc,
                    score=score,
                    rank=0,
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)

        for i, result in enumerate(results[:top_k]):
            result.rank = i + 1

        return results[:top_k]

    async def delete(self, document_id: str) -> bool:
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False

    async def get(self, document_id: str) -> VectorDocument | None:
        return self._documents.get(document_id)

    def get_stats(self) -> dict:
        """Get store statistics."""
        return {
            "total_documents": len(self._documents),
        }


def create_vector_store(
    store_type: str = "memory",
    collection_name: str = "titanium-memory",
    **kwargs,
) -> BaseVectorStore:
    """Factory function to create vector stores by type."""
    stores = {
        "qdrant": lambda: QdrantStore(collection_name=collection_name, **kwargs),
        "chroma": lambda: ChromaStore(collection_name=collection_name, **kwargs),
        "memory": lambda: InMemoryStore(),
    }

    if store_type not in stores:
        raise ValueError(f"Unknown store type: {store_type}. Choose from {list(stores.keys())}")

    return stores[store_type]()
