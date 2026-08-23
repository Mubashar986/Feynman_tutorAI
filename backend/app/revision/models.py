from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


class ReviewRating(int, Enum):
    """
    Active Recall review performance rating (1 to 4 scale).
    """
    AGAIN = 1  # Total blackout / incorrect recall
    HARD = 2   # Recalled with significant hesitation / difficulty
    GOOD = 3   # Successful recall with normal effort
    EASY = 4   # Instantaneous, effortless recall


class CardState(str, Enum):
    """
    Spaced repetition lifecycle state of a learning flashcard.
    """
    NEW = "new"              # Fresh card, never reviewed
    LEARNING = "learning"    # Initial acquisition phase (1-2 repetitions)
    REVIEW = "review"        # Regular retention interval expansion
    RELEARNING = "relearning"# Failed card returning from memory lapse


class SpacedReviewCard(SQLModel, table=True):
    """
    Individual Spaced Repetition flashcard tracking long-term memory stability (PRD FR-007, Cap 7, §15).
    """
    __tablename__ = "spaced_review_cards"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
    )
    student_id: str = Field(foreign_key="users.id", index=True)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True)
    topic_id: str = Field(foreign_key="topics.id", index=True)
    question_id: str = Field(foreign_key="questions.id", index=True)

    card_state: CardState = Field(default=CardState.NEW, index=True)
    repetitions: int = Field(default=0, description="Consecutive successful recall count")
    interval_days: float = Field(default=0.0, description="Current scheduled review interval in days")
    ease_factor: float = Field(default=2.50, description="SM-2 Ease Factor (clamped 1.30 - 2.80)")
    stability: float = Field(default=1.0, description="Estimated memory stability in days")
    difficulty: float = Field(default=5.0, description="Inherent item difficulty metric")

    due_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        description="Timestamp when this item becomes due for spaced review",
    )
    last_reviewed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of most recent review submission",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewLog(SQLModel, table=True):
    """
    Immutable audit log recording every retrieval practice telemetry event.
    """
    __tablename__ = "review_logs"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
    )
    card_id: str = Field(foreign_key="spaced_review_cards.id", index=True)
    student_id: str = Field(foreign_key="users.id", index=True)

    rating: ReviewRating = Field(description="Review quality rating (1 to 4)")
    prior_interval_days: float = Field(description="Scheduled interval before this review")
    new_interval_days: float = Field(description="New scheduled interval after calculation")
    prior_ease_factor: float = Field(description="Ease factor prior to review")
    new_ease_factor: float = Field(description="Updated ease factor after review")

    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
