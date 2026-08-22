from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.learning_state.models import LearningState


class StateTransitionRequest(BaseModel):
    """
    Request payload for executing a verified learning state transition.
    """
    exam_template_id: str = Field(..., description="Target exam template UUID")
    topic_id: str = Field(..., description="Target syllabus topic UUID")
    target_state: LearningState = Field(..., description="Desired target state in the FSM")
    trigger: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Event reason (e.g. ASSESSMENT_PASSED, SOCRATIC_REPAIR_COMPLETE)",
    )
    evidence_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured verification data (scores, failed items, misconception tags)",
    )
    mastery_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional updated mastery probability score",
    )
    student_id: Optional[str] = Field(
        default=None,
        description="Target student UUID (restricted to admin roles; defaults to current authenticated student)",
    )


class StudentLearningStateResponse(BaseModel):
    """
    Public response schema for student topic learning state.
    """
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    current_state: LearningState
    mastery_score: float
    consecutive_successes: int
    consecutive_failures: int
    last_transition_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StateTransitionLogResponse(BaseModel):
    """
    Public response schema for immutable audit log records.
    """
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    from_state: LearningState
    to_state: LearningState
    trigger: str
    evidence_payload: Dict[str, Any]
    actor_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExamLearningSummaryResponse(BaseModel):
    """
    Overview of all topic states for a student in a specific exam.
    """
    student_id: str
    exam_template_id: str
    total_topics: int
    mastered_count: int
    in_progress_count: int
    topic_states: List[StudentLearningStateResponse]
