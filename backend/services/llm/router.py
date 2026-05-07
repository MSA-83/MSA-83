"""LLM router with automatic fallback and model registry."""

import json
import logging
from collections.abc import AsyncGenerator

from backend.services.llm.base import BaseLLMProvider, LLMResponse, ModelCapability
from backend.services.llm.groq_provider import GroqProvider
from backend.services.llm.ollama_provider import OllamaProvider
from backend.services.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes requests to available LLM providers with automatic fallback."""

    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {}
        self.fallback_order: list[str] = []
        self._availability_cache: dict[str, bool] = {}
        self._initialized = False

    def register_provider(
        self,
        provider: BaseLLMProvider,
        priority: int = 0,
        is_fallback: bool = False,
    ):
        """Register an LLM provider."""
        self.providers[provider.name] = provider
        if is_fallback:
            self.fallback_order.append(provider.name)
        self._availability_cache[provider.name] = None

    def _resolve_model_provider(self, model: str) -> BaseLLMProvider | None:
        """Find which provider owns a given model."""
        for provider in self.providers.values():
            for capability in provider.get_available_models():
                if capability.name == model:
                    return provider

        provider_prefix = model.split("/")[0] if "/" in model else ""
        if provider_prefix in self.providers:
            return self.providers[provider_prefix]

        return None

    async def _check_availability(self, provider_name: str) -> bool:
        if provider_name not in self.providers:
            return False
        if self._availability_cache.get(provider_name) is not None:
            return self._availability_cache[provider_name]

        provider = self.providers[provider_name]
        available = await provider.is_available()
        self._availability_cache[provider_name] = available
        return available

    async def get_available_providers(self) -> list[str]:
        """Get list of available provider names."""
        available = []
        for name in self.providers:
            if await self._check_availability(name):
                available.append(name)
        return available

    def get_all_models(self) -> list[ModelCapability]:
        """Get all registered models across providers."""
        models = []
        for provider in self.providers.values():
            models.extend(provider.get_available_models())
        return models

    def get_model_info(self, model: str) -> ModelCapability | None:
        """Get capability info for a specific model."""
        for provider in self.providers.values():
            for capability in provider.get_available_models():
                if capability.name == model:
                    return capability
        return None

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a response, falling back through providers if needed."""
        model_name = model or self._get_default_model()

        target_provider = self._resolve_model_provider(model_name)
        if target_provider:
            if await target_provider.is_available():
                return await target_provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            logger.warning(f"Provider {target_provider.name} unavailable for model {model_name}")

        for fallback_name in self.fallback_order:
            provider = self.providers.get(fallback_name)
            if not provider or not await provider.is_available():
                continue

            fallback_model = provider.get_available_models()[0].name if provider.get_available_models() else None
            if fallback_model:
                logger.info(f"Falling back to {fallback_name}/{fallback_model}")
                return await provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=fallback_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

        raise RuntimeError("No LLM providers available")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a response, falling back through providers if needed."""
        model_name = model or self._get_default_model()

        target_provider = self._resolve_model_provider(model_name)
        if target_provider and await target_provider.is_available():
            async for chunk in target_provider.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model_name,
                temperature=temperature,
            ):
                yield chunk
            return

        for fallback_name in self.fallback_order:
            provider = self.providers.get(fallback_name)
            if not provider or not await provider.is_available():
                continue

            fallback_model = provider.get_available_models()[0].name if provider.get_available_models() else None
            if fallback_model:
                async for chunk in provider.generate_stream(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=fallback_model,
                    temperature=temperature,
                ):
                    yield chunk
                return

        yield json.dumps({"error": "No LLM providers available"})

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Chat completion with fallback."""
        model_name = model or self._get_default_model()

        target_provider = self._resolve_model_provider(model_name)
        if target_provider and await target_provider.is_available():
            return await target_provider.chat(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        for fallback_name in self.fallback_order:
            provider = self.providers.get(fallback_name)
            if not provider or not await provider.is_available():
                continue

            fallback_model = provider.get_available_models()[0].name if provider.get_available_models() else None
            if fallback_model:
                return await provider.chat(
                    messages=messages,
                    model=fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

        raise RuntimeError("No LLM providers available")

    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion with fallback."""
        model_name = model or self._get_default_model()

        target_provider = self._resolve_model_provider(model_name)
        if target_provider and await target_provider.is_available():
            async for chunk in target_provider.chat_stream(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk
            return

        for fallback_name in self.fallback_order:
            provider = self.providers.get(fallback_name)
            if not provider or not await provider.is_available():
                continue

            fallback_model = provider.get_available_models()[0].name if provider.get_available_models() else None
            if fallback_model:
                async for chunk in provider.chat_stream(
                    messages=messages,
                    model=fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yield chunk
                return

        yield json.dumps({"error": "No LLM providers available"})

    def _get_default_model(self) -> str:
        if "groq" in self.providers:
            return "llama-3.1-8b-instant"
        if "ollama" in self.providers:
            return "llama3"
        if "openai" in self.providers:
            return "gpt-4o-mini"
        return "llama3"


llm_router = LLMRouter()

ollama = OllamaProvider()
groq = GroqProvider()
openai = OpenAIProvider()

llm_router.register_provider(ollama, priority=0, is_fallback=True)
llm_router.register_provider(groq, priority=1, is_fallback=False)
llm_router.register_provider(openai, priority=2, is_fallback=False)
