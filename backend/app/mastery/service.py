from datetime import datetime, timezone
import logging
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.mastery.bkt import BKTEngine
from backend.app.mastery.models import (
    MasteryStatus,
    StudentQuestionAttempt,
    StudentTopicMastery,
)
from backend.app.mastery.schemas import (
    MasteryUpdateResponse,
    RecordAttemptRequest,
)
from backend.app.questions.models import DifficultyLevel
from backend.app.questions.service import QuestionBankService

logger = logging.getLogger("adaptive_exam_platform.mastery.service")


class MasteryEngineService:
    """
    Student Topic Mastery & Difficulty Calibration Orchestrator (PRD §5.4, §13, FR-003).
    Implements Bayesian belief updating on every question attempt.
    """

    @classmethod
    async def get_or_create_mastery(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
        topic_id: str,
    ) -> StudentTopicMastery:
        """
        Retrieves existing StudentTopicMastery or initializes a fresh prior record.
        """
        stmt = select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.exam_template_id == exam_template_id,
            StudentTopicMastery.topic_id == topic_id,
        )
        res = await session.exec(stmt)
        mastery = res.first()

        if not mastery:
            mastery = StudentTopicMastery(
                student_id=student_id,
                exam_template_id=exam_template_id,
                topic_id=topic_id,
                mastery_probability=0.10,
                status=MasteryStatus.NOVICE,
                current_difficulty=DifficultyLevel.EASY,
                total_attempts=0,
                correct_attempts=0,
                current_streak=0,
                best_streak=0,
                last_attempt_at=None,
            )
            session.add(mastery)
            await session.flush()
            await session.refresh(mastery)

        return mastery

    @classmethod
    async def record_attempt(
        cls,
        session: AsyncSession,
        student_id: str,
        attempt_in: RecordAttemptRequest,
    ) -> MasteryUpdateResponse:
        """
        Records a question attempt, executes Bayesian belief update, persists telemetry,
        and adapts target difficulty in real time.
        """
        # 1. Fetch Question Metadata
        question = await QuestionBankService.get_question(session, attempt_in.question_id)
        if not question:
            raise ValueError(f"Question with ID '{attempt_in.question_id}' not found")

        # 2. Fetch or Init StudentTopicMastery
        mastery = await cls.get_or_create_mastery(
            session=session,
            student_id=student_id,
            exam_template_id=question.exam_template_id,
            topic_id=question.topic_id,
        )

        prior_p = mastery.mastery_probability

        # 3. Compute BKT Bayesian Posterior & Difficulty Adaptation
        posterior_p, new_status, target_diff = BKTEngine.update_mastery(
            prior_probability=prior_p,
            is_correct=attempt_in.is_correct,
            question_type=question.question_type,
            difficulty=question.difficulty,
        )

        # 4. Update Mastery Record Metrics
        mastery.mastery_probability = round(posterior_p, 4)
        mastery.status = new_status
        mastery.current_difficulty = target_diff
        mastery.total_attempts += 1

        if attempt_in.is_correct:
            mastery.correct_attempts += 1
            mastery.current_streak += 1
            if mastery.current_streak > mastery.best_streak:
                mastery.best_streak = mastery.current_streak
        else:
            mastery.current_streak = 0

        mastery.last_attempt_at = datetime.now(timezone.utc)
        mastery.updated_at = datetime.now(timezone.utc)
        session.add(mastery)

        # 5. Persist Immutable Telemetry Attempt Log
        attempt = StudentQuestionAttempt(
            student_id=student_id,
            exam_template_id=question.exam_template_id,
            topic_id=question.topic_id,
            question_id=question.id,
            selected_option_key=attempt_in.selected_option_key,
            is_correct=attempt_in.is_correct,
            time_spent_seconds=attempt_in.time_spent_seconds,
            prior_mastery_probability=round(prior_p, 4),
            posterior_mastery_probability=round(posterior_p, 4),
        )
        session.add(attempt)
        await session.flush()
        await session.refresh(mastery)

        # 6. Diagnostic Error Bank Integration (PRD §12, FR-006, Constraint #8)
        if not attempt_in.is_correct:
            try:
                from backend.app.errors.service import ErrorBankService
                await ErrorBankService.log_error(
                    session=session,
                    student_id=student_id,
                    question=question,
                    selected_option_key=attempt_in.selected_option_key,
                    attempt_id=attempt.id,
                )
            except Exception as e:
                logger.warning(f"Error bank logging failed: {e}")

        # 7. Sync with Learning State Machine & Auto-Repair Error Bank (if MASTERED)
        if new_status == MasteryStatus.MASTERED:
            try:
                from backend.app.errors.service import ErrorBankService
                await ErrorBankService.auto_resolve_topic_errors(
                    session=session,
                    student_id=student_id,
                    topic_id=question.topic_id,
                )
            except Exception as e:
                logger.warning(f"Error bank auto-resolve failed: {e}")

            try:
                from backend.app.learning_state.models import LearningState
                from backend.app.learning_state.service import LearningStateMachineService
                await LearningStateMachineService.transition_state(
                    session=session,
                    student_id=student_id,
                    exam_template_id=question.exam_template_id,
                    topic_id=question.topic_id,
                    to_state=LearningState.MASTERY,
                    trigger="BKT_MASTERY_THRESHOLD_REACHED",
                    actor_id=student_id,
                    evidence={"mastery_probability": mastery.mastery_probability, "streak": mastery.current_streak},
                )
            except Exception as e:
                logger.debug(f"Learning state machine transition skipped or already in state: {e}")

        return MasteryUpdateResponse(
            student_id=student_id,
            exam_template_id=question.exam_template_id,
            topic_id=question.topic_id,
            question_id=question.id,
            is_correct=attempt_in.is_correct,
            prior_mastery_probability=round(prior_p, 4),
            posterior_mastery_probability=round(posterior_p, 4),
            status=new_status,
            current_difficulty=target_diff,
            total_attempts=mastery.total_attempts,
            correct_attempts=mastery.correct_attempts,
            current_streak=mastery.current_streak,
            best_streak=mastery.best_streak,
            updated_at=mastery.updated_at,
        )

    @classmethod
    async def get_topic_mastery(
        cls,
        session: AsyncSession,
        student_id: str,
        topic_id: str,
    ) -> Optional[StudentTopicMastery]:
        """
        Retrieves a student's topic mastery profile.
        """
        stmt = select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.topic_id == topic_id,
        )
        res = await session.exec(stmt)
        return res.first()

    @classmethod
    async def list_exam_topic_mastery(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
    ) -> List[StudentTopicMastery]:
        """
        Retrieves all topic mastery records for a student within a specific exam template.
        """
        stmt = (
            select(StudentTopicMastery)
            .where(
                StudentTopicMastery.student_id == student_id,
                StudentTopicMastery.exam_template_id == exam_template_id,
            )
            .order_by(StudentTopicMastery.updated_at.desc())
        )
        res = await session.exec(stmt)
        return list(res.all())
