from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.database import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, UserRole
from backend.app.learning_state.models import StudentLearningState, StateTransitionLog
from backend.app.learning_state.schemas import (
    ExamLearningSummaryResponse,
    StateTransitionLogResponse,
    StateTransitionRequest,
    StudentLearningStateResponse,
)
from backend.app.learning_state.service import LearningStateMachineService

router = APIRouter(prefix="/learning-state", tags=["Learning State Machine"])


def resolve_student_id(current_user: User, requested_student_id: Optional[str]) -> str:
    """
    Enforces server-side tenant isolation (PRD Constraint #2, FR-021).
    Regular students can only access their own state. Instructors and Admins can query other students.
    """
    if requested_student_id and requested_student_id != current_user.id:
        if current_user.role not in [UserRole.INSTRUCTOR, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only access their own learning state.",
            )
        return requested_student_id
    return current_user.id


@router.post(
    "/transition",
    response_model=StudentLearningStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a verified learning state transition",
)
async def transition_learning_state(
    request: StateTransitionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StudentLearningStateResponse:
    """
    Validates and executes an atomic state transition in the Student Learning State Machine.
    Records an immutable audit log entry with structured evidence (PRD §13, FR-001, FR-025).
    """
    target_student_id = resolve_student_id(current_user, request.student_id)

    state_record, _ = await LearningStateMachineService.transition_state(
        session=session,
        student_id=target_student_id,
        exam_template_id=request.exam_template_id,
        topic_id=request.topic_id,
        target_state=request.target_state,
        trigger=request.trigger,
        evidence_payload=request.evidence_payload,
        actor_id=current_user.id,
        mastery_score=request.mastery_score,
    )

    return StudentLearningStateResponse.model_validate(state_record)


@router.get(
    "/topic/{topic_id}",
    response_model=StudentLearningStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current student state for a topic",
)
async def get_topic_state(
    topic_id: str,
    exam_template_id: str = Query(..., description="Exam template UUID"),
    student_id: Optional[str] = Query(None, description="Optional student ID for instructor/admin lookup"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StudentLearningStateResponse:
    """
    Fetches the current learning state for a specific student, exam, and topic.
    """
    target_student_id = resolve_student_id(current_user, student_id)

    state_record = await LearningStateMachineService.get_or_create_state(
        session=session,
        student_id=target_student_id,
        exam_template_id=exam_template_id,
        topic_id=topic_id,
    )

    return StudentLearningStateResponse.model_validate(state_record)


@router.get(
    "/topic/{topic_id}/history",
    response_model=List[StateTransitionLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Get audit log history for a topic",
)
async def get_topic_history(
    topic_id: str,
    exam_template_id: str = Query(..., description="Exam template UUID"),
    student_id: Optional[str] = Query(None, description="Optional student ID for instructor/admin lookup"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[StateTransitionLogResponse]:
    """
    Retrieves the complete immutable audit trail for a topic (PRD FR-025, NFR-008).
    """
    target_student_id = resolve_student_id(current_user, student_id)

    logs = await LearningStateMachineService.get_topic_history(
        session=session,
        student_id=target_student_id,
        exam_template_id=exam_template_id,
        topic_id=topic_id,
    )

    return [StateTransitionLogResponse.model_validate(log) for log in logs]


@router.get(
    "/exam/{exam_template_id}",
    response_model=ExamLearningSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student exam learning progress summary",
)
async def get_exam_summary(
    exam_template_id: str,
    student_id: Optional[str] = Query(None, description="Optional student ID for instructor/admin lookup"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExamLearningSummaryResponse:
    """
    Fetches aggregate progress metrics and all topic states for an exam.
    """
    target_student_id = resolve_student_id(current_user, student_id)

    return await LearningStateMachineService.get_exam_summary(
        session=session,
        student_id=target_student_id,
        exam_template_id=exam_template_id,
    )
