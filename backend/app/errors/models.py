from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


# ==============================================================================
# 1. Error Taxonomy & Repair Status Enums (PRD §12, FR-006, FR-012)
# ==============================================================================

class ErrorCategory(str, Enum):
    """
    Cognitive diagnostic taxonomy categories.
    """
    CONCEPTUAL = "conceptual"                # Misunderstanding of core physics/math law or principle
    CALCULATION = "calculation"              # Arithmetic, algebraic manipulation, or sign mistake
    MISREAD = "misread"                      # Overlooked parameter, unit conversion, or question wording
    INCOMPLETE = "incomplete"                # Early termination of multi-step problem derivation
    REPRESENTATIONAL = "representational"    # Diagram, vector, coordinate frame, or graph interpretation error


class RepairStatus(str, Enum):
    """
    Remediation lifecycle status of a student's error ticket.
    """
    ACTIVE = "active"            # Recently detected, pending remediation
    REMEDIATING = "remediating"  # Currently in Socratic review or teach-back drill
    REPAIRED = "repaired"        # Resolved via subsequent correct attempts or topic mastery


# ==============================================================================
# 2. Database Models
# ==============================================================================

class MisconceptionBase(SQLModel):
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    code: str = Field(index=True, description="Human-readable taxonomy slug e.g. MISC_KIN_SIGN_CONFUSION")
    title: str = Field(description="Short pedagogical misconception summary")
    description: str = Field(description="Detailed explanation of the cognitive misconception")
    remediation_guidance: Optional[str] = Field(default=None, description="Actionable tutor remediation strategy")


class Misconception(MisconceptionBase, table=True):
    """
    Root cognitive misconception node in the curriculum knowledge graph (PRD FR-012).
    Maps 1-to-many across multiple student question mistakes.
    """
    __tablename__ = "misconceptions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StudentErrorLogBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    question_id: str = Field(foreign_key="questions.id", index=True, nullable=False)
    attempt_id: Optional[str] = Field(default=None, index=True)
    misconception_id: Optional[str] = Field(default=None, foreign_key="misconceptions.id", index=True)
    error_category: ErrorCategory = Field(default=ErrorCategory.CONCEPTUAL, index=True)
    student_answer: Optional[str] = Field(default=None, description="Option letter or raw response submitted")
    correct_answer: Optional[str] = Field(default=None, description="Correct option letter or answer value")
    distractor_rationale: Optional[str] = Field(default=None, description="Diagnostic rationale from question option")
    repair_status: RepairStatus = Field(default=RepairStatus.ACTIVE, index=True)
    occurrence_count: int = Field(default=1, ge=1, description="Number of times this mistake was repeated")


class StudentErrorLog(StudentErrorLogBase, table=True):
    """
    Diagnostic error bank ticket tracking student mistakes and remediation state (PRD FR-006, Cap 6).
    Enforces PRD Constraint #8 (no silent advance after critical failure).
    """
    __tablename__ = "student_error_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    first_detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    repaired_at: Optional[datetime] = Field(default=None)
