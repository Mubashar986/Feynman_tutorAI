from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.errors.models import ErrorCategory, RepairStatus
from backend.app.errors.schemas import (
    ErrorListResponse,
    MisconceptionResponse,
    RepairErrorRequest,
    StudentErrorDetailResponse,
    StudentErrorLogResponse,
)
from backend.app.errors.service import ErrorBankService

router = APIRouter(prefix="/error-bank", tags=["Error Bank & Misconception Tracking"])


@router.get(
    "",
    response_model=ErrorListResponse,
    status_code=status.HTTP_200_OK,
    summary="List student error bank records with category and status filters",
)
async def list_errors(
    topic_id: Optional[str] = Query(None, description="Filter by topic ID"),
    exam_template_id: Optional[str] = Query(None, description="Filter by exam template ID"),
    repair_status: Optional[RepairStatus] = Query(None, description="Filter by repair status"),
    error_category: Optional[ErrorCategory] = Query(None, description="Filter by error category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ErrorListResponse:
    """
    Retrieves the authenticated student's diagnostic mistake tickets and aggregate active/repaired metrics.
    """
    return await ErrorBankService.list_student_errors(
        session=session,
        student_id=current_user.id,
        topic_id=topic_id,
        exam_template_id=exam_template_id,
        repair_status=repair_status,
        error_category=error_category,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{error_id}",
    response_model=StudentErrorDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get error record detail with distractor rationale and remediation guidance",
)
async def get_error_detail(
    error_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StudentErrorDetailResponse:
    """
    Retrieves detailed information about a student's mistake, including question prompt and misconception root.
    """
    error_detail = await ErrorBankService.get_error_detail(
        session=session,
        student_id=current_user.id,
        error_log_id=error_id,
    )
    if not error_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error log with ID '{error_id}' not found",
        )
    return error_detail


@router.post(
    "/{error_id}/repair",
    response_model=StudentErrorLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark an active error ticket as repaired",
)
async def repair_error(
    error_id: str,
    repair_in: Optional[RepairErrorRequest] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StudentErrorLogResponse:
    """
    Transitions an error ticket from ACTIVE/REMEDIATING to REPAIRED.
    """
    try:
        updated = await ErrorBankService.resolve_error(
            session=session,
            student_id=current_user.id,
            error_log_id=error_id,
        )
        return StudentErrorLogResponse.model_validate(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/misconceptions/topics/{topic_id}",
    response_model=List[MisconceptionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all known misconception knowledge nodes for a topic",
)
async def list_topic_misconceptions(
    topic_id: str,
    session: AsyncSession = Depends(get_db),
) -> List[MisconceptionResponse]:
    """
    Retrieves known cognitive misconception taxonomy entries for a curriculum topic.
    """
    misconceptions = await ErrorBankService.list_topic_misconceptions(
        session=session,
        topic_id=topic_id,
    )
    return [MisconceptionResponse.model_validate(m) for m in misconceptions]
