import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional

from backend.app.core.llm.base import LLMProviderBase
from backend.app.core.llm.schemas import (
    LLMMessage,
    LLMResponse,
    ModelTier,
    ProviderAuthError,
    ProviderRateLimitError,
    StreamChunk,
)


class MockLLMProvider(LLMProviderBase):
    """
    Deterministic in-memory mock provider for offline development and fast CI unit tests.
    Supports simulated errors (e.g. rate limits) to verify gateway fallback routing.
    """

    def __init__(
        self,
        name: str = "mock",
        default_text: str = "This is a mock response from MockLLMProvider.",
        default_json: Optional[Dict[str, Any]] = None,
        simulate_rate_limit: bool = False,
        simulate_auth_error: bool = False,
        delay_seconds: float = 0.0,
    ):
        self._name = name
        self.default_text = default_text
        self.default_json = default_json or {"status": "ok", "message": "mock structured output"}
        self.simulate_rate_limit = simulate_rate_limit
        self.simulate_auth_error = simulate_auth_error
        self.delay_seconds = delay_seconds
        self.calls_count = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def is_configured(self) -> bool:
        return True

    def _check_simulated_errors(self) -> None:
        self.calls_count += 1
        if self.simulate_rate_limit:
            raise ProviderRateLimitError(
                provider=self._name,
                message="Simulated HTTP 429: Too Many Requests / Quota Exceeded",
                status_code=429,
            )
        if self.simulate_auth_error:
            raise ProviderAuthError(
                provider=self._name,
                message="Simulated HTTP 401: Invalid API key",
                status_code=401,
            )

    async def generate_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        self._check_simulated_errors()

        user_content = messages[-1].content if messages else ""
        return LLMResponse(
            content=f"{self.default_text} (Prompt: {user_content[:40]}...)",
            model=f"mock-{tier.value}-model",
            provider=self._name,
            usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
            finish_reason="stop",
        )

    async def generate_json(
        self,
        messages: List[LLMMessage],
        json_schema: Optional[Dict[str, Any]] = None,
        tier: ModelTier = ModelTier.REASONING,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        self._check_simulated_errors()

        return json.dumps(self.default_json)

    async def stream_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        self._check_simulated_errors()

        tokens = ["This ", "is ", "a ", "mock ", "streaming ", "dialogue ", "token."]
        for i, token in enumerate(tokens):
            is_final = (i == len(tokens) - 1)
            yield StreamChunk(
                text=token,
                is_final=is_final,
                provider=self._name,
                finish_reason="stop" if is_final else None,
            )
