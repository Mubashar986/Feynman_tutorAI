from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.curriculum.models import (
    BloomLevel,
    ExamBoard,
    TopicDifficulty,
)


# ==============================================================================
# 1. Learning Objective Schemas
# ==============================================================================

class LearningObjectiveBase(BaseModel):
    code: str = Field(..., description="Unique syllabus code, e.g., '9702.4.1'")
    description: str = Field(..., description="Competency statement")
    formula_latex: Optional[str] = Field(None, description="LaTeX formula if applicable")
    bloom_level: BloomLevel = Field(default=BloomLevel.UNDERSTAND)


class LearningObjectiveCreate(LearningObjectiveBase):
    topic_id: str
    subtopic_id: Optional[str] = None


class LearningObjectiveResponse(LearningObjectiveBase):
    id: str
    topic_id: str
    subtopic_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearningObjectiveImportSchema(LearningObjectiveBase):
    pass


# ==============================================================================
# 2. Topic & Prerequisite Schemas
# ==============================================================================

class TopicPrerequisiteResponse(BaseModel):
    id: str
    topic_id: str
    prerequisite_topic_id: str
    prerequisite_topic_title: Optional[str] = None
    is_mandatory: bool = True

    class Config:
        from_attributes = True


class TopicPrerequisiteImportSchema(BaseModel):
    prerequisite_topic_code_or_title: str
    is_mandatory: bool = True


class SubtopicResponse(BaseModel):
    id: str
    topic_id: str
    title: str
    order: int
    description: str

    class Config:
        from_attributes = True


class SubtopicImportSchema(BaseModel):
    title: str
    order: int = 0
    description: str = ""


class TopicBase(BaseModel):
    title: str
    order: int = 0
    difficulty: TopicDifficulty = TopicDifficulty.INTERMEDIATE
    estimated_hours: float = 4.0
    importance_weight: float = 1.0
    description: str = ""


class TopicCreate(TopicBase):
    subject_id: str
    section_id: Optional[str] = None


class TopicResponse(TopicBase):
    id: str
    subject_id: str
    section_id: Optional[str] = None
    objective_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicDetailResponse(TopicBase):
    id: str
    subject_id: str
    section_id: Optional[str] = None
    subtopics: List[SubtopicResponse] = []
    objectives: List[LearningObjectiveResponse] = []
    prerequisites: List[TopicPrerequisiteResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicImportSchema(TopicBase):
    code: Optional[str] = None  # Optional identifier for prerequisite linking
    subtopics: List[SubtopicImportSchema] = []
    objectives: List[LearningObjectiveImportSchema] = []
    prerequisites: List[TopicPrerequisiteImportSchema] = []


# ==============================================================================
# 3. Subject & Section Schemas
# ==============================================================================

class SectionResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    order: int
    description: str

    class Config:
        from_attributes = True


class SectionImportSchema(BaseModel):
    title: str
    order: int = 0
    description: str = ""


class SubjectBase(BaseModel):
    title: str
    order: int = 0
    description: str = ""


class SubjectCreate(SubjectBase):
    exam_template_id: str


class SubjectResponse(SubjectBase):
    id: str
    exam_template_id: str
    topic_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubjectDetailResponse(SubjectBase):
    id: str
    exam_template_id: str
    topics: List[TopicDetailResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubjectImportSchema(SubjectBase):
    sections: List[SectionImportSchema] = []
    topics: List[TopicImportSchema] = []


# ==============================================================================
# 4. Exam Template Schemas
# ==============================================================================

class ExamTemplateBase(BaseModel):
    title: str
    code: str
    board: ExamBoard = ExamBoard.CAMBRIDGE
    description: str = ""
    difficulty_level: str = "Advanced Placement / A-Level"
    icon_name: str = "BookOpen"
    total_duration_minutes: int = 180
    passing_score_percentage: float = 70.0


class ExamTemplateCreate(ExamTemplateBase):
    pass


class ExamTemplateResponse(ExamTemplateBase):
    id: str
    subject_count: int = 0
    topic_count: int = 0
    objective_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExamTemplateDetailResponse(ExamTemplateResponse):
    subjects: List[SubjectDetailResponse] = []


class ExamTemplateImportSchema(ExamTemplateBase):
    subjects: List[SubjectImportSchema] = []


# ==============================================================================
# 5. Curriculum DAG & Prerequisite Engine Schemas
# ==============================================================================

class DAGNodeResponse(BaseModel):
    id: str
    title: str
    subject_id: str
    difficulty: str
    estimated_hours: float
    importance_weight: float
    in_degree: int
    out_degree: int
    level: int
    prerequisite_ids: List[str] = []
    dependent_ids: List[str] = []


class DAGEdgeResponse(BaseModel):
    id: str
    source: str  # Prerequisite topic ID
    target: str  # Dependent topic ID
    is_mandatory: bool = True


class DAGGraphResponse(BaseModel):
    exam_template_id: str
    exam_title: str
    is_acyclic: bool
    cycle_path: Optional[List[str]] = None
    total_nodes: int
    total_edges: int
    root_topic_ids: List[str] = []
    terminal_topic_ids: List[str] = []
    nodes: List[DAGNodeResponse] = []
    edges: List[DAGEdgeResponse] = []


class DAGValidationResponse(BaseModel):
    exam_template_id: str
    exam_title: str
    is_valid: bool
    has_cycles: bool
    cycle_path: Optional[List[str]] = None
    total_topics: int
    total_prerequisite_edges: int
    root_topic_ids: List[str] = []
    terminal_topic_ids: List[str] = []
    max_depth_level: int = 0


class LearningPathNodeResponse(BaseModel):
    sequence_number: int
    topic_id: str
    title: str
    subject_id: str
    difficulty: str
    estimated_hours: float
    level: int
    prerequisite_ids: List[str] = []


class LearningPathResponse(BaseModel):
    exam_template_id: str
    exam_title: str
    total_topics: int
    learning_path: List[LearningPathNodeResponse] = []


class TopicUnlockStatusResponse(BaseModel):
    topic_id: str
    title: str
    subject_id: str
    difficulty: str
    level: int
    current_learning_state: str
    unlock_status: str  # "locked" | "unlocked" | "mastered"
    is_unlocked: bool
    missing_prerequisite_ids: List[str] = []
    missing_prerequisite_titles: List[str] = []


class BlockerNodeResponse(BaseModel):
    topic_id: str
    title: str
    difficulty: str
    level: int
    current_state: str
    is_direct_prerequisite: bool


class TopicBlockerReportResponse(BaseModel):
    target_topic_id: str
    target_topic_title: str
    exam_template_id: str
    student_id: str
    is_unlocked: bool
    total_unmastered_ancestors: int
    blockers: List[BlockerNodeResponse] = []

