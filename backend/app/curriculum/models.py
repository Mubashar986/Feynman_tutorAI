from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


class ExamBoard(str, Enum):
    CAMBRIDGE = "Cambridge International"
    COLLEGE_BOARD = "College Board"
    AQA = "AQA"
    IB = "IB"
    AAMC = "AAMC"


class BloomLevel(str, Enum):
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"
    EVALUATE = "Evaluate"
    CREATE = "Create"


class TopicDifficulty(str, Enum):
    FOUNDATIONAL = "foundational"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExamTemplate(SQLModel, table=True):
    """
    Master definition of an exam specification and its syllabus (PRD §5.1, FR-002).
    Shared across multiple students with isolated progress state.
    """
    __tablename__ = "exam_templates"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    title: str = Field(index=True, nullable=False)
    code: str = Field(unique=True, index=True, nullable=False)  # e.g. "9702", "AP-CALC-BC"
    board: ExamBoard = Field(default=ExamBoard.CAMBRIDGE, nullable=False)
    description: str = Field(default="", nullable=False)
    difficulty_level: str = Field(default="Advanced Placement / A-Level", nullable=False)
    icon_name: str = Field(default="BookOpen", nullable=False)
    total_duration_minutes: int = Field(default=180, nullable=False)
    passing_score_percentage: float = Field(default=70.0, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Subject(SQLModel, table=True):
    """
    Major academic subject division within an exam template (e.g., Mechanics, Electromagnetism).
    """
    __tablename__ = "subjects"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    exam_template_id: str = Field(
        foreign_key="exam_templates.id",
        index=True,
        nullable=False,
    )
    title: str = Field(nullable=False)
    order: int = Field(default=0, nullable=False)
    description: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Section(SQLModel, table=True):
    """
    Optional conceptual section grouping within a subject.
    """
    __tablename__ = "sections"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    subject_id: str = Field(
        foreign_key="subjects.id",
        index=True,
        nullable=False,
    )
    title: str = Field(nullable=False)
    order: int = Field(default=0, nullable=False)
    description: str = Field(default="", nullable=False)


class Topic(SQLModel, table=True):
    """
    Atomic syllabus unit where learning state and mastery probability are calculated.
    """
    __tablename__ = "topics"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    subject_id: str = Field(
        foreign_key="subjects.id",
        index=True,
        nullable=False,
    )
    section_id: Optional[str] = Field(
        default=None,
        foreign_key="sections.id",
        index=True,
        nullable=True,
    )
    title: str = Field(nullable=False)
    order: int = Field(default=0, nullable=False)
    difficulty: TopicDifficulty = Field(
        default=TopicDifficulty.INTERMEDIATE,
        nullable=False,
    )
    estimated_hours: float = Field(default=4.0, nullable=False)
    importance_weight: float = Field(default=1.0, nullable=False)
    description: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Subtopic(SQLModel, table=True):
    """
    Optional subtopic breakdown within a topic.
    """
    __tablename__ = "subtopics"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    topic_id: str = Field(
        foreign_key="topics.id",
        index=True,
        nullable=False,
    )
    title: str = Field(nullable=False)
    order: int = Field(default=0, nullable=False)
    description: str = Field(default="", nullable=False)


class LearningObjective(SQLModel, table=True):
    """
    Fine-grained competency statement tagged with Bloom taxonomy level and LaTeX equations.
    """
    __tablename__ = "learning_objectives"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    topic_id: str = Field(
        foreign_key="topics.id",
        index=True,
        nullable=False,
    )
    subtopic_id: Optional[str] = Field(
        default=None,
        foreign_key="subtopics.id",
        index=True,
        nullable=True,
    )
    code: str = Field(index=True, nullable=False)  # e.g. "9702.4.1"
    description: str = Field(nullable=False)
    formula_latex: Optional[str] = Field(default=None, nullable=True)
    bloom_level: BloomLevel = Field(
        default=BloomLevel.UNDERSTAND,
        nullable=False,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TopicPrerequisite(SQLModel, table=True):
    """
    Directed dependency edge establishing prerequisite order between two topics.
    """
    __tablename__ = "topic_prerequisites"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    topic_id: str = Field(
        foreign_key="topics.id",
        index=True,
        nullable=False,
    )
    prerequisite_topic_id: str = Field(
        foreign_key="topics.id",
        index=True,
        nullable=False,
    )
    is_mandatory: bool = Field(default=True, nullable=False)
