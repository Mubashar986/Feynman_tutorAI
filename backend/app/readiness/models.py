from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlmodel import Column, Field, JSON, SQLModel


class ExamReadinessSnapshot(SQLModel, table=True):
    """
    Persisted historical snapshot of a student's calibrated exam readiness assessment (PRD Cap 20, FR-020, FR-025).
    """
    __tablename__ = "exam_readiness_snapshots"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    student_id: str = Field(foreign_key="users.id", index=True)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True)
    blueprint_id: Optional[str] = Field(default=None, foreign_key="exam_blueprints.id", index=True)

    # Composite & Pass Probability Metrics
    overall_readiness_score: float = Field(ge=0.0, le=100.0, description="Composite readiness percentage (0-100%)")
    pass_probability: float = Field(ge=0.0, le=1.0, description="Calibrated sigmoid pass probability (0.0 - 1.0)")
    is_ready_for_exam: bool = Field(default=False, description="True if readiness >= blueprint passing threshold")

    # 4 Multi-Factor Sub-Pillar Scores
    mastery_component: float = Field(ge=0.0, le=100.0, description="Blueprint-weighted BKT topic mastery score")
    retention_component: float = Field(ge=0.0, le=100.0, description="Continuous Ebbinghaus memory retrievability score")
    simulation_component: float = Field(ge=0.0, le=100.0, description="Recent timed mock simulation performance score")
    pacing_component: float = Field(ge=0.0, le=100.0, description="Response latency consistency & pacing score")

    # Detailed Analysis Snapshots (Stored as JSON)
    topic_breakdown: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    high_roi_recommendations: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
