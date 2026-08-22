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


class AnthropicProvider(LLMProviderBase):
    """
    Anthropic Claude Adapter supporting Claude 3.5 Sonnet (Reasoning) and Claude 3.5 Haiku (Fast).
    """

    BASE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(
        self,
        api_key: str = "",
        reasoning_model: str = "claude-3-5-sonnet-20241022",
        fast_model: str = "claude-3-5-haiku-20241022",
        timeout_seconds: float = 60.0,
    ):
        self._api_key = api_key
        self.reasoning_model = reasoning_model
        self.fast_model = fast_model
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def _resolve_model(self, tier: ModelTier) -> str:
        if tier == ModelTier.REASONING:
            return self.reasoning_model
        return self.fast_model

    def _format_messages(self, messages: List[LLMMessage]) -> tuple[Optional[str], List[Dict[str, str]]]:
        system_prompt = None
        formatted = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                formatted.append({"role": role, "content": msg.content})
        return system_prompt, formatted

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status = exc.response.status_code
        err_msg = exc.response.text
        if status == 429:
            raise ProviderRateLimitError(provider="anthropic", message=err_msg, status_code=status) from exc
        if status in (401, 403):
            raise ProviderAuthError(provider="anthropic", message=err_msg, status_code=status) from exc
        raise LLMProviderError(provider="anthropic", message=err_msg, status_code=status) from exc

    async def generate_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if not self.is_configured():
            raise ProviderAuthError(provider="anthropic", message="ANTHROPIC_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        system_prompt, formatted_msgs = self._format_messages(messages)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": formatted_msgs,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.BASE_URL, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                data = response.json()

                content_blocks = data.get("content", [])
                text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                usage = data.get("usage", {})

                return LLMResponse(
                    content=text,
                    model=model,
                    provider="anthropic",
                    usage={
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                    },
                    finish_reason=data.get("stop_reason", "end_turn"),
                )
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="anthropic", message=f"Request timed out after {self.timeout_seconds}s") from e
        except Exception as e:
            raise LLMProviderError(provider="anthropic", message=str(e)) from e

    async def generate_json(
        self,
        messages: List[LLMMessage],
        json_schema: Optional[Dict[str, Any]] = None,
        tier: ModelTier = ModelTier.REASONING,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        # Prepend explicit JSON schema enforcement instruction to system message
        schema_instruction = " Respond ONLY with valid JSON conforming to the requested schema. Do not include markdown formatting or commentary."
        augmented_messages = list(messages)
        if augmented_messages and augmented_messages[0].role == MessageRole.SYSTEM:
            augmented_messages[0] = LLMMessage(
                role=MessageRole.SYSTEM,
                content=augmented_messages[0].content + schema_instruction,
            )
        else:
            augmented_messages.insert(0, LLMMessage(role=MessageRole.SYSTEM, content=schema_instruction))

        response = await self.generate_text(
            messages=augmented_messages,
            tier=tier,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.content

    async def stream_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        if not self.is_configured():
            raise ProviderAuthError(provider="anthropic", message="ANTHROPIC_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        system_prompt, formatted_msgs = self._format_messages(messages)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": formatted_msgs,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream("POST", self.BASE_URL, headers=self._get_headers(), json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        err_text = err_bytes.decode("utf-8", errors="replace")
                        if response.status_code == 429:
                            raise ProviderRateLimitError(provider="anthropic", message=err_text, status_code=429)
                        if response.status_code in (401, 403):
                            raise ProviderAuthError(provider="anthropic", message=err_text, status_code=response.status_code)
                        raise LLMProviderError(provider="anthropic", message=err_text, status_code=response.status_code)

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            try:
                                event_data = json.loads(raw_data)
                                event_type = event_data.get("type")
                                if event_type == "content_block_delta":
                                    text_delta = event_data.get("delta", {}).get("text", "")
                                    if text_delta:
                                        yield StreamChunk(text=text_delta, is_final=False, provider="anthropic")
                                elif event_type == "message_stop":
                                    yield StreamChunk(text="", is_final=True, provider="anthropic", finish_reason="end_turn")
                            except json.JSONDecodeError:
                                continue
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="anthropic", message=f"Stream timed out after {self.timeout_seconds}s") from e
