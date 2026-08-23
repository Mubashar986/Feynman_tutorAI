from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


# ==============================================================================
# 1. Enums: Simulation Session Lifecycle
# ==============================================================================

class SimulationStatus(str, Enum):
    """
    Lifecycle state of a timed mock exam simulation.
    """
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"
    GRADED = "graded"


# ==============================================================================
# 2. Database Models: Exam Blueprints & Topic Distributions (PRD FR-014)
# ==============================================================================

class ExamBlueprintBase(SQLModel):
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    code: str = Field(index=True, unique=True, max_length=50, nullable=False)
    title: str = Field(max_length=200, nullable=False)
    description: Optional[str] = Field(default=None)
    duration_minutes: int = Field(default=90, ge=1, le=360, nullable=False, description="Exam time limit in minutes")
    total_questions: int = Field(default=40, ge=1, le=200, nullable=False, description="Total questions on the paper")
    total_marks: float = Field(default=40.0, ge=1.0, nullable=False, description="Max possible marks")
    passing_percentage: float = Field(default=60.0, ge=0.0, le=100.0, nullable=False)


class ExamBlueprint(ExamBlueprintBase, table=True):
    """
    Official Exam Blueprint specification defining content weighting and exam structure.
    """
    __tablename__ = "exam_blueprints"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class BlueprintTopicDistributionBase(SQLModel):
    blueprint_id: str = Field(foreign_key="exam_blueprints.id", index=True, nullable=False)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    target_weight: float = Field(ge=0.0, le=1.0, nullable=False, description="Target proportion (e.g. 0.30 for 30%)")
    target_question_count: int = Field(default=1, ge=0, nullable=False, description="Computed question quota")


class BlueprintTopicDistribution(BlueprintTopicDistributionBase, table=True):
    """
    Individual topic weighting quota within an Exam Blueprint.
    """
    __tablename__ = "blueprint_topic_distributions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)


# ==============================================================================
# 3. Database Models: Simulation Sessions, Answers & Reports (PRD FR-020)
# ==============================================================================

class SimulationSessionBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    blueprint_id: str = Field(foreign_key="exam_blueprints.id", index=True, nullable=False)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    status: SimulationStatus = Field(default=SimulationStatus.IN_PROGRESS, nullable=False)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: datetime = Field(nullable=False, description="Authoritative server expiry timestamp in UTC")
    submitted_at: Optional[datetime] = Field(default=None)


class SimulationSession(SimulationSessionBase, table=True):
    """
    Active or completed timed exam simulation session.
    """
    __tablename__ = "simulation_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    # JSON list of question IDs assembled for this session in order
    question_ids: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )


class SimulationAnswerBase(SQLModel):
    session_id: str = Field(foreign_key="simulation_sessions.id", index=True, nullable=False)
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    question_id: str = Field(foreign_key="questions.id", index=True, nullable=False)
    selected_option_id: Optional[str] = Field(default=None, description="Selected Option ID for MCQ items")
    numerical_response: Optional[float] = Field(default=None, description="Student numerical answer value")
    text_response: Optional[str] = Field(default=None, description="Student free-response or derivation text")
    is_correct: Optional[bool] = Field(default=None)
    marks_awarded: float = Field(default=0.0, ge=0.0)


class SimulationAnswer(SimulationAnswerBase, table=True):
    """
    Student response to an individual question within a simulation session.
    """
    __tablename__ = "simulation_answers"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    answered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SimulationReportBase(SQLModel):
    session_id: str = Field(foreign_key="simulation_sessions.id", index=True, unique=True, nullable=False)
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    blueprint_id: str = Field(foreign_key="exam_blueprints.id", index=True, nullable=False)
    total_marks_available: float = Field(nullable=False)
    earned_marks: float = Field(nullable=False)
    percentage_score: float = Field(nullable=False)
    is_passed: bool = Field(nullable=False)


class SimulationReport(SimulationReportBase, table=True):
    """
    Comprehensive auto-graded post-exam score report with topic breakdown.
    """
    __tablename__ = "simulation_reports"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    # JSON list of topic score dictionaries [{topic_id, topic_title, total, earned, percentage}]
    topic_breakdown: List[dict] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
