from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.revision.schemas import (
    CardSeedRequest,
    DueCardsListResponse,
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    RevisionMetricsResponse,
)
from backend.app.revision.service import SpacedRepetitionService

router = APIRouter(prefix="/revision", tags=["Spaced Repetition & Revision"])


@router.get(
    "/due",
    response_model=DueCardsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get prioritized list of due revision flashcards (PRD FR-007)",
)
async def get_due_cards(
    exam_template_id: Optional[str] = Query(None, description="Optional exam filter"),
    topic_id: Optional[str] = Query(None, description="Optional topic filter"),
    limit: int = Query(20, ge=1, le=100, description="Max cards to retrieve"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DueCardsListResponse:
    """
    Returns flashcards due for active recall review, ranked with active Error Bank items first.
    """
    return await SpacedRepetitionService.get_due_cards(
        session=session,
        student_id=current_user.id,
        exam_template_id=exam_template_id,
        topic_id=topic_id,
        limit=limit,
    )


@router.post(
    "/review",
    response_model=ReviewSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit review rating and recalculate SM-2 interval",
)
async def submit_review(
    review_in: ReviewSubmitRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ReviewSubmitResponse:
    """
    Updates the card's ease factor and schedules the next review date using SM-2.
    """
    try:
        return await SpacedRepetitionService.submit_review(
            session=session,
            student_id=current_user.id,
            review_in=review_in,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/metrics",
    response_model=RevisionMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get summary metrics and retention rate for revision decks",
)
async def get_revision_metrics(
    exam_template_id: Optional[str] = Query(None, description="Optional exam template filter"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RevisionMetricsResponse:
    """
    Calculates total cards, cards due today, learning states, and historical retention rate.
    """
    return await SpacedRepetitionService.get_revision_metrics(
        session=session,
        student_id=current_user.id,
        exam_template_id=exam_template_id,
    )


@router.post(
    "/cards/seed",
    status_code=status.HTTP_201_CREATED,
    summary="Seed flashcards from question bank for a syllabus",
)
async def seed_review_cards(
    seed_in: CardSeedRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Initializes flashcards for questions in the specified exam template or topic.
    """
    count = await SpacedRepetitionService.seed_cards_for_topic(
        session=session,
        student_id=current_user.id,
        seed_in=seed_in,
    )
    return {"seeded_count": count, "message": f"Successfully initialized {count} revision cards"}
