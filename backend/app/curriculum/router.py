from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.database import get_db
from backend.app.auth.dependencies import require_role
from backend.app.auth.models import UserRole
from backend.app.curriculum.schemas import (
    ExamTemplateDetailResponse,
    ExamTemplateImportSchema,
    ExamTemplateResponse,
    SubjectDetailResponse,
    TopicDetailResponse,
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
