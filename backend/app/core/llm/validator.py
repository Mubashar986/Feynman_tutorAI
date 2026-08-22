import json
import re
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError

from backend.app.core.llm.schemas import SchemaValidationError

T = TypeVar("T", bound=BaseModel)


class PydanticOutputValidator:
    """
    Validates, sanitizes, and parses LLM outputs against strict Pydantic V2 schemas.
    Enforces PRD Constraint #1 (LLM output must not directly mutate state without validation).
    """

    @staticmethod
    def clean_json_markdown(raw_text: str) -> str:
        """
        Strips markdown code fences (```json ... ``` or ``` ... ```) and leading/trailing whitespace.
        Extracts the outermost valid JSON structure if surrounded by conversational filler.
        """
        text = raw_text.strip()
        
        # Remove ```json ... ``` or ``` ... ``` wrappers
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            text = fence_match.group(1).strip()
            
        # If still not starting with { or [, find the first { or [ and last } or ]
        start_curly = text.find("{")
        start_bracket = text.find("[")
        
        start_idx = -1
        if start_curly != -1 and (start_bracket == -1 or start_curly < start_bracket):
            start_idx = start_curly
            end_idx = text.rfind("}")
            if end_idx > start_idx:
                text = text[start_idx : end_idx + 1]
        elif start_bracket != -1:
            start_idx = start_bracket
            end_idx = text.rfind("]")
            if end_idx > start_idx:
                text = text[start_idx : end_idx + 1]

        return text

    @classmethod
    def validate(cls, raw_text: str, response_model: Type[T]) -> T:
        """
        Sanitizes raw text and validates it against the target Pydantic V2 model.
        Raises SchemaValidationError on failure.
        """
        cleaned_text = cls.clean_json_markdown(raw_text)
        
        try:
            # Pydantic V2 native Rust-based JSON parser & validator
            return response_model.model_validate_json(cleaned_text)
        except ValidationError as ve:
            raise SchemaValidationError(
                message=f"Pydantic validation failed for {response_model.__name__}: {str(ve)}",
                raw_text=raw_text,
                validation_errors=ve.errors(),
            ) from ve
        except Exception as exc:
            # Handle JSON syntax errors before Pydantic
            raise SchemaValidationError(
                message=f"Failed to parse JSON string for {response_model.__name__}: {str(exc)}",
                raw_text=raw_text,
            ) from exc

    @staticmethod
    def get_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
        """Returns JSON schema definition for prompt injection or provider API."""
        return model.model_json_schema()
