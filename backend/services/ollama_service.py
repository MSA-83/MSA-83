"""Ollama inference service."""

from collections.abc import AsyncGenerator

import aiohttp


class OllamaService:
    """Service for interacting with Ollama API."""

    def __init__(
        self,
        base_url: str | None = None,
        default_model: str = "llama3",
        timeout: int = 120,
    ):
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.default_model = default_model
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        context: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """Generate a completion from Ollama."""
        model_name = model or self.default_model

        system_prompt = (
            "You are Titanium, an enterprise AI assistant. "
            "Provide accurate, concise, and helpful responses. "
            "If you don't know the answer, say so clearly."
        )

        if context:
            system_prompt += (
                "\n\nUse the following context to inform your response. "
                "If the context doesn't contain relevant information, "
                "rely on your general knowledge but mention the context was insufficient.\n\n"
                f"Context:\n{context}"
            )

        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response,
        ):
            response.raise_for_status()
            data = await response.json()

        return {
            "response": data.get("response", ""),
            "model": data.get("model", model_name),
            "tokens_used": data.get("eval_count", 0),
        }

    async def generate_stream(
        self,
        prompt: str,
        context: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from Ollama."""
        model_name = model or self.default_model

        system_prompt = (
            "You are Titanium, an enterprise AI assistant. Provide accurate, concise, and helpful responses."
        )

        if context:
            system_prompt += f"\n\nUse the following context:\n\nContext:\n{context}"

        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response,
        ):
            response.raise_for_status()

            async for line in response.content:
                if line:
                    import json

                    try:
                        data = json.loads(line.decode())
                        if "response" in data:
                            yield json.dumps({"chunk": data["response"]})
                    except json.JSONDecodeError:
                        continue

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        async with aiohttp.ClientSession() as session, session.get(f"{self.base_url}/api/tags") as response:
            response.raise_for_status()
            data = await response.json()

        return [m["name"] for m in data.get("models", [])]

    async def pull_model(self, model: str) -> dict:
        """Pull a new model."""
        payload = {"model": model, "stream": False}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=600),
            ) as response,
        ):
            response.raise_for_status()
            return await response.json()

    async def chat_stream(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat-style completion from Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response,
        ):
            response.raise_for_status()

            async for line in response.content:
                if line:
                    try:
                        data = json.loads(line.decode())
                        if "message" in data:
                            content = data["message"].get("content", "")
                            if content:
                                yield json.dumps({"chunk": content})
                        if data.get("done", False):
                            yield json.dumps({"done": True, "total_duration": data.get("total_duration", 0)})
                    except json.JSONDecodeError:
                        continue

    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response,
            ):
                return response.status == 200
        except Exception:
            return False

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict:
        """Chat-style completion using Ollama chat API."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response,
        ):
            response.raise_for_status()
            return await response.json()


ollama_service = OllamaService()
