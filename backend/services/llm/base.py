"""Unified LLM provider system with multi-model support and automatic fallback."""

import json
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field


@dataclass
class ModelCapability:
    """Capabilities of an LLM model."""
    name: str
    provider: str
    context_window: int = 4096
    max_output_tokens: int = 2048
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    cost_per_1m_input: float = 0.0
    cost_per_1m_output: float = 0.0
    is_free: bool = True
    description: str = ""


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    metadata: dict = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Base interface for all LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        pass

    def get_available_models(self) -> list[ModelCapability]:
        return []
