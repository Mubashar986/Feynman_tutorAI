from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TopicReadinessDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic_id: str
    topic_title: str
    target_weight: float = Field(ge=0.0, le=1.0, description="Blueprint weight (0.0 - 1.0)")
    mastery_level: float = Field(ge=0.0, le=1.0, description="BKT latent mastery level (0.0 - 1.0)")
    retention_level: float = Field(ge=0.0, le=1.0, description="Ebbinghaus retrievability level (0.0 - 1.0)")
    composite_topic_score: float = Field(ge=0.0, le=100.0, description="Combined topic score percentage (0-100%)")
    marginal_roi_score: float = Field(ge=0.0, description="Marginal score gain per hour of study")


class ReadinessComponentBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mastery_score: float = Field(ge=0.0, le=100.0, description="Blueprint-weighted BKT topic mastery score (0-100%)")
    mastery_weight: float = Field(default=0.40, description="Pillar weight in composite formula")

    retention_score: float = Field(ge=0.0, le=100.0, description="Continuous Ebbinghaus memory retrievability score (0-100%)")
    retention_weight: float = Field(default=0.20, description="Pillar weight in composite formula")

    simulation_score: float = Field(ge=0.0, le=100.0, description="Recent timed mock exam performance score (0-100%)")
    simulation_weight: float = Field(default=0.25, description="Pillar weight in composite formula")

    pacing_score: float = Field(ge=0.0, le=100.0, description="Response latency consistency & pacing score (0-100%)")
    pacing_weight: float = Field(default=0.15, description="Pillar weight in composite formula")


class HighRoiTopicRecommendation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic_id: str
    topic_title: str
    target_weight: float = Field(description="Exam blueprint weight percentage")
    current_mastery_pct: float = Field(description="Current BKT mastery percentage")
    current_retention_pct: float = Field(description="Current memory retrievability percentage")
    potential_score_gain: float = Field(description="Estimated point gain on exam from mastering this topic")
    reason: str = Field(description="Pedagogical justification for why this topic has highest study ROI")


class ExamReadinessReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exam_template_id: str
    exam_title: str
    blueprint_id: Optional[str] = None
    overall_readiness_score: float = Field(ge=0.0, le=100.0, description="Composite Exam Readiness Score (0-100%)")
    pass_probability: float = Field(ge=0.0, le=1.0, description="Calibrated sigmoid pass probability (0.0 - 1.0)")
    passing_percentage_threshold: float = Field(default=60.0, description="Blueprint passing threshold score")
    is_ready_for_exam: bool = Field(description="True if overall readiness >= passing threshold")
    readiness_tier: str = Field(description="'High Readiness' (>=80%), 'Moderate Readiness' (60-79%), or 'Needs Remediation' (<60%)")

    components: ReadinessComponentBreakdown
    topic_breakdown: List[TopicReadinessDetail]
    high_roi_recommendations: List[HighRoiTopicRecommendation]
    calculated_at: datetime


class ReadinessHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    overall_readiness_score: float
    pass_probability: float
    mastery_component: float
    retention_component: float
    simulation_component: float
    pacing_component: float
    is_ready_for_exam: bool
    created_at: datetime


class ReadinessHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exam_template_id: str
    history: List[ReadinessHistoryItem]
    total_snapshots: int
