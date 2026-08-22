import pytest
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.core.llm import (
    AnthropicProvider,
    GeminiProvider,
    LLMGateway,
    LLMMessage,
    LLMProviderError,
    LLMResponse,
    MessageRole,
    MockLLMProvider,
    ModelTier,
    OllamaProvider,
    OpenAIProvider,
    ProviderRateLimitError,
    PydanticOutputValidator,
    SchemaValidationError,
    StreamChunk,
)


# Test Pydantic Schemas
class SimpleItemSchema(BaseModel):
    name: str
    count: int = Field(gt=0)
    tags: List[str] = Field(default_factory=list)


class GeneratedQuestionStub(BaseModel):
    stem: str
    options: List[str]
    correct_index: int = Field(ge=0, le=3)
    explanation: str


# ==============================================================================
# 1. PydanticOutputValidator Tests
# ==============================================================================

def test_validator_cleans_markdown_fences():
    raw_markdown = """```json
    {
        "name": "Physics Concept",
        "count": 4,
        "tags": ["kinematics", "mechanics"]
    }
    ```"""
    cleaned = PydanticOutputValidator.clean_json_markdown(raw_markdown)
    assert cleaned.startswith("{")
    assert cleaned.endswith("}")

    validated = PydanticOutputValidator.validate(raw_markdown, SimpleItemSchema)
    assert validated.name == "Physics Concept"
    assert validated.count == 4
    assert validated.tags == ["kinematics", "mechanics"]


def test_validator_handles_raw_json():
    raw = '{"name": "Calculus", "count": 10, "tags": ["derivatives"]}'
    validated = PydanticOutputValidator.validate(raw, SimpleItemSchema)
    assert validated.name == "Calculus"
    assert validated.count == 10


def test_validator_rejects_invalid_schema():
    # count is negative, violating gt=0 constraint
    invalid_raw = '{"name": "Invalid", "count": -5}'
    with pytest.raises(SchemaValidationError) as exc_info:
        PydanticOutputValidator.validate(invalid_raw, SimpleItemSchema)
    assert "Pydantic validation failed" in str(exc_info.value)


def test_validator_rejects_malformed_json():
    malformed = '{"name": "Broken", "count": }'
    with pytest.raises(SchemaValidationError):
        PydanticOutputValidator.validate(malformed, SimpleItemSchema)


# ==============================================================================
# 2. MockLLMProvider Unit Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_mock_provider_generate_text():
    provider = MockLLMProvider(default_text="Physics explanation")
    messages = [LLMMessage(role=MessageRole.USER, content="Explain Newton's second law")]

    response = await provider.generate_text(messages=messages, tier=ModelTier.FAST)
    assert isinstance(response, LLMResponse)
    assert "Physics explanation" in response.content
    assert response.provider == "mock"
    assert response.usage["total_tokens"] > 0


@pytest.mark.asyncio
async def test_mock_provider_generate_json():
    expected_data = {
        "stem": "What is force?",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "explanation": "F = ma",
    }
    provider = MockLLMProvider(default_json=expected_data)
    messages = [LLMMessage(role=MessageRole.USER, content="Generate a question")]

    raw_json = await provider.generate_json(messages=messages)
    validated = PydanticOutputValidator.validate(raw_json, GeneratedQuestionStub)
    assert validated.stem == "What is force?"
    assert validated.correct_index == 0


@pytest.mark.asyncio
async def test_mock_provider_stream_text():
    provider = MockLLMProvider()
    messages = [LLMMessage(role=MessageRole.USER, content="Stream hello")]

    chunks = []
    async for chunk in provider.stream_text(messages=messages):
        assert isinstance(chunk, StreamChunk)
        chunks.append(chunk.text)

    full_text = "".join(chunks)
    assert "mock streaming" in full_text


