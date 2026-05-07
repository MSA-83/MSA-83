"""Groq LLM provider implementation."""

import json
import os
from collections.abc import AsyncGenerator

import aiohttp

from backend.services.llm.base import BaseLLMProvider, LLMResponse, ModelCapability


class GroqProvider(BaseLLMProvider):
    """Groq cloud inference provider."""

    API_URL = "https://api.groq.com/openai/v1"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "groq"

    def get_available_models(self) -> list[ModelCapability]:
        return [
            ModelCapability(
                name="llama-3.3-70b-versatile",
                provider=self.name,
                context_window=131072,
                max_output_tokens=32768,
                supports_streaming=True,
                is_free=True,
                description="Llama 3.3 70B - high quality, free tier",
            ),
            ModelCapability(
                name="llama-3.1-8b-instant",
                provider=self.name,
                context_window=131072,
                max_output_tokens=8192,
                supports_streaming=True,
                is_free=True,
                description="Llama 3.1 8B - fast, free tier",
            ),
            ModelCapability(
                name="mixtral-8x7b-32768",
                provider=self.name,
                context_window=32768,
                max_output_tokens=32768,
                supports_streaming=True,
                is_free=True,
                description="Mixtral 8x7B - balanced performance",
            ),
            ModelCapability(
                name="gemma2-9b-it",
                provider=self.name,
                context_window=8192,
                max_output_tokens=8192,
                supports_streaming=True,
                is_free=True,
                description="Google Gemma 2 9B - lightweight",
            ),
        ]

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.API_URL}/models",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
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
        model_name = model or "llama-3.1-8b-instant"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session, session.post(
            f"{self.API_URL}/chat/completions",
            headers=self._headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            data = await response.json()

        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model_name,
            provider=self.name,
            tokens_used=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        model_name = model or "llama-3.1-8b-instant"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "max_tokens": 4096,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session, session.post(
            f"{self.API_URL}/chat/completions",
            headers=self._headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()

            async for line in response.content:
                if line:
                    text = line.decode().strip()
                    if not text.startswith("data: "):
                        continue
                    data_str = text[6:]
                    if data_str == "[DONE]":
                        yield json.dumps({"done": True})
                        continue
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield json.dumps({"chunk": content})
                    except json.JSONDecodeError:
                        continue

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        model_name = model or "llama-3.1-8b-instant"

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session, session.post(
            f"{self.API_URL}/chat/completions",
            headers=self._headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            data = await response.json()

        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model_name,
            provider=self.name,
            tokens_used=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        model_name = model or "llama-3.1-8b-instant"

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session, session.post(
            f"{self.API_URL}/chat/completions",
            headers=self._headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()

            async for line in response.content:
                if line:
                    text = line.decode().strip()
                    if not text.startswith("data: "):
                        continue
                    data_str = text[6:]
                    if data_str == "[DONE]":
                        yield json.dumps({"done": True})
                        continue
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield json.dumps({"chunk": content})
                    except json.JSONDecodeError:
                        continue

    async def list_models(self) -> list[str]:
        try:
            async with aiohttp.ClientSession() as session, session.get(
                f"{self.API_URL}/models",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                return [m["id"] for m in data.get("data", []) if m.get("active")]
        except Exception:
            return []
