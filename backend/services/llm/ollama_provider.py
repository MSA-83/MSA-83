"""Ollama LLM provider implementation."""

import json
import os
from collections.abc import AsyncGenerator

import aiohttp

from backend.services.llm.base import BaseLLMProvider, LLMResponse, ModelCapability


class OllamaProvider(BaseLLMProvider):
    """Ollama local inference provider."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "ollama"

    def get_available_models(self) -> list[ModelCapability]:
        return [
            ModelCapability(
                name="llama3",
                provider=self.name,
                context_window=8192,
                max_output_tokens=4096,
                supports_streaming=True,
                is_free=True,
                description="Meta Llama 3 - general purpose",
            ),
            ModelCapability(
                name="mistral",
                provider=self.name,
                context_window=8192,
                max_output_tokens=4096,
                supports_streaming=True,
                is_free=True,
                description="Mistral 7B - efficient general purpose",
            ),
            ModelCapability(
                name="codellama",
                provider=self.name,
                context_window=16384,
                max_output_tokens=4096,
                supports_streaming=True,
                is_free=True,
                description="Code Llama - code generation",
            ),
            ModelCapability(
                name="phi3",
                provider=self.name,
                context_window=4096,
                max_output_tokens=2048,
                supports_streaming=True,
                is_free=True,
                description="Microsoft Phi-3 - lightweight",
            ),
        ]

    async def is_available(self) -> bool:
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

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        model_name = model or "llama3"

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

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

        return LLMResponse(
            content=data.get("response", ""),
            model=model_name,
            provider=self.name,
            tokens_used=data.get("eval_count", 0),
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        model_name = model or "llama3"

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

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
                    try:
                        data = json.loads(line.decode())
                        if "response" in data:
                            yield json.dumps({"chunk": data["response"]})
                    except json.JSONDecodeError:
                        continue

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        model_name = model or "llama3"

        payload = {
            "model": model_name,
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
            data = await response.json()

        content = ""
        if "message" in data:
            content = data["message"].get("content", "")
        elif "response" in data:
            content = data["response"]

        return LLMResponse(
            content=content,
            model=model_name,
            provider=self.name,
            tokens_used=data.get("eval_count", 0),
        )

    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        model_name = model or "llama3"

        payload = {
            "model": model_name,
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

    async def list_models(self) -> list[str]:
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response,
            ):
                if response.status != 200:
                    return []
                data = await response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
