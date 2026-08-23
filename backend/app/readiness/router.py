from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.readiness.schemas import ExamReadinessReport, ReadinessHistoryResponse
from backend.app.readiness.service import ExamReadinessService

router = APIRouter(tags=["Calibrated Exam Readiness & Analytics"])


@router.get(
    "/readiness/{exam_template_id}",
    response_model=ExamReadinessReport,
    status_code=status.HTTP_200_OK,
    summary="Compute current calibrated exam readiness score, pass probability & topic recommendations",
)
async def get_exam_readiness_assessment(
    exam_template_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExamReadinessReport:
    """
    Synthesizes Blueprint-weighted BKT knowledge tracing, continuous Ebbinghaus retrievability,
    timed mock exam simulation performance, and response latency pacing consistency into a
    calibrated exam readiness score (0-100%) and logistic pass probability (PRD Cap 20, FR-020).
    """
    try:
        return await ExamReadinessService.calculate_readiness(
            session=session,
            student_id=current_user.id,
            exam_template_id=exam_template_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/readiness/{exam_template_id}/history",
    response_model=ReadinessHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve historical readiness progression trajectory curve",
)
async def get_readiness_history(
    exam_template_id: str,
    limit: int = Query(30, ge=1, le=100, description="Max historical snapshots to retrieve"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReadinessHistoryResponse:
    """
    Retrieves chronological progression snapshots of exam readiness scores for progress charting.
    """
    return await ExamReadinessService.get_readiness_history(
        session=session,
        student_id=current_user.id,
        exam_template_id=exam_template_id,
        limit=limit,
    )
