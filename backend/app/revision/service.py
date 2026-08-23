from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Optional
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.errors.models import RepairStatus, StudentErrorLog
from backend.app.questions.models import Question
from backend.app.revision.models import CardState, ReviewLog, ReviewRating, SpacedReviewCard
from backend.app.revision.schemas import (
    CardSeedRequest,
    DueCardsListResponse,
    ReviewCardDetailResponse,
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    RevisionMetricsResponse,
)
from backend.app.revision.sm2 import SM2Engine

logger = logging.getLogger("adaptive_exam_platform.revision.service")


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SpacedRepetitionService:
    """
    Spaced Repetition Scheduling & Retention Engine (PRD FR-007, Cap 7, §15).
    Orchestrates SM-2 intervals, due queues, and Error Bank priority boosting.
    """

    @classmethod
    async def get_or_create_card(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
        topic_id: str,
        question_id: str,
    ) -> SpacedReviewCard:
        """
        Retrieves an existing review card or initializes a new one.
        """
        stmt = select(SpacedReviewCard).where(
            SpacedReviewCard.student_id == student_id,
            SpacedReviewCard.question_id == question_id,
        )
        res = await session.exec(stmt)
        card = res.first()
        if card:
            return card

        card = SpacedReviewCard(
            student_id=student_id,
            exam_template_id=exam_template_id,
            topic_id=topic_id,
            question_id=question_id,
            card_state=CardState.NEW,
            repetitions=0,
            interval_days=0.0,
            ease_factor=SM2Engine.DEFAULT_EASE_FACTOR,
            stability=1.0,
            due_at=datetime.now(timezone.utc),
        )
        session.add(card)
        await session.flush()
        await session.refresh(card)
        return card

    @classmethod
    async def submit_review(
        cls,
        session: AsyncSession,
        student_id: str,
        review_in: ReviewSubmitRequest,
    ) -> ReviewSubmitResponse:
        """
        Submits an active recall rating, updates SM-2 intervals, and schedules the next review date.
        """
        stmt = select(SpacedReviewCard).where(
            SpacedReviewCard.id == review_in.card_id,
            SpacedReviewCard.student_id == student_id,
        )
        res = await session.exec(stmt)
        card = res.first()
        if not card:
            raise ValueError(f"Spaced review card '{review_in.card_id}' not found for this student")

        prior_interval = card.interval_days
        prior_ef = card.ease_factor

        # 1. Compute new intervals via SM2Engine
        new_rep, new_interval, new_ef, new_state, new_stab = SM2Engine.calculate_next_interval(
            repetitions=card.repetitions,
            interval_days=card.interval_days,
            ease_factor=card.ease_factor,
            rating=review_in.rating,
        )

        now = datetime.now(timezone.utc)
        new_due_at = now + timedelta(days=new_interval)

        # 2. Update Card State
        card.repetitions = new_rep
        card.interval_days = new_interval
        card.ease_factor = new_ef
        card.card_state = new_state
        card.stability = new_stab
        card.due_at = new_due_at
        card.last_reviewed_at = now
        card.updated_at = now
        session.add(card)

        # 3. Log Telemetry
        review_log = ReviewLog(
            card_id=card.id,
            student_id=student_id,
            rating=review_in.rating,
            prior_interval_days=prior_interval,
            new_interval_days=new_interval,
            prior_ease_factor=prior_ef,
            new_ease_factor=new_ef,
            reviewed_at=now,
        )
        session.add(review_log)
        await session.flush()

        feedback_msg = (
            f"Review recorded! Next review in {new_interval} day(s) "
            f"({new_due_at.strftime('%Y-%m-%d %H:%M UTC')})."
        )

        return ReviewSubmitResponse(
            card_id=card.id,
            rating=review_in.rating,
            prior_interval_days=prior_interval,
            new_interval_days=new_interval,
            new_ease_factor=new_ef,
            new_due_at=new_due_at,
            card_state=new_state,
            message=feedback_msg,
        )

    @classmethod
    async def get_due_cards(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        limit: int = 20,
    ) -> DueCardsListResponse:
        """
        Retrieves due review flashcards ordered by Error Bank priority and retrievability urgency.
        """
        now = datetime.now(timezone.utc)
        stmt = select(SpacedReviewCard).where(
            SpacedReviewCard.student_id == student_id,
            SpacedReviewCard.due_at <= now,
        )
        if exam_template_id:
            stmt = stmt.where(SpacedReviewCard.exam_template_id == exam_template_id)
        if topic_id:
            stmt = stmt.where(SpacedReviewCard.topic_id == topic_id)

        res = await session.exec(stmt)
        cards = list(res.all())

        if not cards:
            return DueCardsListResponse(total_due=0, due_cards=[])

        # 1. Fetch active errors to identify high-priority cards
        err_stmt = select(StudentErrorLog.question_id).where(
            StudentErrorLog.student_id == student_id,
            StudentErrorLog.repair_status == RepairStatus.ACTIVE,
        )
        err_res = await session.exec(err_stmt)
        active_error_qids = set(err_res.all())

        # 2. Fetch associated questions
        q_ids = [c.question_id for c in cards]
        q_stmt = select(Question).where(Question.id.in_(q_ids))
        q_res = await session.exec(q_stmt)
        questions_by_id: Dict[str, Question] = {q.id: q for q in q_res.all()}

        # 3. Assemble and rank cards
        detailed_cards: List[ReviewCardDetailResponse] = []
        for c in cards:
            q = questions_by_id.get(c.question_id)
            if not q:
                continue

            has_error = c.question_id in active_error_qids
            last_rev = _ensure_utc(c.last_reviewed_at)
            days_elapsed = (now - last_rev).total_seconds() / 86400.0 if last_rev else 1.0
            retrievability = SM2Engine.calculate_retrievability(days_elapsed, c.stability)

            detail = ReviewCardDetailResponse(
                id=c.id,
                student_id=c.student_id,
                exam_template_id=c.exam_template_id,
                topic_id=c.topic_id,
                question_id=c.question_id,
                card_state=c.card_state,
                repetitions=c.repetitions,
                interval_days=c.interval_days,
                ease_factor=c.ease_factor,
                stability=c.stability,
                due_at=c.due_at,
                last_reviewed_at=c.last_reviewed_at,
                created_at=c.created_at,
                question_prompt=q.prompt,
                question_explanation=q.explanation,
                has_active_error=has_error,
                estimated_retrievability=retrievability,
            )
            detailed_cards.append(detail)

        # Multi-tier ranking:
        # 1. Cards with active errors first (True > False)
        # 2. Lower retrievability first (ascending order of R(t))
        detailed_cards.sort(key=lambda x: (not x.has_active_error, x.estimated_retrievability))

        return DueCardsListResponse(
            total_due=len(detailed_cards),
            due_cards=detailed_cards[:limit],
        )

    @classmethod
    async def get_revision_metrics(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: Optional[str] = None,
    ) -> RevisionMetricsResponse:
        """
        Calculates retention metrics, active deck sizes, and historical accuracy.
        """
        now = datetime.now(timezone.utc)
        stmt = select(SpacedReviewCard).where(SpacedReviewCard.student_id == student_id)
        if exam_template_id:
            stmt = stmt.where(SpacedReviewCard.exam_template_id == exam_template_id)

        res = await session.exec(stmt)
        cards = list(res.all())

        total_cards = len(cards)
        new_cards = sum(1 for c in cards if c.card_state == CardState.NEW)
        learning_cards = sum(1 for c in cards if c.card_state in (CardState.LEARNING, CardState.RELEARNING))
        review_cards = sum(1 for c in cards if c.card_state == CardState.REVIEW)
        due_today = sum(1 for c in cards if _ensure_utc(c.due_at) <= now)

        # Compute historical retention accuracy from logs
        log_stmt = select(ReviewLog).where(ReviewLog.student_id == student_id)
        log_res = await session.exec(log_stmt)
        logs = list(log_res.all())

        if logs:
            successful_recalls = sum(1 for l in logs if l.rating in (ReviewRating.GOOD, ReviewRating.EASY))
            avg_retention = round(successful_recalls / len(logs), 3)
        else:
            avg_retention = 1.0

        return RevisionMetricsResponse(
            total_cards=total_cards,
            new_cards=new_cards,
            learning_cards=learning_cards,
            review_cards=review_cards,
            due_today=due_today,
            average_retention_rate=avg_retention,
        )

    @classmethod
    async def seed_cards_for_topic(
        cls,
        session: AsyncSession,
        student_id: str,
        seed_in: CardSeedRequest,
    ) -> int:
        """
        Seeds flashcards for all validated questions in an exam template/topic.
        """
        q_stmt = select(Question).where(Question.exam_template_id == seed_in.exam_template_id)
        if seed_in.topic_id:
            q_stmt = q_stmt.where(Question.topic_id == seed_in.topic_id)

        res = await session.exec(q_stmt)
        questions = list(res.all())

        seeded_count = 0
        for q in questions:
            await cls.get_or_create_card(
                session=session,
                student_id=student_id,
                exam_template_id=q.exam_template_id,
                topic_id=q.topic_id,
                question_id=q.id,
            )
            seeded_count += 1

        return seeded_count
