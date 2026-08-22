import json
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from backend.app.core.llm.base import LLMProviderBase
from backend.app.core.llm.schemas import (
    LLMMessage,
    LLMProviderError,
    LLMResponse,
    ModelTier,
    ProviderTimeoutError,
    StreamChunk,
)


class OllamaProvider(LLMProviderBase):
    """
    Local Ollama Adapter for offline local execution (e.g. Llama 3.1, Qwen 2.5).
    Guarantees zero-network local execution and zero developer cloud costs.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        reasoning_model: str = "llama3.1:8b",
        fast_model: str = "llama3.1:8b",
        timeout_seconds: float = 90.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.reasoning_model = reasoning_model
        self.fast_model = fast_model
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _resolve_model(self, tier: ModelTier) -> str:
        if tier == ModelTier.REASONING:
            return self.reasoning_model
        return self.fast_model

    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    async def generate_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.LOCAL,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        model = self._resolve_model(tier)
        url = f"{self.base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                content = data.get("message", {}).get("content", "")
                return LLMResponse(
                    content=content,
                    model=model,
                    provider="ollama",
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    },
                    finish_reason="stop" if data.get("done") else None,
                )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise LLMProviderError(provider="ollama", message=f"Failed to connect to Ollama daemon at {self.base_url}: {str(e)}") from e
        except httpx.ReadTimeout as e:
            raise ProviderTimeoutError(provider="ollama", message=f"Ollama generation timed out after {self.timeout_seconds}s") from e
        except Exception as e:
            raise LLMProviderError(provider="ollama", message=str(e)) from e

    async def generate_json(
        self,
        messages: List[LLMMessage],
        json_schema: Optional[Dict[str, Any]] = None,
        tier: ModelTier = ModelTier.LOCAL,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        model = self._resolve_model(tier)
        url = f"{self.base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "{}")
        except Exception as e:
            raise LLMProviderError(provider="ollama", message=str(e)) from e

    async def stream_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.LOCAL,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        model = self._resolve_model(tier)
        url = f"{self.base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": True,
            "options": {"temperature": temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        raise LLMProviderError(provider="ollama", message=err_bytes.decode("utf-8"), status_code=response.status_code)

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk_data = json.loads(line)
                            content = chunk_data.get("message", {}).get("content", "")
                            done = chunk_data.get("done", False)
                            if content or done:
                                yield StreamChunk(
                                    text=content,
                                    is_final=done,
                                    provider="ollama",
                                    finish_reason="stop" if done else None,
                                )
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise LLMProviderError(provider="ollama", message=str(e)) from e
