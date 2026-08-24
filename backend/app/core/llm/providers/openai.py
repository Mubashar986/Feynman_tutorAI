import json
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from backend.app.core.llm.base import LLMProviderBase
from backend.app.core.llm.schemas import (
    LLMMessage,
    LLMProviderError,
    LLMResponse,
    MessageRole,
    ModelTier,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    StreamChunk,
)


class OpenAIProvider(LLMProviderBase):
    """
    OpenAI & OpenRouter compatible adapter supporting GPT-4o, GPT-4o-mini, and compatible proxies.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        reasoning_model: str = "gpt-4o",
        fast_model: str = "gpt-4o-mini",
        timeout_seconds: float = 60.0,
        provider_name: str = "openai",
    ):
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.reasoning_model = reasoning_model
        self.fast_model = fast_model
        self.timeout_seconds = timeout_seconds
        self._custom_provider_name = provider_name

    @property
    def provider_name(self) -> str:
        return self._custom_provider_name

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def _resolve_model(self, tier: ModelTier) -> str:
        if tier == ModelTier.REASONING:
            return self.reasoning_model
        return self.fast_model

    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status = exc.response.status_code
        err_msg = exc.response.text
        if status == 429:
            raise ProviderRateLimitError(provider="openai", message=err_msg, status_code=status) from exc
        if status in (401, 403):
            raise ProviderAuthError(provider="openai", message=err_msg, status_code=status) from exc
        raise LLMProviderError(provider="openai", message=err_msg, status_code=status) from exc

    async def generate_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if not self.is_configured():
            raise ProviderAuthError(provider="openai", message="OPENAI_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                data = response.json()

                choice = data.get("choices", [{}])[0]
                text = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})

                return LLMResponse(
                    content=text,
                    model=model,
                    provider="openai",
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    finish_reason=choice.get("finish_reason", "stop"),
                )
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="openai", message=f"Request timed out after {self.timeout_seconds}s") from e
        except Exception as e:
            raise LLMProviderError(provider="openai", message=str(e)) from e

    async def generate_json(
        self,
        messages: List[LLMMessage],
        json_schema: Optional[Dict[str, Any]] = None,
        tier: ModelTier = ModelTier.REASONING,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        if not self.is_configured():
            raise ProviderAuthError(provider="openai", message="OPENAI_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                data = response.json()
                choice = data.get("choices", [{}])[0]
                return choice.get("message", {}).get("content", "{}")
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="openai", message=f"Request timed out after {self.timeout_seconds}s") from e
        except Exception as e:
            raise LLMProviderError(provider="openai", message=str(e)) from e

    async def stream_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        if not self.is_configured():
            raise ProviderAuthError(provider="openai", message="OPENAI_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        err_text = err_bytes.decode("utf-8", errors="replace")
                        if response.status_code == 429:
                            raise ProviderRateLimitError(provider="openai", message=err_text, status_code=429)
                        if response.status_code in (401, 403):
                            raise ProviderAuthError(provider="openai", message=err_text, status_code=response.status_code)
                        raise LLMProviderError(provider="openai", message=err_text, status_code=response.status_code)

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(raw_data)
                                choice = chunk_data.get("choices", [{}])[0]
                                delta = choice.get("delta", {})
                                text_part = delta.get("content", "")
                                finish_reason = choice.get("finish_reason")
                                is_final = finish_reason is not None
                                if text_part or is_final:
                                    yield StreamChunk(
                                        text=text_part or "",
                                        is_final=is_final,
                                        provider="openai",
                                        finish_reason=finish_reason,
                                    )
                            except json.JSONDecodeError:
                                continue
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="openai", message=f"Stream timed out after {self.timeout_seconds}s") from e
