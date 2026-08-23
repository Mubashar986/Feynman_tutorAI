from datetime import datetime
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.teach_back.models import (
    MasteryAssessmentLevel,
    TeachBackAudienceLevel,
)


# ==============================================================================
# 1. Rubric Dimension & Diagnostic Item Schemas
# ==============================================================================

class RubricCriterionScore(BaseModel):
    criterion_name: str = Field(..., description="Name of the rubric dimension evaluated")
    score: int = Field(..., ge=1, le=5, description="Score on 1-5 integer scale")
    weight: float = Field(..., ge=0.0, le=1.0, description="Normalized weight for this criterion (e.g. 0.30)")
    feedback: str = Field(..., description="Specific feedback on this criterion")


class PrerequisiteGap(BaseModel):
    prerequisite_topic_id: Optional[str] = Field(default=None, description="ID of missing syllabus topic if identified")
    prerequisite_title: str = Field(..., description="Name of the prerequisite concept or law missing")
    gap_description: str = Field(..., description="Why missing this prerequisite impacted the explanation")
    severity: str = Field(default="medium", description="Severity level: low, medium, high")


class RubricDimensionDetail(BaseModel):
    criterion_name: str
    weight: float
    description: str
    max_score: int = 5


# ==============================================================================
# 2. LLM Structured Output Target Schema (PRD FR-010, FR-017)
# ==============================================================================

class TeachBackLLMEvaluationOutput(BaseModel):
    """
    Pydantic V2 schema used as the strict validation target for LLMGateway.generate_structured().
    Enforces PRD Constraint #1 (No raw LLM text directly touches database state).
    """
    criteria_scores: List[RubricCriterionScore] = Field(
        ...,
        min_length=3,
        description="Detailed scores across standard rubric dimensions",
    )
    strengths: List[str] = Field(
        default=[],
        description="Key points and correct principles accurately explained",
    )
    misconceptions: List[str] = Field(
        default=[],
        description="Specific false statements, flawed logic, or confused terms",
    )
    missing_elements: List[str] = Field(
        default=[],
        description="Omitted learning objectives or key physical conditions",
    )
    prerequisite_gaps: List[PrerequisiteGap] = Field(
        default=[],
        description="Identified gaps in foundational prerequisite concepts",
    )
    pedagogical_feedback: str = Field(
        ...,
        description="Encouraging, actionable advice on how to improve the explanation",
    )
    model_correction_latex: Optional[str] = Field(
        default=None,
        description="Clear model correction snippet with KaTeX math notation",
    )


# ==============================================================================
# 3. Client Request & Response Schemas
# ==============================================================================

class TeachBackEvaluateRequest(BaseModel):
    exam_template_id: str = Field(..., description="Target exam curriculum ID")
    topic_id: str = Field(..., description="Target topic being explained")
    concept_title: Optional[str] = Field(None, max_length=200, description="Optional custom concept title")
    explanation: str = Field(
        ...,
        min_length=15,
        max_length=10000,
        description="Student explanation text or voice transcript (Feynman technique)",
    )
    audience_level: TeachBackAudienceLevel = Field(
        default=TeachBackAudienceLevel.HIGH_SCHOOL_PEER,
        description="Target audience complexity level",
    )


class TeachBackEvaluationResponse(BaseModel):
    id: str
    session_id: str
    topic_id: str
    concept_title: str
    audience_level: TeachBackAudienceLevel
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Composite weighted score 0-100")
    assessment_level: MasteryAssessmentLevel
    criteria_scores: List[RubricCriterionScore] = []
    strengths: List[str] = []
    misconceptions: List[str] = []
    missing_elements: List[str] = []
    prerequisite_gaps: List[PrerequisiteGap] = []
    pedagogical_feedback: str
    model_correction_latex: Optional[str] = None
    created_at: datetime

    @classmethod
    def from_db_models(
        cls,
        session_obj: Any,
        eval_obj: Any,
    ) -> "TeachBackEvaluationResponse":
        """Helper to parse JSON fields safely from SQLModel rows."""
        def safe_json_load(json_str: Optional[str], default_val: Any) -> Any:
            if not json_str:
                return default_val
            try:
                return json.loads(json_str)
            except Exception:
                return default_val

        raw_criteria = safe_json_load(eval_obj.criteria_scores_json, [])
        criteria = [RubricCriterionScore(**c) if isinstance(c, dict) else c for c in raw_criteria]

        raw_prereqs = safe_json_load(eval_obj.prerequisite_gaps_json, [])
        prereqs = [PrerequisiteGap(**p) if isinstance(p, dict) else p for p in raw_prereqs]

        return cls(
            id=eval_obj.id,
            session_id=session_obj.id,
            topic_id=session_obj.topic_id,
            concept_title=session_obj.concept_title,
            audience_level=session_obj.audience_level,
            overall_score=eval_obj.overall_score,
            assessment_level=eval_obj.assessment_level,
            criteria_scores=criteria,
            strengths=safe_json_load(eval_obj.strengths_json, []),
            misconceptions=safe_json_load(eval_obj.misconceptions_json, []),
            missing_elements=safe_json_load(eval_obj.missing_elements_json, []),
            prerequisite_gaps=prereqs,
            pedagogical_feedback=eval_obj.pedagogical_feedback,
            model_correction_latex=eval_obj.model_correction_latex,
            created_at=eval_obj.created_at,
        )


class TeachBackSessionResponse(BaseModel):
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    concept_title: str
    audience_level: TeachBackAudienceLevel
    created_at: datetime
    updated_at: datetime
    latest_score: Optional[float] = None
    latest_assessment_level: Optional[MasteryAssessmentLevel] = None

    class Config:
        from_attributes = True


class TeachBackSessionListResponse(BaseModel):
    sessions: List[TeachBackSessionResponse] = []
    total: int = 0


class TopicRubricResponse(BaseModel):
    topic_id: str
    topic_title: str
    description: str
    learning_objectives: List[Dict[str, Any]] = []
    prerequisites: List[Dict[str, Any]] = []
    rubric_dimensions: List[RubricDimensionDetail] = []
