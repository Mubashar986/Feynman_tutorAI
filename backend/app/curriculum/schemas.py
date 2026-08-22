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
