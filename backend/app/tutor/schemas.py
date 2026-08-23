from datetime import datetime
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.tutor.models import HintLevel, TutorRole


# ==============================================================================
# 1. Session Schemas
# ==============================================================================

class TutorSessionCreate(BaseModel):
    exam_template_id: str = Field(..., description="Target exam curriculum ID")
    topic_id: str = Field(..., description="Current topic under review")
    question_id: Optional[str] = Field(None, description="Optional question context if asking about a specific item")
    title: Optional[str] = Field(None, max_length=150, description="Optional session title")


class TutorSessionResponse(BaseModel):
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    question_id: Optional[str] = None
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# 2. Message & Dialogue Turn Schemas
# ==============================================================================

class TutorMessageResponse(BaseModel):
    id: str
    session_id: str
    role: TutorRole
    content: str
    hint_level: Optional[HintLevel] = None
    citations: List[Dict[str, Any]] = []
    created_at: datetime

    @classmethod
    def from_orm_model(cls, message) -> "TutorMessageResponse":
        citations_list = []
        if message.citations_json:
            try:
                citations_list = json.loads(message.citations_json)
            except Exception:
                citations_list = []
        return cls(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            hint_level=message.hint_level,
            citations=citations_list,
            created_at=message.created_at,
        )


class TutorSessionDetailResponse(TutorSessionResponse):
    messages: List[TutorMessageResponse] = []


class SocraticPromptRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Student question or response to tutor")
    hint_level: HintLevel = Field(default=HintLevel.CONCEPTUAL, description="Desired scaffolding depth")


class SocraticResponse(BaseModel):
    session_id: str
    topic_id: str
    message: TutorMessageResponse
    citations: List[Dict[str, Any]] = []
