from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import get_current_user, require_role
from backend.app.auth.models import User, UserRole
from backend.app.core.database import get_db
from backend.app.simulation.schemas import (
    BlueprintCreateRequest,
    BlueprintResponse,
    SaveAnswerRequest,
    SaveAnswerResponse,
    SimulationSessionListResponse,
    SimulationSessionResponse,
    SimulationStartRequest,
    SimulationSubmitResponse,
)
from backend.app.simulation.service import ExamSimulationService

router = APIRouter(tags=["Exam Simulation & Blueprints"])


# ==============================================================================
# 1. Exam Blueprint Management Routes (PRD FR-014)
# ==============================================================================

@router.post(
    "/blueprints",
    response_model=BlueprintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Exam Blueprint with topic weightings (Admin / Instructor)",
)
async def create_exam_blueprint(
    request_in: BlueprintCreateRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.INSTRUCTOR])),
    session: AsyncSession = Depends(get_db),
) -> BlueprintResponse:
    try:
        return await ExamSimulationService.create_blueprint(session, request_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/blueprints",
    response_model=List[BlueprintResponse],
    status_code=status.HTTP_200_OK,
    summary="List available Exam Blueprints",
)
async def list_exam_blueprints(
    exam_template_id: Optional[str] = Query(None, description="Optional exam template ID filter"),
    session: AsyncSession = Depends(get_db),
) -> List[BlueprintResponse]:
    return await ExamSimulationService.list_blueprints(session, exam_template_id)


@router.get(
    "/blueprints/{blueprint_id}",
    response_model=BlueprintResponse,
    status_code=status.HTTP_200_OK,
    summary="Get blueprint configuration details",
)
async def get_exam_blueprint(
    blueprint_id: str,
    session: AsyncSession = Depends(get_db),
) -> BlueprintResponse:
    try:
        return await ExamSimulationService.get_blueprint(session, blueprint_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==============================================================================
# 2. Mock Exam Simulation Lifecycle Routes (PRD FR-020)
# ==============================================================================

@router.post(
    "/simulations/start",
    response_model=SimulationSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a full-length timed exam simulation",
)
async def start_simulation(
    request_in: SimulationStartRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SimulationSessionResponse:
    try:
        return await ExamSimulationService.start_simulation(
            session=session,
            student_id=current_user.id,
            request_in=request_in,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/simulations/{session_id}",
    response_model=SimulationSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active simulation paper and time remaining",
)
async def get_active_simulation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SimulationSessionResponse:
    try:
        return await ExamSimulationService.get_active_simulation(
            session=session,
            student_id=current_user.id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/simulations/{session_id}/save-answer",
    response_model=SaveAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Auto-save an individual question answer during exam taking",
)
async def save_simulation_answer(
    session_id: str,
    request_in: SaveAnswerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SaveAnswerResponse:
    try:
        return await ExamSimulationService.save_answer(
            session=session,
            student_id=current_user.id,
            session_id=session_id,
            request_in=request_in,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/simulations/{session_id}/submit",
    response_model=SimulationSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit exam paper and trigger deterministic auto-grading",
)
async def submit_simulation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SimulationSubmitResponse:
    try:
        return await ExamSimulationService.submit_simulation(
            session=session,
            student_id=current_user.id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/simulations/{session_id}/report",
    response_model=SimulationSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="View comprehensive post-exam report and topic breakdown",
)
async def get_simulation_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SimulationSubmitResponse:
    try:
        return await ExamSimulationService.get_simulation_report(
            session=session,
            student_id=current_user.id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/simulations",
    response_model=SimulationSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List past simulation sessions for current student",
)
async def list_student_simulations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SimulationSessionListResponse:
    return await ExamSimulationService.list_student_simulations(
        session=session,
        student_id=current_user.id,
        limit=limit,
        offset=offset,
    )
