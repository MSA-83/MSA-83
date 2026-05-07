"""OpenAI LLM provider implementation."""

import json
import os
from collections.abc import AsyncGenerator

import aiohttp

from backend.services.llm.base import BaseLLMProvider, LLMResponse, ModelCapability


class OpenAIProvider(BaseLLMProvider):
    """OpenAI cloud inference provider."""

    API_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", self.API_URL)).rstrip("/")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "openai"

    def get_available_models(self) -> list[ModelCapability]:
        return [
            ModelCapability(
                name="gpt-4o-mini",
                provider=self.name,
                context_window=128000,
                max_output_tokens=16384,
                supports_streaming=True,
                supports_function_calling=True,
                supports_vision=True,
                cost_per_1m_input=0.15,
                cost_per_1m_output=0.60,
                description="GPT-4o Mini - fast, affordable",
            ),
            ModelCapability(
                name="gpt-4o",
                provider=self.name,
                context_window=128000,
                max_output_tokens=16384,
                supports_streaming=True,
                supports_function_calling=True,
                supports_vision=True,
                cost_per_1m_input=2.50,
                cost_per_1m_output=10.0,
                description="GPT-4o - flagship multimodal",
            ),
            ModelCapability(
                name="gpt-3.5-turbo",
                provider=self.name,
                context_window=16385,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_function_calling=True,
                cost_per_1m_input=0.50,
                cost_per_1m_output=1.50,
                description="GPT-3.5 Turbo - fast, cost-effective",
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
                f"{self.base_url}/models",
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
        model_name = model or "gpt-4o-mini"

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
            f"{self.base_url}/chat/completions",
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
        model_name = model or "gpt-4o-mini"

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
            f"{self.base_url}/chat/completions",
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
        model_name = model or "gpt-4o-mini"

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session, session.post(
            f"{self.base_url}/chat/completions",
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
        model_name = model or "gpt-4o-mini"

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session, session.post(
            f"{self.base_url}/chat/completions",
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
                f"{self.base_url}/models",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception:
            return []
