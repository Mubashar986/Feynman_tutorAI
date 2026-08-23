from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.advanced_modes.schemas import (
    AdversarialChallengeRequest,
    AdversarialChallengeResponse,
    AdversarialDefendRequest,
    AdversarialSessionDetailResponse,
    AdversarialSessionListResponse,
    DefenseEvaluationResponse,
    WhyWrongDiagnosticRequest,
    WhyWrongDiagnosticResponse,
)
from backend.app.advanced_modes.service import (
    AdversarialTutorService,
    WhyWrongDiagnosticService,
)
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db

router = APIRouter(prefix="/modes", tags=["Adversarial Tutor & Diagnostic Modes"])


# ==============================================================================
# 1. Adversarial Tutor Mode Endpoints (PRD Cap 18, FR-018)
# ==============================================================================

@router.post(
    "/adversarial/challenge",
    response_model=AdversarialChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Challenge student reasoning with an adversarial counterexample or edge case",
)
async def generate_adversarial_challenge(
    request_in: AdversarialChallengeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdversarialChallengeResponse:
    try:
        return await AdversarialTutorService.generate_challenge(
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
            detail=f"Failed to generate adversarial challenge: {str(e)}",
        )


@router.post(
    "/adversarial/defend",
    response_model=DefenseEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit student defense and evaluate argument robustness against challenge",
)
async def evaluate_adversarial_defense(
    request_in: AdversarialDefendRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DefenseEvaluationResponse:
    try:
        return await AdversarialTutorService.evaluate_defense(
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
            detail=f"Failed to evaluate student defense: {str(e)}",
        )


@router.get(
    "/adversarial/sessions",
    response_model=AdversarialSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List past adversarial sparring sessions for the current student",
)
async def list_adversarial_sessions(
    exam_template_id: Optional[str] = Query(None, description="Optional exam template filter"),
    limit: int = Query(20, ge=1, le=100, description="Max sessions to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdversarialSessionListResponse:
    return await AdversarialTutorService.list_student_sessions(
        session=session,
        student_id=current_user.id,
        exam_template_id=exam_template_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/adversarial/sessions/{session_id}",
    response_model=AdversarialSessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full history of challenges and defenses for an adversarial session",
)
async def get_adversarial_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdversarialSessionDetailResponse:
    try:
        return await AdversarialTutorService.get_session_detail(
            session=session,
            student_id=current_user.id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==============================================================================
# 2. Why-You-Are-Wrong Diagnostic Mode Endpoints (PRD Cap 19, FR-019)
# ==============================================================================

@router.post(
    "/why-wrong/diagnose",
    response_model=WhyWrongDiagnosticResponse,
    status_code=status.HTTP_200_OK,
    summary="Diagnose why an answer choice is incorrect and extract cognitive fallacy",
)
async def diagnose_incorrect_answer(
    request_in: WhyWrongDiagnosticRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WhyWrongDiagnosticResponse:
    try:
        return await WhyWrongDiagnosticService.diagnose_incorrect_answer(
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
            detail=f"Failed to diagnose incorrect answer: {str(e)}",
        )


@router.get(
    "/why-wrong/diagnostics",
    response_model=List[WhyWrongDiagnosticResponse],
    status_code=status.HTTP_200_OK,
    summary="List past fallacy diagnostics for the current student",
)
async def list_student_diagnostics(
    topic_id: Optional[str] = Query(None, description="Optional topic filter"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[WhyWrongDiagnosticResponse]:
    return await WhyWrongDiagnosticService.list_student_diagnostics(
        session=session,
        student_id=current_user.id,
        topic_id=topic_id,
        limit=limit,
        offset=offset,
    )
