import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel

from backend.app.core.config import Settings, settings as app_settings
from backend.app.core.llm.base import LLMProviderBase
from backend.app.core.llm.providers.anthropic import AnthropicProvider
from backend.app.core.llm.providers.gemini import GeminiProvider
from backend.app.core.llm.providers.mock import MockLLMProvider
from backend.app.core.llm.providers.ollama import OllamaProvider
from backend.app.core.llm.providers.openai import OpenAIProvider
from backend.app.core.llm.schemas import (
    LLMMessage,
    LLMProviderError,
    LLMResponse,
    MessageRole,
    ModelTier,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SchemaValidationError,
    StreamChunk,
)
from backend.app.core.llm.validator import PydanticOutputValidator

logger = logging.getLogger("feynman.llm.gateway")
T = TypeVar("T", bound=BaseModel)


class LLMGateway:
    """
    Central Multi-Provider LLM Gateway Orchestrator.
    Handles dynamic provider routing, automated fallback on rate limits/downtime,
    and strict Pydantic V2 schema validation for structured outputs.
    Enforces PRD Constraint #1 (AI Safety) and PRD Constraint #10 (Zero Vendor Lock-in).
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or app_settings
        self._providers: Dict[str, LLMProviderBase] = {}
        self._default_provider_name: str = "mock"
        self._fallback_order: List[str] = []
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initializes all concrete provider adapters from application settings."""
        # 1. OpenRouter (Multi-Model Gateway)
        openrouter_key = getattr(self.settings, "OPENROUTER_API_KEY", "") or (
            self.settings.OPENAI_API_KEY if self.settings.OPENAI_API_KEY.startswith("sk-or-") else ""
        )
        openrouter_model = getattr(self.settings, "OPENROUTER_MODEL", "z-ai/glm-5.2:free")
        openrouter = OpenAIProvider(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            reasoning_model=openrouter_model,
            fast_model=openrouter_model,
            provider_name="openrouter",
        )
        self.register_provider(openrouter)

        # 2. Groq Cloud (Ultra-Fast)
        groq_key = getattr(self.settings, "GROQ_API_KEY", "")
        groq = OpenAIProvider(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
            reasoning_model="llama-3.3-70b-versatile",
            fast_model="llama-3.3-70b-versatile",
            provider_name="groq",
        )
        self.register_provider(groq)

        # 3. Google Gemini
        gemini = GeminiProvider(api_key=self.settings.GEMINI_API_KEY)
        self.register_provider(gemini)

        # 4. Direct OpenAI
        openai = OpenAIProvider(api_key=self.settings.OPENAI_API_KEY)
        self.register_provider(openai)

        # 5. Anthropic Claude
        anthropic = AnthropicProvider(api_key=self.settings.ANTHROPIC_API_KEY)
        self.register_provider(anthropic)

        # 6. Local Ollama
        ollama = OllamaProvider(base_url=self.settings.OLLAMA_BASE_URL)
        self.register_provider(ollama)

        # 7. Deterministic Mock Provider (always available for fallback/testing)
        mock_provider = MockLLMProvider()
        self.register_provider(mock_provider)

        # Determine configured default and fallback order
        configured_default = getattr(self.settings, "DEFAULT_LLM_PROVIDER", "openrouter").lower()
        
        # Priority order: configured default -> openrouter -> groq -> gemini -> openai -> anthropic -> ollama -> mock
        candidate_order = [configured_default, "openrouter", "groq", "gemini", "openai", "anthropic", "ollama", "mock"]
        seen = set()
        self._fallback_order = []
        for name in candidate_order:
            if name in self._providers and name not in seen:
                seen.add(name)
                self._fallback_order.append(name)

        # Set default to the first configured provider that has active credentials, or mock
        self._default_provider_name = "mock"
        for name in self._fallback_order:
            if name == "mock" or (name in self._providers and self._providers[name].is_configured()):
                self._default_provider_name = name
                break

        logger.info(
            f"LLMGateway initialized. Default provider: '{self._default_provider_name}'. "
            f"Fallback chain: {self._fallback_order}"
        )

    def register_provider(self, provider: LLMProviderBase, is_default: bool = False) -> None:
        """Registers or overrides a provider adapter."""
        self._providers[provider.provider_name] = provider
        if is_default:
            self._default_provider_name = provider.provider_name
            if provider.provider_name in self._fallback_order:
                self._fallback_order.remove(provider.provider_name)
            self._fallback_order.insert(0, provider.provider_name)
        elif provider.provider_name not in self._fallback_order:
            self._fallback_order.append(provider.provider_name)

    def set_fallback_chain(self, chain: List[str]) -> None:
        """Explicitly sets the fallback priority order."""
        self._fallback_order = list(chain)

    def get_provider(self, name: str) -> LLMProviderBase:
        """Retrieves a registered provider by name."""
        if name not in self._providers:
            raise LLMProviderError(provider=name, message=f"Provider '{name}' is not registered in LLMGateway")
        return self._providers[name]

    def _build_provider_chain(self, preferred_provider: Optional[str] = None) -> List[LLMProviderBase]:
        """Builds an ordered list of providers to attempt in sequence."""
        chain_names = []
        if preferred_provider and preferred_provider in self._providers:
            chain_names.append(preferred_provider)
        if self._default_provider_name in self._providers and self._default_provider_name not in chain_names:
            chain_names.append(self._default_provider_name)
        for name in self._fallback_order:
            if name not in chain_names and name in self._providers:
                chain_names.append(name)

        # Filter to active/configured providers
        active_providers = [
            self._providers[name]
            for name in chain_names
            if name in self._providers and (name == "mock" or isinstance(self._providers[name], MockLLMProvider) or self._providers[name].is_configured())
        ]
        if not active_providers:
            active_providers = [self._providers.get("mock", MockLLMProvider())]
        return active_providers

    def _normalize_messages(self, messages: Union[List[LLMMessage], str], system_prompt: Optional[str] = None) -> List[LLMMessage]:
        """Normalizes raw strings or message lists into List[LLMMessage]."""
        formatted: List[LLMMessage] = []
        if system_prompt:
            formatted.append(LLMMessage(role=MessageRole.SYSTEM, content=system_prompt))

        if isinstance(messages, str):
            formatted.append(LLMMessage(role=MessageRole.USER, content=messages))
        else:
            for msg in messages:
                formatted.append(msg)
        return formatted

    async def generate_text(
        self,
        messages: Union[List[LLMMessage], str],
        tier: ModelTier = ModelTier.FAST,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Executes text generation with automated fallback on rate limits and cloud errors.
        """
        normalized_messages = self._normalize_messages(messages, system_prompt)
        provider_chain = self._build_provider_chain(preferred_provider)
        last_error: Optional[Exception] = None

        for provider in provider_chain:
            try:
                logger.debug(f"Attempting generate_text via provider: {provider.provider_name}")
                response = await provider.generate_text(
                    messages=normalized_messages,
                    tier=tier,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                return response
            except (ProviderRateLimitError, ProviderTimeoutError, ProviderAuthError, LLMProviderError) as exc:
                logger.warning(
                    f"Provider '{provider.provider_name}' failed during generate_text: {exc}. "
                    "Triggering next fallback provider..."
                )
                last_error = exc
                continue

        raise LLMProviderError(
            provider="gateway",
            message=f"All configured providers in fallback chain failed. Last error: {str(last_error)}",
        ) from last_error

    async def generate_structured(
        self,
        messages: Union[List[LLMMessage], str],
        response_model: Type[T],
        tier: ModelTier = ModelTier.REASONING,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> T:
        """
        Generates structured JSON and validates it against a strict Pydantic V2 model.
        Enforces PRD Constraint #1 (No unvalidated LLM output becomes official state).
        """
        schema = PydanticOutputValidator.get_json_schema(response_model)
        schema_instruction = (
            f"\n\nYou MUST respond strictly in valid JSON conforming to this schema:\n"
            f"{schema}\nDo not include any conversational preamble or explanations outside JSON."
        )

        effective_system_prompt = (system_prompt or "") + schema_instruction
        normalized_messages = self._normalize_messages(messages, effective_system_prompt)
        provider_chain = self._build_provider_chain(preferred_provider)
        last_error: Optional[Exception] = None

        for provider in provider_chain:
            try:
                logger.debug(f"Attempting generate_structured via provider: {provider.provider_name}")
                raw_json = await provider.generate_json(
                    messages=normalized_messages,
                    json_schema=schema,
                    tier=tier,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                # Strict validation gate
                validated_obj = PydanticOutputValidator.validate(raw_json, response_model)
                return validated_obj
            except SchemaValidationError as sve:
                logger.warning(
                    f"Pydantic schema validation error on provider '{provider.provider_name}': {sve}. "
                    "Attempting fallback provider..."
                )
                last_error = sve
                continue
            except (ProviderRateLimitError, ProviderTimeoutError, ProviderAuthError, LLMProviderError) as exc:
                logger.warning(
                    f"Provider '{provider.provider_name}' failed during generate_structured: {exc}. "
                    "Triggering next fallback provider..."
                )
                last_error = exc
                continue

        raise LLMProviderError(
            provider="gateway",
            message=f"All configured providers failed structured output generation. Last error: {str(last_error)}",
        ) from last_error

    async def stream_text(
        self,
        messages: Union[List[LLMMessage], str],
        tier: ModelTier = ModelTier.FAST,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Streams text tokens from the primary provider with fallback to backup on immediate connection failure.
        """
        normalized_messages = self._normalize_messages(messages, system_prompt)
        provider_chain = self._build_provider_chain(preferred_provider)
        last_error: Optional[Exception] = None

        for provider in provider_chain:
            try:
                logger.debug(f"Attempting stream_text via provider: {provider.provider_name}")
                stream = provider.stream_text(
                    messages=normalized_messages,
                    tier=tier,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                # Yield from the active provider stream
                async for chunk in stream:
                    yield chunk
                return
            except (ProviderRateLimitError, ProviderTimeoutError, ProviderAuthError, LLMProviderError) as exc:
                logger.warning(
                    f"Provider '{provider.provider_name}' failed stream initialization: {exc}. "
                    "Falling back to next provider..."
                )
                last_error = exc
                continue

        raise LLMProviderError(
            provider="gateway",
            message=f"All providers failed to initialize stream. Last error: {str(last_error)}",
        ) from last_error


# Singleton instance helper
_gateway_instance: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    """FastAPI dependency injection and service helper."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = LLMGateway()
    return _gateway_instance
