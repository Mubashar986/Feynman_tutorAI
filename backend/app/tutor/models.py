from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


# ==============================================================================
# 1. Enums: Roles & Socratic Scaffolding Hint Levels (PRD §14.5, FR-008)
# ==============================================================================

class TutorRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class HintLevel(str, Enum):
    """
    Socratic 4-Tier Scaffolding Hierarchy.
    """
    CONCEPTUAL = "conceptual"    # Tier 1: Reminds the student of definitions and physical/math laws
    STRATEGIC = "strategic"      # Tier 2: Suggests mathematical strategy without executing algebra
    STEP = "step"                # Tier 3: Outlines specific algebraic equation setup with variables
    EXPLANATION = "explanation"  # Tier 4: Comprehensive solution derivation for post-exam review


# ==============================================================================
# 2. Database Models: Sessions & Messages
# ==============================================================================

class TutorSessionBase(SQLModel):
    student_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    exam_template_id: str = Field(foreign_key="exam_templates.id", index=True, nullable=False)
    topic_id: str = Field(foreign_key="topics.id", index=True, nullable=False)
    question_id: Optional[str] = Field(default=None, foreign_key="questions.id", index=True)
    title: str = Field(default="Socratic Tutoring Session", max_length=150)
    is_active: bool = Field(default=True, index=True)


class TutorSession(TutorSessionBase, table=True):
    """
    Conversational state boundary for 1-on-1 Socratic dialogue (PRD FR-008, Cap 4).
    Enforces student-exam isolation (Constraint #2).
    """
    __tablename__ = "tutor_sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class TutorMessageBase(SQLModel):
    session_id: str = Field(foreign_key="tutor_sessions.id", index=True, nullable=False)
    role: TutorRole = Field(index=True, nullable=False)
    content: str = Field(description="Message body rendered with KaTeX markdown")
    hint_level: Optional[HintLevel] = Field(default=HintLevel.CONCEPTUAL)
    citations_json: Optional[str] = Field(default=None, description="Serialized JSON array of source citations")


class TutorMessage(TutorMessageBase, table=True):
    """
    Individual conversational turn within a Socratic tutoring dialogue.
    """
    __tablename__ = "tutor_messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
