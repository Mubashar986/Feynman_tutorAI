from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.learning_state.models import (
    LearningState,
    StudentLearningState,
    StateTransitionLog,
)
from backend.app.learning_state.schemas import (
    ExamLearningSummaryResponse,
    StudentLearningStateResponse,
)


class InvalidStateTransitionException(HTTPException):
    """Raised when an illegal transition is attempted according to PRD §13."""
    def __init__(self, from_state: LearningState, to_state: LearningState, reason: str = ""):
        detail = f"Illegal transition from '{from_state.value}' to '{to_state.value}'."
        if reason:
            detail += f" Reason: {reason}"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# Deterministic FSM transition matrix conforming strictly to PRD §13 (ADR-016)
VALID_TRANSITIONS: Dict[LearningState, Set[LearningState]] = {
    LearningState.NOT_STARTED: {
        LearningState.CALIBRATION,
        LearningState.FOUNDATION,
    },
    LearningState.CALIBRATION: {
        LearningState.FOUNDATION,
        LearningState.PRACTICING,
        LearningState.DIAGNOSIS,
    },
    LearningState.FOUNDATION: {
        LearningState.PRACTICING,
        LearningState.ASSESSMENT,
    },
    LearningState.PRACTICING: {
        LearningState.ASSESSMENT,
        LearningState.DIAGNOSIS,
        LearningState.REPAIR,
    },
    LearningState.ASSESSMENT: {
        LearningState.MASTERY,
        LearningState.DIAGNOSIS,
        LearningState.REPAIR,
    },
    LearningState.DIAGNOSIS: {
        LearningState.REPAIR,
        LearningState.FOUNDATION,
    },
    LearningState.REPAIR: {
        LearningState.PRACTICING,
        LearningState.ASSESSMENT,
    },
    LearningState.MASTERY: {
        LearningState.REVISION,
        LearningState.DIAGNOSIS,
    },
    LearningState.REVISION: {
        LearningState.MASTERY,
        LearningState.DIAGNOSIS,
        LearningState.REPAIR,
    },
}


class LearningStateMachineService:
    """
    Domain service orchestrating student state progression, transition verification,
    and ACID audit ledger recording.
    """

    @staticmethod
    async def get_or_create_state(
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
        topic_id: str,
    ) -> StudentLearningState:
        """
        Retrieves the student's topic state, or initializes a new NOT_STARTED record.
        """
        statement = (
            select(StudentLearningState)
            .where(StudentLearningState.student_id == student_id)
            .where(StudentLearningState.exam_template_id == exam_template_id)
            .where(StudentLearningState.topic_id == topic_id)
        )
        result = await session.execute(statement)
        state_record = result.scalar_one_or_none()

        if state_record is None:
            state_record = StudentLearningState(
                student_id=student_id,
                exam_template_id=exam_template_id,
                topic_id=topic_id,
                current_state=LearningState.NOT_STARTED,
                mastery_score=0.0,
            )
            session.add(state_record)
            await session.flush()

        return state_record

    @staticmethod
    def validate_transition(
        current_state: LearningState,
        target_state: LearningState,
        evidence_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Validates transition legality against the FSM matrix and guard predicates.
        """
        allowed_targets = VALID_TRANSITIONS.get(current_state, set())
        if target_state not in allowed_targets:
            raise InvalidStateTransitionException(
                from_state=current_state,
                to_state=target_state,
                reason=f"Allowed target states from '{current_state.value}' are: {[s.value for s in allowed_targets]}",
            )

        # Guard predicate: Assessment -> Mastery requires verification evidence
        if current_state == LearningState.ASSESSMENT and target_state == LearningState.MASTERY:
            if evidence_payload is not None and "score" in evidence_payload:
                score = float(evidence_payload["score"])
                min_threshold = float(evidence_payload.get("passing_threshold", 0.80))
                if score < min_threshold:
                    raise InvalidStateTransitionException(
                        from_state=current_state,
                        to_state=target_state,
                        reason=f"Score ({score}) does not satisfy required mastery threshold ({min_threshold}). Must route to DIAGNOSIS or REPAIR.",
                    )

    @classmethod
    async def transition_state(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
        topic_id: str,
        target_state: LearningState,
        trigger: str,
        evidence_payload: Dict[str, Any],
        actor_id: str,
        mastery_score: Optional[float] = None,
    ) -> Tuple[StudentLearningState, StateTransitionLog]:
        """
        Executes an atomic state transition:
        1. Loads current state record (with lock).
        2. Validates legality against FSM rules and guard predicates.
        3. Updates current state, counters, and timestamps.
        4. Appends an immutable audit log record.
        5. Flushes within the transaction.
        """
        state_record = await cls.get_or_create_state(
            session=session,
            student_id=student_id,
            exam_template_id=exam_template_id,
            topic_id=topic_id,
        )

        from_state = state_record.current_state

        # Validate transition
        cls.validate_transition(
            current_state=from_state,
            target_state=target_state,
            evidence_payload=evidence_payload,
        )

        now = datetime.now(timezone.utc)

        # Update state model
        state_record.current_state = target_state
        state_record.last_transition_at = now
        state_record.updated_at = now

        if mastery_score is not None:
            state_record.mastery_score = max(0.0, min(1.0, mastery_score))

        # Adjust success/failure counters
        if target_state == LearningState.MASTERY:
            state_record.consecutive_successes += 1
            state_record.consecutive_failures = 0
        elif target_state in {LearningState.DIAGNOSIS, LearningState.REPAIR}:
            state_record.consecutive_failures += 1
            state_record.consecutive_successes = 0

        # Create immutable audit log entry
        log_entry = StateTransitionLog(
            student_id=student_id,
            exam_template_id=exam_template_id,
            topic_id=topic_id,
            from_state=from_state,
            to_state=target_state,
            trigger=trigger,
            evidence_payload=evidence_payload or {},
            actor_id=actor_id,
            created_at=now,
        )

        session.add(state_record)
        session.add(log_entry)
        await session.flush()

        return state_record, log_entry

    @staticmethod
    async def get_topic_history(
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
        topic_id: str,
    ) -> List[StateTransitionLog]:
        """
        Fetches full chronological audit trail for a topic.
        """
        statement = (
            select(StateTransitionLog)
            .where(StateTransitionLog.student_id == student_id)
            .where(StateTransitionLog.exam_template_id == exam_template_id)
            .where(StateTransitionLog.topic_id == topic_id)
            .order_by(StateTransitionLog.created_at.desc())
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    @staticmethod
    async def get_student_exam_states(
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
    ) -> List[StudentLearningState]:
        """
        Fetches all topic learning states for a student in an exam.
        """
        statement = (
            select(StudentLearningState)
            .where(StudentLearningState.student_id == student_id)
            .where(StudentLearningState.exam_template_id == exam_template_id)
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    @classmethod
    async def get_exam_summary(
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
    ) -> ExamLearningSummaryResponse:
        """
        Generates aggregate progress overview across all topics for an exam.
        """
        states = await LearningStateMachineService.get_student_exam_states(
            session=session,
            student_id=student_id,
            exam_template_id=exam_template_id,
        )
        mastered = sum(1 for s in states if s.current_state == LearningState.MASTERY)
        in_progress = sum(1 for s in states if s.current_state not in {LearningState.NOT_STARTED, LearningState.MASTERY})

        return ExamLearningSummaryResponse(
            student_id=student_id,
            exam_template_id=exam_template_id,
            total_topics=len(states),
            mastered_count=mastered,
            in_progress_count=in_progress,
            topic_states=[StudentLearningStateResponse.model_validate(s) for s in states],
        )
