from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.mastery.schemas import (
    MasteryUpdateResponse,
    RecordAttemptRequest,
    StudentTopicMasteryResponse,
    TopicMasteryListResponse,
)
from backend.app.mastery.service import MasteryEngineService

router = APIRouter(prefix="/mastery", tags=["Student Mastery & Difficulty Calibration"])


@router.post(
    "/record-attempt",
    response_model=MasteryUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Record question attempt and update topic mastery via Bayesian Knowledge Tracing",
)
async def record_question_attempt(
    attempt_in: RecordAttemptRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MasteryUpdateResponse:
    """
    Submits a student's answer to a question, executes the BKT probabilistic update,
    adapts the next item difficulty, and records telemetry.
    """
    try:
        return await MasteryEngineService.record_attempt(
            session=session,
            student_id=current_user.id,
            attempt_in=attempt_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/topics/{topic_id}",
    response_model=StudentTopicMasteryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student mastery profile for a specific topic",
)
async def get_topic_mastery(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StudentTopicMasteryResponse:
    """
    Retrieves the authenticated student's mastery probability, status tier, and streak on a topic.
    """
    mastery = await MasteryEngineService.get_topic_mastery(
        session=session,
        student_id=current_user.id,
        topic_id=topic_id,
    )
    if not mastery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mastery profile found for topic '{topic_id}'",
        )
    return StudentTopicMasteryResponse.model_validate(mastery)


@router.get(
    "/exams/{exam_template_id}",
    response_model=TopicMasteryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all topic masteries for the current student in an exam syllabus",
)
async def list_exam_topic_masteries(
    exam_template_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TopicMasteryListResponse:
    """
    Returns an overview of all topic masteries across an entire exam curriculum.
    """
    records = await MasteryEngineService.list_exam_topic_mastery(
        session=session,
        student_id=current_user.id,
        exam_template_id=exam_template_id,
    )
    return TopicMasteryListResponse(
        total=len(records),
        topic_masteries=[StudentTopicMasteryResponse.model_validate(m) for m in records],
    )
