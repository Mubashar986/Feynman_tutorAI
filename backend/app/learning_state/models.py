from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid
from sqlmodel import Column, Field, JSON, SQLModel


class LearningState(str, Enum):
    """
    Formal Student Learning States conforming to PRD §13 & FR-001.
    Controls the pedagogical progression lifecycle.
    """
    NOT_STARTED = "not_started"
    CALIBRATION = "calibration"
    FOUNDATION = "foundation"
    PRACTICING = "practicing"
    ASSESSMENT = "assessment"
    DIAGNOSIS = "diagnosis"
    REPAIR = "repair"
    MASTERY = "mastery"
    REVISION = "revision"


class StudentLearningState(SQLModel, table=True):
    """
    Authoritative student learning state per topic and exam template.
    Guarantees tenant isolation per student and exam (PRD Constraint #2, FR-022).
    """
    __tablename__ = "student_learning_states"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(index=True, nullable=False)
    topic_id: str = Field(index=True, nullable=False)
    current_state: LearningState = Field(
        default=LearningState.NOT_STARTED,
        index=True,
        nullable=False,
    )
    mastery_score: float = Field(default=0.0, nullable=False)
    consecutive_successes: int = Field(default=0, nullable=False)
    consecutive_failures: int = Field(default=0, nullable=False)
    last_transition_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class StateTransitionLog(SQLModel, table=True):
    """
    Immutable append-only audit trail recording every state change and its evidence.
    Fulfills PRD FR-025, NFR-008 (Explainability and Auditability).
    """
    __tablename__ = "state_transition_logs"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(index=True, nullable=False)
    topic_id: str = Field(index=True, nullable=False)
    from_state: LearningState = Field(nullable=False)
    to_state: LearningState = Field(nullable=False)
    trigger: str = Field(nullable=False, description="Reason/Event that triggered transition")
    evidence_payload: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Structured JSON metrics, quiz score, or error diagnostics",
    )
    actor_id: str = Field(nullable=False, description="User UUID or System Agent ID initiating transition")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
