from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.database import get_db
from backend.app.auth.dependencies import get_current_user, require_role
from backend.app.auth.models import User, UserRole
from backend.app.learning_state.router import resolve_student_id
from backend.app.curriculum.dag import TopicDAGService
from backend.app.curriculum.schemas import (
    DAGGraphResponse,
    DAGValidationResponse,
    ExamTemplateDetailResponse,
    ExamTemplateImportSchema,
    ExamTemplateResponse,
    LearningPathResponse,
    SubjectDetailResponse,
    TopicBlockerReportResponse,
    TopicDetailResponse,
    TopicUnlockStatusResponse,
)
from backend.app.curriculum.service import (
    CurriculumService,
    SyllabusParserService,
)

router = APIRouter(prefix="/exam-templates", tags=["Exam Templates & Curriculum"])



@router.get(
    "",
    response_model=List[ExamTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="List all active exam templates",
)
async def list_exam_templates(
    session: AsyncSession = Depends(get_db),
) -> List[ExamTemplateResponse]:
    """
    Returns the catalog of all available examination templates with subject and topic counts (PRD §5.1, FR-002).
    """
    return await CurriculumService.list_exam_templates(session)


@router.get(
    "/{template_id}",
    response_model=ExamTemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get exam template by ID or code",
)
async def get_exam_template(
    template_id: str,
    session: AsyncSession = Depends(get_db),
) -> ExamTemplateResponse:
    """
    Retrieves metadata and configuration for a specific examination template.
    """
    template = await CurriculumService.get_exam_template(session, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam template '{template_id}' not found",
        )
    return ExamTemplateResponse.model_validate(template)


@router.get(
    "/{template_id}/syllabus",
    response_model=List[SubjectDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get complete hierarchical syllabus tree for an exam",
)
async def get_syllabus_tree(
    template_id: str,
    session: AsyncSession = Depends(get_db),
) -> List[SubjectDetailResponse]:
    """
    Returns the nested syllabus tree (Subjects -> Topics -> Subtopics & Learning Objectives & Prerequisites)
    for rendering in the syllabus explorer UI.
    """
    return await CurriculumService.get_syllabus_tree(session, template_id)


@router.get(
    "/topics/{topic_id}",
    response_model=TopicDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get topic details with objectives and prerequisites",
)
async def get_topic_detail(
    topic_id: str,
    session: AsyncSession = Depends(get_db),
) -> TopicDetailResponse:
    """
    Retrieves topic information including subtopics, LaTeX formulas, Bloom levels, and prerequisite links.
    """
    topic = await CurriculumService.get_topic_detail(session, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{topic_id}' not found",
        )
    return topic


@router.post(
    "/import",
    response_model=ExamTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import complete nested curriculum blueprint (Admin/Instructor only)",
    dependencies=[Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
async def import_exam_blueprint(
    blueprint: ExamTemplateImportSchema,
    session: AsyncSession = Depends(get_db),
) -> ExamTemplateResponse:
    """
    Parses and persists a full nested curriculum blueprint (Exam -> Subjects -> Topics -> Objectives & Prerequisites)
    in a single atomic database transaction.
    """
    template = await SyllabusParserService.import_blueprint(session, blueprint)
    return ExamTemplateResponse.model_validate(template)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an exam template and its syllabus (Admin only)",
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def delete_exam_template(
    template_id: str,
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently removes an exam template and cascades deletions to all associated subjects, topics, and objectives.
    """
    deleted = await CurriculumService.delete_exam_template(session, template_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam template '{template_id}' not found",
        )


# ==============================================================================
# Curriculum DAG & Prerequisite Engine Endpoints (PRD §5.1, §8, FR-003)
# ==============================================================================

@router.get(
    "/{template_id}/dag",
    response_model=DAGGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete topic dependency graph with depth levels and connectivity",
)
async def get_exam_dag(
    template_id: str,
    session: AsyncSession = Depends(get_db),
) -> DAGGraphResponse:
    """
    Returns the visual Directed Acyclic Graph (DAG) for an exam template including node depth levels,
    in-degrees, out-degrees, and mandatory prerequisite edges for DAG visualization.
    """
    return await TopicDAGService.get_dag_graph(session, template_id)


@router.get(
    "/{template_id}/learning-path",
    response_model=LearningPathResponse,
    status_code=status.HTTP_200_OK,
    summary="Get canonical topologically sorted recommended learning sequence",
)
async def get_learning_path(
    template_id: str,
    session: AsyncSession = Depends(get_db),
) -> LearningPathResponse:
    """
    Computes a linear topological sequence of topics guaranteeing that all prerequisites are completed
    prior to dependent topics.
    """
    return await TopicDAGService.get_learning_path(session, template_id)


@router.get(
    "/{template_id}/unlocked-topics",
    response_model=List[TopicUnlockStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get unlocked vs locked topic statuses for a student",
)
async def get_unlocked_topics(
    template_id: str,
    student_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[TopicUnlockStatusResponse]:
    """
    Evaluates which topics are currently LOCKED, UNLOCKED, or MASTERED for the given student
    based on their recorded learning state history.
    """
    target_student_id = resolve_student_id(current_user, student_id)
    return await TopicDAGService.get_student_unlocked_topics(session, template_id, target_student_id)


@router.get(
    "/{template_id}/topics/{topic_id}/blockers",
    response_model=TopicBlockerReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ancestral prerequisite blockers for a struggling student on a topic",
)
async def get_topic_prerequisite_blockers(
    template_id: str,
    topic_id: str,
    student_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TopicBlockerReportResponse:
    """
    Performs reverse graph reachability analysis to extract all unmastered ancestral prerequisites
    preventing a student from mastering the target topic.
    """
    target_student_id = resolve_student_id(current_user, student_id)
    return await TopicDAGService.get_topic_blocker_report(session, template_id, topic_id, target_student_id)


@router.post(
    "/{template_id}/validate-dag",
    response_model=DAGValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Audit curriculum DAG integrity and detect circular dependencies (Admin/Instructor)",
    dependencies=[Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
async def validate_exam_dag(
    template_id: str,
    session: AsyncSession = Depends(get_db),
) -> DAGValidationResponse:
    """
    Audits the exam template's topic prerequisite graph for cycles, connectivity, and depth levels.
    """
    return await TopicDAGService.validate_exam_dag(session, template_id)

