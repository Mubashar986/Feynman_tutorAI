from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.tutor.schemas import (
    SocraticPromptRequest,
    SocraticResponse,
    TutorSessionCreate,
    TutorSessionDetailResponse,
    TutorSessionResponse,
)
from backend.app.tutor.service import SocraticTutorService

router = APIRouter(prefix="/tutor", tags=["Socratic AI Tutor Engine"])


@router.post(
    "/sessions",
    response_model=TutorSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new 1-on-1 Socratic tutoring session",
)
async def create_tutor_session(
    session_in: TutorSessionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TutorSessionResponse:
    """
    Initializes a new conversational session scoped to a topic or specific question.
    """
    tutor_sess = await SocraticTutorService.create_session(
        session=session,
        student_id=current_user.id,
        session_in=session_in,
    )
    return TutorSessionResponse.model_validate(tutor_sess)


@router.get(
    "/sessions",
    response_model=List[TutorSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tutor sessions for the current student",
)
async def list_tutor_sessions(
    topic_id: Optional[str] = Query(None, description="Optional topic filter"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[TutorSessionResponse]:
    """
    Returns recent active and archived Socratic tutoring dialogues.
    """
    sessions = await SocraticTutorService.list_sessions(
        session=session,
        student_id=current_user.id,
        topic_id=topic_id,
        limit=limit,
    )
    return [TutorSessionResponse.model_validate(s) for s in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=TutorSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full dialogue turn history for a tutor session",
)
async def get_tutor_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TutorSessionDetailResponse:
    """
    Retrieves all chronological messages, KaTeX equations, and source citations for a session.
    """
    detail = await SocraticTutorService.get_session_history(
        session=session,
        student_id=current_user.id,
        session_id=session_id,
    )
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor session with ID '{session_id}' not found",
        )
    return detail


@router.post(
    "/sessions/{session_id}/message",
    response_model=SocraticResponse,
    status_code=status.HTTP_200_OK,
    summary="Send message and receive grounded Socratic guiding hint",
)
async def send_socratic_message(
    session_id: str,
    message_in: SocraticPromptRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SocraticResponse:
    """
    Executes a Socratic conversation turn with RAG curriculum grounding, mastery adaptation,
    and anti-leakage scaffolding.
    """
    try:
        return await SocraticTutorService.send_message(
            session=session,
            student_id=current_user.id,
            session_id=session_id,
            message_in=message_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
