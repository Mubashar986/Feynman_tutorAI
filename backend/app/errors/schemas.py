from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.errors.models import ErrorCategory, RepairStatus


# ==============================================================================
# 1. Misconception Schemas
# ==============================================================================

class MisconceptionResponse(BaseModel):
    id: str
    topic_id: str
    code: str
    title: str
    description: str
    remediation_guidance: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 2. Student Error Log Schemas
# ==============================================================================

class StudentErrorLogResponse(BaseModel):
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    question_id: str
    attempt_id: Optional[str] = None
    misconception_id: Optional[str] = None
    error_category: ErrorCategory
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    distractor_rationale: Optional[str] = None
    repair_status: RepairStatus
    occurrence_count: int
    first_detected_at: datetime
    last_occurred_at: datetime
    repaired_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentErrorDetailResponse(StudentErrorLogResponse):
    question_prompt: Optional[str] = None
    question_explanation: Optional[str] = None
    misconception: Optional[MisconceptionResponse] = None


class ErrorListResponse(BaseModel):
    total: int
    active_count: int
    repaired_count: int
    errors: List[StudentErrorDetailResponse] = []


class RepairErrorRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Optional remediation notes from student or tutor")
