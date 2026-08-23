from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.revision.models import CardState, ReviewRating


# ==============================================================================
# 1. Spaced Review Card Schemas
# ==============================================================================

class ReviewCardResponse(BaseModel):
    id: str
    student_id: str
    exam_template_id: str
    topic_id: str
    question_id: str
    card_state: CardState
    repetitions: int
    interval_days: float
    ease_factor: float
    stability: float
    due_at: datetime
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewCardDetailResponse(ReviewCardResponse):
    question_prompt: str
    question_explanation: Optional[str] = None
    has_active_error: bool = False
    estimated_retrievability: float = 1.0


class DueCardsListResponse(BaseModel):
    total_due: int
    due_cards: List[ReviewCardDetailResponse] = []


# ==============================================================================
# 2. Review Submission Schemas
# ==============================================================================

class ReviewSubmitRequest(BaseModel):
    card_id: str = Field(..., description="Unique ID of the spaced review flashcard")
    rating: ReviewRating = Field(..., description="Review rating: 1 (AGAIN), 2 (HARD), 3 (GOOD), 4 (EASY)")


class ReviewSubmitResponse(BaseModel):
    card_id: str
    rating: ReviewRating
    prior_interval_days: float
    new_interval_days: float
    new_ease_factor: float
    new_due_at: datetime
    card_state: CardState
    message: str


# ==============================================================================
# 3. Analytics & Metrics Schemas
# ==============================================================================

class RevisionMetricsResponse(BaseModel):
    total_cards: int
    new_cards: int
    learning_cards: int
    review_cards: int
    due_today: int
    average_retention_rate: float


class CardSeedRequest(BaseModel):
    exam_template_id: str = Field(..., description="Exam template ID to seed flashcards from")
    topic_id: Optional[str] = Field(None, description="Optional topic ID filter")
