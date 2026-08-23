from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.mastery.models import MasteryStatus
from backend.app.questions.models import DifficultyLevel


# ==============================================================================
# 1. Attempt Recording Schemas
# ==============================================================================

class RecordAttemptRequest(BaseModel):
    question_id: str = Field(..., description="ID of the question attempted")
    selected_option_key: Optional[str] = Field(None, description="Selected option letter e.g. A, B, C, D")
    is_correct: bool = Field(..., description="Whether the student answered correctly")
    time_spent_seconds: Optional[int] = Field(None, ge=0, description="Time spent solving the question in seconds")


class MasteryUpdateResponse(BaseModel):
    student_id: str
    exam_template_id: str
    topic_id: str
    question_id: str
    is_correct: bool
    prior_mastery_probability: float
    posterior_mastery_probability: float
    status: MasteryStatus
    current_difficulty: DifficultyLevel
    total_attempts: int
    correct_attempts: int
    current_streak: int
    best_streak: int
    updated_at: datetime


# ==============================================================================
# 2. Topic Mastery Profile Schemas
# ==============================================================================

class StudentTopicMasteryResponse(BaseModel):
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    mastery_probability: float
    status: MasteryStatus
    current_difficulty: DifficultyLevel
    total_attempts: int
    correct_attempts: int
    current_streak: int
    best_streak: int
    last_attempt_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicMasteryListResponse(BaseModel):
    total: int
    topic_masteries: List[StudentTopicMasteryResponse] = []
