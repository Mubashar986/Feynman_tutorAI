from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.teach_back.schemas import (
    TeachBackEvaluateRequest,
    TeachBackEvaluationResponse,
    TeachBackSessionListResponse,
    TopicRubricResponse,
)
from backend.app.teach_back.service import TeachBackService

router = APIRouter(tags=["Teach-Back Mode & Rubric Evaluator"])


@router.post(
    "/teach-back/evaluate",
    response_model=TeachBackEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate student concept explanation using Feynman rubric (PRD FR-017, Cap 17)",
)
@router.post(
    "/modes/teach-back/evaluate",
    response_model=TeachBackEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="PRD standard alias endpoint for Teach-Back evaluation",
    include_in_schema=False,
)
async def evaluate_teach_back(
    request_in: TeachBackEvaluateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TeachBackEvaluationResponse:
    """
    Evaluates a student explanation against multi-criterion rubrics:
    Accuracy (30%), Completeness (25%), Intuition (20%), KaTeX Rigor (15%), Prereqs (10%).
    Returns scores, identified misconceptions, and missing prerequisite gaps.
    """
    try:
        return await TeachBackService.evaluate_explanation(
            session=session,
            student_id=current_user.id,
            request_in=request_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Teach-Back evaluation failed: {str(e)}",
        )


@router.get(
    "/teach-back/rubric/{topic_id}",
    response_model=TopicRubricResponse,
    status_code=status.HTTP_200_OK,
    summary="Get grounded rubric expectations and objectives for a topic",
)
async def get_topic_rubric(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TopicRubricResponse:
    """
    Returns the syllabus learning objectives, prerequisites, and rubric criteria for a topic.
    """
    try:
        return await TeachBackService.get_topic_rubric(
            session=session,
            topic_id=topic_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/teach-back/sessions",
    response_model=TeachBackSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List past Teach-Back sessions and scores for the current student",
)
async def list_teach_back_sessions(
    exam_template_id: Optional[str] = Query(None, description="Optional exam filter"),
    limit: int = Query(20, ge=1, le=100, description="Max sessions to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TeachBackSessionListResponse:
    """
    Lists historical Teach-Back explanation attempts and scores for the authenticated student.
    """
    return await TeachBackService.list_student_sessions(
        session=session,
        student_id=current_user.id,
        exam_template_id=exam_template_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/teach-back/sessions/{session_id}",
    response_model=TeachBackEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full evaluation report for a specific Teach-Back session",
)
async def get_session_evaluation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TeachBackEvaluationResponse:
    """
    Retrieves full evaluation report including rubric criteria scores, strengths, and misconceptions.
    Enforces student isolation (PRD Constraint #2).
    """
    try:
        return await TeachBackService.get_session_evaluation(
            session=session,
            student_id=current_user.id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