@pytest.mark.asyncio
async def test_mock_provider_simulates_rate_limit():
    provider = MockLLMProvider(simulate_rate_limit=True)
    messages = [LLMMessage(role=MessageRole.USER, content="Test")]

    with pytest.raises(ProviderRateLimitError) as exc_info:
        await provider.generate_text(messages=messages)
    assert exc_info.value.status_code == 429


# ==============================================================================
# 3. LLMGateway Multi-Provider Fallback Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_llm_gateway_generate_text_success():
    gateway = LLMGateway()
    mock = MockLLMProvider(name="mock_primary", default_text="Success response")
    gateway.register_provider(mock, is_default=True)

    response = await gateway.generate_text("What is energy?")
    assert isinstance(response, LLMResponse)
    assert "Success response" in response.content
    assert response.provider == "mock_primary"


@pytest.mark.asyncio
async def test_llm_gateway_structured_output_validation():
    gateway = LLMGateway()
    question_data = {
        "stem": "What is the unit of electric charge?",
        "options": ["Coulomb", "Ampere", "Volt", "Ohm"],
        "correct_index": 0,
        "explanation": "Charge is measured in Coulombs (C).",
    }
    mock = MockLLMProvider(name="mock_reasoning", default_json=question_data)
    gateway.register_provider(mock, is_default=True)

    result = await gateway.generate_structured(
        messages="Generate a physics question on charge",
        response_model=GeneratedQuestionStub,
        tier=ModelTier.REASONING,
    )

    assert isinstance(result, GeneratedQuestionStub)
    assert result.stem == "What is the unit of electric charge?"
    assert result.options[0] == "Coulomb"
    assert result.correct_index == 0


@pytest.mark.asyncio
async def test_llm_gateway_dynamic_fallback_on_rate_limit():
    """
    Verifies that when the primary provider hits HTTP 429 rate limit,
    the gateway automatically catches the error and falls back to the secondary provider seamlessly.
    """
    gateway = LLMGateway()

    # Provider 1: Failing with 429
    failing_primary = MockLLMProvider(
        name="failing_primary",
        simulate_rate_limit=True,
    )
    # Provider 2: Healthy backup
    healthy_secondary = MockLLMProvider(
        name="healthy_secondary",
        default_text="Resilient fallback successful!",
    )

    # Register both and configure explicit fallback chain
    gateway.register_provider(failing_primary)
    gateway.register_provider(healthy_secondary)
    gateway.set_fallback_chain(["failing_primary", "healthy_secondary"])

    # Preferred failing_primary -> should fallback to healthy_secondary
    response = await gateway.generate_text(
        messages="Test prompt",
        preferred_provider="failing_primary",
    )

    assert response.provider == "healthy_secondary"
    assert "Resilient fallback successful!" in response.content


@pytest.mark.asyncio
async def test_llm_gateway_all_providers_fail_raises():
    gateway = LLMGateway()
    p1 = MockLLMProvider(name="mock1", simulate_rate_limit=True)
    gateway._providers = {"mock1": p1}
    gateway._fallback_order = ["mock1"]

    with pytest.raises(LLMProviderError) as exc_info:
        await gateway.generate_text("Test prompt")
    assert "All configured providers in fallback chain failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_llm_gateway_stream_text():
    gateway = LLMGateway()
    mock = MockLLMProvider(name="stream_mock")
    gateway.register_provider(mock, is_default=True)

    chunks = []
    async for chunk in gateway.stream_text("Stream test"):
        chunks.append(chunk.text)

    assert len(chunks) > 0
    assert "mock streaming" in "".join(chunks)


# ==============================================================================
# 4. Concrete Provider Adapter Sanity & Configuration Checks
# ==============================================================================

def test_concrete_providers_unconfigured_state():
    gemini = GeminiProvider(api_key="")
    openai = OpenAIProvider(api_key="")
    anthropic = AnthropicProvider(api_key="")
    ollama = OllamaProvider(base_url="http://localhost:11434")

    assert not gemini.is_configured()
    assert not openai.is_configured()
    assert not anthropic.is_configured()
    assert ollama.is_configured()  # Ollama requires only base_url
