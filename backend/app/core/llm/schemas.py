from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelTier(str, Enum):
    """Pedagogical and reasoning capability tiers."""
    REASONING = "reasoning"  # Frontier reasoning: Question Lab, Blueprint Extraction, Rubrics
    FAST = "fast"            # Low latency interactive: Socratic Tutor streaming, Classifications
    LOCAL = "local"          # Offline / Dev: Ollama local models, Mock testing


class MessageRole(str, Enum):
    """Standard message roles across all LLM providers."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    """Unified chat message representation."""
    role: MessageRole
    content: str


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: Optional[str] = None


class StreamChunk(BaseModel):
    """Incremental streaming token chunk."""
    text: str
    is_final: bool = False
    provider: Optional[str] = None
    finish_reason: Optional[str] = None


# ==============================================================================
# LLM Gateway Exception Hierarchy
# ==============================================================================

class LLMError(Exception):
    """Base exception for all LLM Gateway operations."""
    pass


class LLMProviderError(LLMError):
    """Raised when an external LLM provider returns an API error."""
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        super().__init__(f"[{provider}] {message} (Status: {status_code})")
        self.provider = provider
        self.message = message
        self.status_code = status_code


class ProviderRateLimitError(LLMProviderError):
    """Raised on HTTP 429 (Rate Limit / Quota Exceeded). Triggers immediate fallback."""
    pass


class ProviderAuthError(LLMProviderError):
    """Raised on HTTP 401/403 (Invalid or Missing API Key)."""
    pass


class ProviderTimeoutError(LLMProviderError):
    """Raised when provider request exceeds connect or read timeout."""
    pass


class SchemaValidationError(LLMError):
    """Raised when LLM output fails Pydantic schema validation."""
    def __init__(self, message: str, raw_text: str, validation_errors: Optional[Any] = None):
        super().__init__(f"Structured output schema validation failed: {message}")
        self.raw_text = raw_text
        self.validation_errors = validation_errors
