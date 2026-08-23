from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.questions.models import QuestionType
from backend.app.simulation.models import SimulationStatus


# ==============================================================================
# 1. Blueprint Schemas (PRD FR-014)
# ==============================================================================

class BlueprintTopicWeightInput(BaseModel):
    topic_id: str = Field(..., description="Target syllabus topic ID")
    target_weight: float = Field(..., ge=0.0, le=1.0, description="Target proportion e.g. 0.30")


class BlueprintCreateRequest(BaseModel):
    exam_template_id: str = Field(..., description="Parent exam template ID")
    code: str = Field(..., max_length=50, description="Unique blueprint code e.g. '9702_PAPER_1'")
    title: str = Field(..., max_length=200, description="Descriptive title")
    description: Optional[str] = None
    duration_minutes: int = Field(90, ge=1, le=360, description="Time limit in minutes")
    total_questions: int = Field(40, ge=1, le=200, description="Number of questions on paper")
    total_marks: float = Field(40.0, ge=1.0, description="Total possible marks")
    passing_percentage: float = Field(60.0, ge=0.0, le=100.0)
    topic_distributions: List[BlueprintTopicWeightInput] = Field(
        default_factory=list,
        description="List of topic weight allocations",
    )


class BlueprintTopicDistributionResponse(BaseModel):
    id: str
    topic_id: str
    topic_title: Optional[str] = None
    target_weight: float
    target_question_count: int

    class Config:
        from_attributes = True


class BlueprintResponse(BaseModel):
    id: str
    exam_template_id: str
    code: str
    title: str
    description: Optional[str] = None
    duration_minutes: int
    total_questions: int
    total_marks: float
    passing_percentage: float
    topic_distributions: List[BlueprintTopicDistributionResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 2. Simulation Session & Sanitized Question Delivery Schemas
# ==============================================================================

class SimulationStartRequest(BaseModel):
    blueprint_id: str = Field(..., description="Exam blueprint to simulate")


class SanitizedOption(BaseModel):
    """
    Sanitized option view for exam taking (strips correct answer flag).
    """
    id: str
    option_key: str
    option_text: str
    order: int


class SanitizedQuestion(BaseModel):
    """
    Sanitized question view for exam taking (strips correct answers and explanations).
    """
    id: str
    topic_id: str
    topic_title: Optional[str] = None
    prompt: str
    question_type: QuestionType
    marks: float
    options: List[SanitizedOption] = []


class SimulationSessionResponse(BaseModel):
    id: str
    blueprint_id: str
    exam_template_id: str
    status: SimulationStatus
    duration_minutes: int
    total_questions: int
    total_marks: float
    started_at: datetime
    expires_at: datetime
    time_remaining_seconds: int
    questions: List[SanitizedQuestion] = []
    saved_answers: Dict[str, Any] = {}


class SaveAnswerRequest(BaseModel):
    question_id: str = Field(..., description="Target question ID")
    selected_option_id: Optional[str] = Field(None, description="Selected option ID for MCQ")
    numerical_response: Optional[float] = Field(None, description="Numerical value response")
    text_response: Optional[str] = Field(None, description="Free response or derivation text")


class SaveAnswerResponse(BaseModel):
    session_id: str
    question_id: str
    saved_at: datetime
    status: str = "saved"


# ==============================================================================
# 3. Post-Exam Scorecard & Topic Breakdown Schemas (PRD FR-020)
# ==============================================================================

class QuestionResultDetail(BaseModel):
    question_id: str
    topic_id: str
    topic_title: Optional[str] = None
    prompt: str
    question_type: QuestionType
    selected_option_id: Optional[str] = None
    selected_option_key: Optional[str] = None
    correct_option_id: Optional[str] = None
    correct_option_key: Optional[str] = None
    student_numerical: Optional[float] = None
    correct_numerical: Optional[float] = None
    is_correct: bool
    marks_awarded: float
    marks_available: float
    explanation: Optional[str] = None


class TopicPerformanceSummary(BaseModel):
    topic_id: str
    topic_title: str
    total_questions: int
    total_marks: float
    earned_marks: float
    percentage: float


class SimulationSubmitResponse(BaseModel):
    session_id: str
    blueprint_id: str
    status: SimulationStatus
    total_marks_available: float
    earned_marks: float
    percentage_score: float
    is_passed: bool
    time_spent_seconds: int
    topic_breakdown: List[TopicPerformanceSummary] = []
    question_results: List[QuestionResultDetail] = []
    submitted_at: datetime


class SimulationSessionSummary(BaseModel):
    id: str
    blueprint_id: str
    blueprint_title: Optional[str] = None
    status: SimulationStatus
    total_marks_available: Optional[float] = None
    earned_marks: Optional[float] = None
    percentage_score: Optional[float] = None
    is_passed: Optional[bool] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SimulationSessionListResponse(BaseModel):
    simulations: List[SimulationSessionSummary] = []
    total: int = 0
