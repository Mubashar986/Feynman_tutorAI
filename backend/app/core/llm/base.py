from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from backend.app.core.llm.schemas import (
    LLMMessage,
    LLMResponse,
    ModelTier,
    StreamChunk,
)


class LLMProviderBase(ABC):
    """
    Abstract base protocol for all LLM provider adapters.
    Guarantees vendor-neutral interaction for text, structured JSON, and streaming tokens.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for the provider (e.g. 'gemini', 'openai', 'anthropic', 'ollama')."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider has valid credentials / endpoint configuration."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a text response given a list of messages.
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        messages: List[LLMMessage],
        json_schema: Optional[Dict[str, Any]] = None,
        tier: ModelTier = ModelTier.REASONING,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate raw JSON string conforming to the given schema / prompt instructions.
        """
        pass

    @abstractmethod
    async def stream_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Yield incremental stream chunks as they arrive from the LLM provider.
        """
        pass
