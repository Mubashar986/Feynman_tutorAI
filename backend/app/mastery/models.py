from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel

from backend.app.questions.models import DifficultyLevel


# ==============================================================================
# 1. Mastery Status Enumeration (PRD §5.4, §13, FR-003)
# ==============================================================================

class MasteryStatus(str, Enum):
    """
    Pedagogical topic mastery status levels.
    """
    NOVICE = "novice"              # P(L) < 0.30 (Not studied / foundational)
    PRACTICING = "practicing"      # 0.30 <= P(L) < 0.60 (Active learning)
    PROFICIENT = "proficient"      # 0.60 <= P(L) < 0.85 (Reliable solving)
    MASTERED = "mastered"          # P(L) >= 0.85 (Certified high-confidence competence)


# ==============================================================================
# 2. Database Models
# ==============================================================================

class StudentTopicMasteryBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    mastery_probability: float = Field(default=0.10, ge=0.0, le=1.0, index=True)
    status: MasteryStatus = Field(default=MasteryStatus.NOVICE, index=True)
    current_difficulty: DifficultyLevel = Field(default=DifficultyLevel.EASY, index=True)
    total_attempts: int = Field(default=0, ge=0)
    correct_attempts: int = Field(default=0, ge=0)
    current_streak: int = Field(default=0, ge=0)
    best_streak: int = Field(default=0, ge=0)
    last_attempt_at: Optional[datetime] = Field(default=None)


class StudentTopicMastery(StudentTopicMasteryBase, table=True):
    """
    Live mathematical student mastery state per topic and exam template (PRD FR-003, Cap 3).
    Isolates student state per tenant/exam (Constraint #2).
    """
    __tablename__ = "student_topic_masteries"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudentQuestionAttemptBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    question_id: str = Field(foreign_key="questions.id", index=True, nullable=False)
    selected_option_key: Optional[str] = Field(default=None)
    is_correct: bool = Field(nullable=False)
    time_spent_seconds: Optional[int] = Field(default=None, ge=0)
    prior_mastery_probability: float = Field(ge=0.0, le=1.0)
    posterior_mastery_probability: float = Field(ge=0.0, le=1.0)


class StudentQuestionAttempt(StudentQuestionAttemptBase, table=True):
    """
    Immutable telemetry record for each question attempt (PRD FR-025, NFR-008).
    Captures telemetry and provides event feeds for the Error Bank (Task 5.2).
    """
    __tablename__ = "student_question_attempts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
