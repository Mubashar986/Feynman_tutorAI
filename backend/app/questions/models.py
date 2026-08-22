from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid
from sqlmodel import Field, Relationship, SQLModel


# ==============================================================================
# Enumerations for Question Bank & Psychometrics (PRD §5.4, §15, FR-004)
# ==============================================================================

class QuestionType(str, Enum):
    MCQ_SINGLE = "mcq_single"
    MCQ_MULTI = "mcq_multi"
    NUMERICAL = "numerical"
    FREE_RESPONSE = "free_response"
    DERIVATION_STEP = "derivation_step"
    MATCHING = "matching"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    CHALLENGE = "challenge"


class BloomTaxonomy(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class ValidationStatus(str, Enum):
    DRAFT = "draft"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    FLAGGED = "flagged"


# ==============================================================================
# Database Models
# ==============================================================================

class QuestionBase(SQLModel):
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True)
    topic_id: str = Field(foreign_key="topics.id", index=True)
    learning_objective_id: Optional[str] = Field(default=None, foreign_key="learning_objectives.id", index=True)
    question_type: QuestionType = Field(default=QuestionType.MCQ_SINGLE, index=True)
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, index=True)
    bloom_level: BloomTaxonomy = Field(default=BloomTaxonomy.APPLY, index=True)
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING_VALIDATION, index=True)
    prompt: str = Field(description="Markdown and KaTeX formatted question prompt")
    hint: Optional[str] = Field(default=None, description="Optional pedagogical hint")
    explanation: str = Field(description="Detailed step-by-step solution derivation")
    estimated_time_seconds: int = Field(default=120, ge=10, le=3600)
    points: float = Field(default=1.0, ge=0.5, le=100.0)
    is_generated_by_ai: bool = Field(default=False)
    created_by_user_id: Optional[str] = Field(default=None, foreign_key="users.id")


class Question(QuestionBase, table=True):
    __tablename__ = "questions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relational associations
    options: List["QuestionOption"] = Relationship(
        back_populates="question",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    rubric_items: List["QuestionRubricItem"] = Relationship(
        back_populates="question",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )


class QuestionOptionBase(SQLModel):
    option_key: str = Field(description="Letter or identifier e.g. A, B, C, D")
    content: str = Field(description="Markdown and KaTeX formatted option content")
    is_correct: bool = Field(default=False)
    distractor_rationale: Optional[str] = Field(default=None, description="Misconception diagnostic rationale")
    order: int = Field(default=0)


class QuestionOption(QuestionOptionBase, table=True):
    __tablename__ = "question_options"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    question_id: str = Field(foreign_key="questions.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    question: Optional[Question] = Relationship(back_populates="options")


class QuestionRubricItemBase(SQLModel):
    criterion: str = Field(description="Grading rubric criterion description")
    points: float = Field(default=1.0, ge=0.25)
    order: int = Field(default=0)


class QuestionRubricItem(QuestionRubricItemBase, table=True):
    __tablename__ = "question_rubrics"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    question_id: str = Field(foreign_key="questions.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    question: Optional[Question] = Relationship(back_populates="rubric_items")
