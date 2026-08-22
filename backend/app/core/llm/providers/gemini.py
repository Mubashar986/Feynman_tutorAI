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


class GeminiProvider(LLMProviderBase):
    """
    Google Gemini Adapter for Gemini 1.5 Pro (Reasoning) and Gemini 1.5 Flash (Interactive/Fast).
    Communicates via Google AI Studio REST and Server-Sent Events (SSE) streaming API.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: str = "",
        reasoning_model: str = "gemini-1.5-pro",
        fast_model: str = "gemini-1.5-flash",
        timeout_seconds: float = 60.0,
    ):
        self._api_key = api_key
        self.reasoning_model = reasoning_model
        self.fast_model = fast_model
        self.timeout_seconds = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "gemini"

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def _resolve_model(self, tier: ModelTier) -> str:
        if tier == ModelTier.REASONING:
            return self.reasoning_model
        return self.fast_model

    def _format_contents(self, messages: List[LLMMessage]) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        system_instruction = None
        contents = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = {"parts": [{"text": msg.content}]}
            elif msg.role == MessageRole.USER:
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == MessageRole.ASSISTANT:
                contents.append({"role": "model", "parts": [{"text": msg.content}]})

        return system_instruction, contents

    def _handle_http_error(self, exc: httpx.HTTPStatusError) -> None:
        status = exc.response.status_code
        err_msg = exc.response.text
        if status == 429:
            raise ProviderRateLimitError(provider="gemini", message=err_msg, status_code=status) from exc
        if status in (401, 403):
            raise ProviderAuthError(provider="gemini", message=err_msg, status_code=status) from exc
        raise LLMProviderError(provider="gemini", message=err_msg, status_code=status) from exc

    async def generate_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if not self.is_configured():
            raise ProviderAuthError(provider="gemini", message="GEMINI_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        url = f"{self.BASE_URL}/{model}:generateContent?key={self._api_key}"
        system_instruction, contents = self._format_contents(messages)

        generation_config: Dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                candidate = data.get("candidates", [{}])[0]
                text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                usage_meta = data.get("usageMetadata", {})

                return LLMResponse(
                    content=text,
                    model=model,
                    provider="gemini",
                    usage={
                        "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                        "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                        "total_tokens": usage_meta.get("totalTokenCount", 0),
                    },
                    finish_reason=candidate.get("finishReason", "STOP"),
                )
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="gemini", message=f"Request timed out after {self.timeout_seconds}s") from e
        except Exception as e:
            raise LLMProviderError(provider="gemini", message=str(e)) from e

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
            raise ProviderAuthError(provider="gemini", message="GEMINI_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        url = f"{self.BASE_URL}/{model}:generateContent?key={self._api_key}"
        system_instruction, contents = self._format_contents(messages)

        generation_config: Dict[str, Any] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
        }
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens
        if json_schema:
            generation_config["responseSchema"] = json_schema

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                candidate = data.get("candidates", [{}])[0]
                return candidate.get("content", {}).get("parts", [{}])[0].get("text", "{}")
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="gemini", message=f"Request timed out after {self.timeout_seconds}s") from e
        except Exception as e:
            raise LLMProviderError(provider="gemini", message=str(e)) from e

    async def stream_text(
        self,
        messages: List[LLMMessage],
        tier: ModelTier = ModelTier.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        if not self.is_configured():
            raise ProviderAuthError(provider="gemini", message="GEMINI_API_KEY is not configured", status_code=401)

        model = self._resolve_model(tier)
        url = f"{self.BASE_URL}/{model}:streamGenerateContent?alt=sse&key={self._api_key}"
        system_instruction, contents = self._format_contents(messages)

        generation_config: Dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        err_text = err_bytes.decode("utf-8", errors="replace")
                        if response.status_code == 429:
                            raise ProviderRateLimitError(provider="gemini", message=err_text, status_code=429)
                        if response.status_code in (401, 403):
                            raise ProviderAuthError(provider="gemini", message=err_text, status_code=response.status_code)
                        raise LLMProviderError(provider="gemini", message=err_text, status_code=response.status_code)

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            raw_json = line[6:].strip()
                            if not raw_json:
                                continue
                            try:
                                chunk_data = json.loads(raw_json)
                                candidate = chunk_data.get("candidates", [{}])[0]
                                text_part = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                                finish_reason = candidate.get("finishReason")
                                is_final = bool(finish_reason and finish_reason != "null")
                                if text_part or is_final:
                                    yield StreamChunk(
                                        text=text_part,
                                        is_final=is_final,
                                        provider="gemini",
                                        finish_reason=finish_reason,
                                    )
                            except json.JSONDecodeError:
                                continue
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise ProviderTimeoutError(provider="gemini", message=f"Stream timed out after {self.timeout_seconds}s") from e
