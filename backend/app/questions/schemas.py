from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from backend.app.questions.models import (
    BloomTaxonomy,
    DifficultyLevel,
    QuestionType,
    ValidationStatus,
)


# ==============================================================================
# 1. Option Schemas
# ==============================================================================

class QuestionOptionBase(BaseModel):
    option_key: str = Field(..., min_length=1, max_length=10, description="Option identifier e.g. A, B, C, D")
    content: str = Field(..., min_length=1, description="Option text with KaTeX support")
    is_correct: bool = Field(default=False)
    distractor_rationale: Optional[str] = Field(None, description="Diagnostic misconception rationale")
    order: int = Field(default=0)


class QuestionOptionCreate(QuestionOptionBase):
    pass


class QuestionOptionResponse(QuestionOptionBase):
    id: str
    question_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 2. Rubric Item Schemas
# ==============================================================================

class QuestionRubricItemBase(BaseModel):
    criterion: str = Field(..., min_length=1, description="Scoring criterion step")
    points: float = Field(default=1.0, ge=0.25, le=50.0)
    order: int = Field(default=0)


class QuestionRubricItemCreate(QuestionRubricItemBase):
    pass


class QuestionRubricItemResponse(QuestionRubricItemBase):
    id: str
    question_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 3. Question Schemas
# ==============================================================================

class QuestionBase(BaseModel):
    exam_template_id: str
    topic_id: str
    learning_objective_id: Optional[str] = None
    question_type: QuestionType = QuestionType.MCQ_SINGLE
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    bloom_level: BloomTaxonomy = BloomTaxonomy.APPLY
    validation_status: ValidationStatus = ValidationStatus.PENDING_VALIDATION
    prompt: str = Field(..., min_length=5, description="Markdown & KaTeX prompt")
    hint: Optional[str] = None
    explanation: str = Field(..., min_length=5, description="Step-by-step solution derivation")
    estimated_time_seconds: int = Field(default=120, ge=10, le=3600)
    points: float = Field(default=1.0, ge=0.5, le=100.0)
    is_generated_by_ai: bool = False


class QuestionCreate(QuestionBase):
    options: List[QuestionOptionCreate] = []
    rubric_items: List[QuestionRubricItemCreate] = []

    @model_validator(mode="after")
    def validate_question_invariants(self) -> "QuestionCreate":
        if self.question_type == QuestionType.MCQ_SINGLE:
            if len(self.options) < 2:
                raise ValueError("MCQ_SINGLE requires at least 2 options")
            correct_count = sum(1 for opt in self.options if opt.is_correct)
            if correct_count != 1:
                raise ValueError(f"MCQ_SINGLE must have exactly 1 correct option (found {correct_count})")
        elif self.question_type == QuestionType.MCQ_MULTI:
            if len(self.options) < 2:
                raise ValueError("MCQ_MULTI requires at least 2 options")
            correct_count = sum(1 for opt in self.options if opt.is_correct)
            if correct_count < 1:
                raise ValueError("MCQ_MULTI must have at least 1 correct option")
        return self


class QuestionUpdate(BaseModel):
    prompt: Optional[str] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    bloom_level: Optional[BloomTaxonomy] = None
    validation_status: Optional[ValidationStatus] = None
    estimated_time_seconds: Optional[int] = None
    points: Optional[float] = None
    topic_id: Optional[str] = None
    learning_objective_id: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: str
    created_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionDetailResponse(QuestionResponse):
    options: List[QuestionOptionResponse] = []
    rubric_items: List[QuestionRubricItemResponse] = []


class QuestionListResponse(BaseModel):
    total: int
    questions: List[QuestionDetailResponse] = []
