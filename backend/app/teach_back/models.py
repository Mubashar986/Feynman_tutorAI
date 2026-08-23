from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


# ==============================================================================
# 1. Enums: Audience Levels & Mastery Assessment Tiers (PRD Cap 17, FR-017)
# ==============================================================================

class TeachBackAudienceLevel(str, Enum):
    """
    Target audience scaffolding level for the Feynman Technique.
    """
    CHILD_10YO = "child_10yo"             # Extreme simplification; no unexplained jargon; simple analogies
    HIGH_SCHOOL_PEER = "high_school_peer" # Standard pedagogical level; basic algebra and standard definitions
    UNDERGRAD_EXAMINER = "undergrad_examiner" # Rigorous academic rigor; complete formal derivations and exact notation


class MasteryAssessmentLevel(str, Enum):
    """
    Holistic mastery tier based on multi-criterion rubric score.
    """
    MASTERED = "mastered"         # >= 85% composite score
    COMPETENT = "competent"       # 70 - 84% composite score
    DEVELOPING = "developing"     # 50 - 69% composite score
    NEEDS_REVIEW = "needs_review" # < 50% composite score


# ==============================================================================
# 2. Database Models: Teach-Back Sessions & Multi-Criterion Evaluations
# ==============================================================================

class TeachBackSessionBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    concept_title: str = Field(default="Concept Teach-Back", max_length=200)
    audience_level: TeachBackAudienceLevel = Field(
        default=TeachBackAudienceLevel.HIGH_SCHOOL_PEER,
        nullable=False,
    )


class TeachBackSession(TeachBackSessionBase, table=True):
    """
    Teach-Back learning session state boundary (PRD Cap 17, §14.4, FR-017).
    Enforces student and exam isolation (Constraint #2).
    """
    __tablename__ = "teach_back_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )


class TeachBackEvaluationBase(SQLModel):
    session_id: str = Field(foreign_key="teach_back_sessions.id", index=True, nullable=False)
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    student_explanation: str = Field(nullable=False, description="Full explanation text submitted by student")
    overall_score: float = Field(default=0.0, nullable=False, description="Weighted composite score 0.0 - 100.0")
    assessment_level: MasteryAssessmentLevel = Field(
        default=MasteryAssessmentLevel.DEVELOPING,
        nullable=False,
    )
    criteria_scores_json: str = Field(
        default="[]",
        description="Serialized JSON array of rubric criteria scores and weights",
    )
    strengths_json: str = Field(
        default="[]",
        description="Serialized JSON array of identified strengths",
    )
    misconceptions_json: str = Field(
        default="[]",
        description="Serialized JSON array of identified student misconceptions",
    )
    missing_elements_json: str = Field(
        default="[]",
        description="Serialized JSON array of missing syllabus learning objectives",
    )
    prerequisite_gaps_json: str = Field(
        default="[]",
        description="Serialized JSON array of missing prerequisite concepts",
    )
    pedagogical_feedback: str = Field(
        default="",
        description="Targeted narrative feedback and corrective guidance",
    )
    model_correction_latex: Optional[str] = Field(
        default=None,
        description="Optional model answer or corrected KaTeX formula snippet",
    )


class TeachBackEvaluation(TeachBackEvaluationBase, table=True):
    """
    Immutable evaluation record capturing multi-criterion rubric scoring,
    misconceptions, and prerequisite gap diagnostics.
    """
    __tablename__ = "teach_back_evaluations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
