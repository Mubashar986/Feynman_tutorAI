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


# ==============================================================================
# 4. LLM Question Generation Schemas (Task 4.2, PRD FR-004, FR-010)
# ==============================================================================

class GeneratedOptionSchema(BaseModel):
    option_key: str = Field(..., description="Letter e.g. A, B, C, D")
    content: str = Field(..., description="Markdown and KaTeX formatted option text")
    is_correct: bool = Field(default=False)
    distractor_rationale: Optional[str] = Field(None, description="Diagnostic pedagogical rationale if incorrect")
    order: int = Field(default=0)


class GeneratedRubricSchema(BaseModel):
    criterion: str = Field(..., description="Scoring criterion step")
    points: float = Field(default=1.0, ge=0.25)
    order: int = Field(default=0)


class GeneratedQuestionSchema(BaseModel):
    prompt: str = Field(..., description="Question prompt with KaTeX math")
    hint: Optional[str] = Field(None, description="Pedagogical hint")
    explanation: str = Field(..., description="Step-by-step solution derivation")
    estimated_time_seconds: int = Field(default=120, ge=10, le=3600)
    points: float = Field(default=1.0, ge=0.5, le=50.0)
    options: List[GeneratedOptionSchema] = []
    rubric_items: List[GeneratedRubricSchema] = []


class GeneratedQuestionBatchSchema(BaseModel):
    questions: List[GeneratedQuestionSchema] = Field(..., min_length=1)


class QuestionGenerateRequest(BaseModel):
    exam_template_id: str
    topic_id: str
    learning_objective_id: Optional[str] = None
    question_type: QuestionType = QuestionType.MCQ_SINGLE
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    bloom_level: BloomTaxonomy = BloomTaxonomy.APPLY
    count: int = Field(default=1, ge=1, le=5, description="Number of questions to synthesize")
    custom_prompt_guidance: Optional[str] = Field(None, description="Additional custom instructions for generation")


class GeneratedQuestionBatchResponse(BaseModel):
    generated_count: int
    questions: List[QuestionDetailResponse] = []
    grounded_sources_used: int = 0


# ==============================================================================
# 5. Question Quality, Solvability & Duplication Validation Schemas (Task 4.3)
# ==============================================================================

class BlindSolveSchema(BaseModel):
    is_solvable: bool = Field(..., description="Whether the question is mathematically and logically solvable")
    derived_solution: str = Field(..., description="Step-by-step mathematical or reasoning derivation")
    derived_answer: str = Field(..., description="Final computed answer text or value")
    matched_option_key: Optional[str] = Field(None, description="The option letter (e.g. A, B, C, D) corresponding to the derived answer, if MCQ")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Solver's confidence in its derived answer")
    critique: Optional[str] = Field(None, description="Critique of any ambiguity or missing information in the prompt")


class QualityAuditSchema(BaseModel):
    katex_score: int = Field(..., ge=0, le=25, description="Score for LaTeX/KaTeX equation formatting and delimiter integrity (0-25)")
    clarity_score: int = Field(..., ge=0, le=25, description="Score for pedagogical clarity, precision, and Bloom alignment (0-25)")
    distractor_score: int = Field(..., ge=0, le=25, description="Score for distractor plausibility and diagnostic misconception rationales (0-25)")
    derivation_score: int = Field(..., ge=0, le=25, description="Score for thoroughness and accuracy of step-by-step solution derivation (0-25)")
    overall_critique: str = Field(..., description="Analytical review feedback and pedagogical strengths/weaknesses")
    suggested_improvements: List[str] = Field(default_factory=list, description="Specific revision suggestions if any")


class QualityScoreBreakdown(BaseModel):
    katex_score: int = Field(..., ge=0, le=25)
    clarity_score: int = Field(..., ge=0, le=25)
    distractor_score: int = Field(..., ge=0, le=25)
    derivation_score: int = Field(..., ge=0, le=25)
    total_score: int = Field(..., ge=0, le=100)


class DuplicateMatchInfo(BaseModel):
    matched_question_id: str
    similarity_score: float
    matched_prompt_snippet: str


class QuestionValidationReportResponse(BaseModel):
    question_id: str
    validation_status: ValidationStatus
    is_solvable: bool
    solver_agrees: bool
    solver_derived_answer: Optional[str] = None
    solver_critique: Optional[str] = None
    max_similarity_score: float = 0.0
    duplicate_matches: List[DuplicateMatchInfo] = []
    quality_scores: QualityScoreBreakdown
    critique: str
    suggested_improvements: List[str] = []
    validated_at: datetime


class BatchValidationRequest(BaseModel):
    topic_id: Optional[str] = None
    exam_template_id: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100, description="Max questions to validate in batch")


class BatchValidationResponse(BaseModel):
    total_processed: int
    validated_count: int
    rejected_count: int
    flagged_count: int
    reports: List[QuestionValidationReportResponse] = []

