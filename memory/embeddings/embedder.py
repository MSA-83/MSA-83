"""Embedding generation service for RAG memory system."""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    vector: list[float]
    model: str
    dimensions: int
    input_text: str
    text_hash: str


class BaseEmbedder(ABC):
    """Base embedding service interface."""

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts."""

    @abstractmethod
    def get_dimensions(self) -> int:
        """Return the embedding dimension size."""


class OllamaEmbedder(BaseEmbedder):
    """Embedding via local Ollama instance."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        dimensions: int = 768,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._dimensions = dimensions

    async def embed(self, text: str) -> EmbeddingResult:
        import aiohttp

        payload = {"model": self.model, "prompt": text}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
            ) as response,
        ):
            response.raise_for_status()
            data = await response.json()

        return EmbeddingResult(
            vector=data["embedding"],
            model=self.model,
            dimensions=len(data["embedding"]),
            input_text=text,
            text_hash=hashlib.sha256(text.encode()).hexdigest()[:16],
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [await self.embed(text) for text in texts]

    def get_dimensions(self) -> int:
        return self._dimensions


class GroqEmbedder(BaseEmbedder):
    """Embedding via Groq API (free-tier)."""

    def __init__(
        self,
        model: str = "nomic-embed-text-v1",
        api_key: str | None = None,
        dimensions: int = 768,
    ):
        self.model = model
        self.api_key = api_key
        self._dimensions = dimensions

    async def embed(self, text: str) -> EmbeddingResult:
        import aiohttp

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": text,
            "encoding_format": "float",
        }

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                "https://api.groq.com/openai/v1/embeddings",
                headers=headers,
                json=payload,
            ) as response,
        ):
            response.raise_for_status()
            data = await response.json()

        vector = data["data"][0]["embedding"]
        return EmbeddingResult(
            vector=vector,
            model=self.model,
            dimensions=len(vector),
            input_text=text,
            text_hash=hashlib.sha256(text.encode()).hexdigest()[:16],
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [await self.embed(text) for text in texts]

    def get_dimensions(self) -> int:
        return self._dimensions


class HuggingFaceEmbedder(BaseEmbedder):
    """Embedding via Hugging Face Inference API (free-tier)."""

    def __init__(
        self,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        api_key: str | None = None,
        dimensions: int = 384,
    ):
        self.model = model
        self.api_key = api_key
        self._dimensions = dimensions

    async def embed(self, text: str) -> EmbeddingResult:
        import aiohttp

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": text}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model}",
                headers=headers,
                json=payload,
            ) as response,
        ):
            response.raise_for_status()
            vector = await response.json()

        if isinstance(vector, list) and len(vector) > 0:
            if isinstance(vector[0], list):
                vector = vector[0]

        return EmbeddingResult(
            vector=vector,
            model=self.model,
            dimensions=len(vector),
            input_text=text,
            text_hash=hashlib.sha256(text.encode()).hexdigest()[:16],
        )

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        return [await self.embed(text) for text in texts]

    def get_dimensions(self) -> int:
        return self._dimensions


def create_embedder(
    provider: str = "ollama",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> BaseEmbedder:
    """Factory function to create embedders by provider name."""
    providers = {
        "ollama": lambda: OllamaEmbedder(
            model=model or "nomic-embed-text",
            base_url=base_url or "http://localhost:11434",
        ),
        "groq": lambda: GroqEmbedder(
            model=model or "nomic-embed-text-v1",
            api_key=api_key,
        ),
        "huggingface": lambda: HuggingFaceEmbedder(
            model=model or "sentence-transformers/all-MiniLM-L6-v2",
            api_key=api_key,
        ),
    }

    if provider not in providers:
        raise ValueError(f"Unknown embedding provider: {provider}. Choose from {list(providers.keys())}")

    return providers[provider]()
