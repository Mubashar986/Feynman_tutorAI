from datetime import datetime, timezone
import logging
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.errors.classifier import ErrorDiagnosticClassifier
from backend.app.errors.models import (
    ErrorCategory,
    Misconception,
    RepairStatus,
    StudentErrorLog,
)
from backend.app.errors.schemas import (
    ErrorListResponse,
    MisconceptionResponse,
    StudentErrorDetailResponse,
    StudentErrorLogResponse,
)
from backend.app.questions.models import Question
from backend.app.questions.service import QuestionBankService

logger = logging.getLogger("adaptive_exam_platform.errors.service")


class ErrorBankService:
    """
    Diagnostic Error Bank & Misconception Tracking Service (PRD §12, FR-006, FR-012, Cap 6).
    Enforces student tenant isolation and lifecycle remediation tracking (Constraint #2, #8).
    """

    @classmethod
    async def get_or_create_misconception(
        cls,
        session: AsyncSession,
        topic_id: str,
        code: str,
        title: str,
        description: str,
        remediation_guidance: Optional[str] = None,
    ) -> Misconception:
        """
        Retrieves existing Misconception entity or creates a new node in the knowledge graph.
        """
        stmt = select(Misconception).where(
            Misconception.topic_id == topic_id,
            Misconception.code == code,
        )
        res = await session.exec(stmt)
        misc = res.first()

        if not misc:
            misc = Misconception(
                topic_id=topic_id,
                code=code,
                title=title,
                description=description,
                remediation_guidance=remediation_guidance,
            )
            session.add(misc)
            await session.flush()
            await session.refresh(misc)

        return misc

    @classmethod
    async def log_error(
        cls,
        session: AsyncSession,
        student_id: str,
        question: Question,
        selected_option_key: Optional[str] = None,
        attempt_id: Optional[str] = None,
    ) -> StudentErrorLog:
        """
        Extracts distractor rationale, classifies error taxonomy, resolves misconception node,
        and atomically upserts a StudentErrorLog ticket.
        """
        # 1. Extract distractor rationale and correct answer from Question options
        distractor_rationale = None
        correct_answer = None
        student_answer = selected_option_key

        if question.options:
            for opt in question.options:
                if opt.is_correct:
                    correct_answer = f"Option {opt.option_key}: {opt.content}"
                if selected_option_key and opt.option_key.strip().upper() == selected_option_key.strip().upper():
                    distractor_rationale = opt.distractor_rationale

        # 2. Classify error and extract misconception metadata
        category, code, title, description, guidance = ErrorDiagnosticClassifier.classify_error(
            distractor_rationale=distractor_rationale,
            question_prompt=question.prompt,
        )

        # 3. Create or resolve Misconception node
        misconception = await cls.get_or_create_misconception(
            session=session,
            topic_id=question.topic_id,
            code=code,
            title=title,
            description=description,
            remediation_guidance=guidance,
        )

        # 4. Check for existing ACTIVE error log on same question to aggregate occurrences
        stmt = select(StudentErrorLog).where(
            StudentErrorLog.student_id == student_id,
            StudentErrorLog.question_id == question.id,
            StudentErrorLog.repair_status == RepairStatus.ACTIVE,
        )
        res = await session.exec(stmt)
        existing_error = res.first()

        if existing_error:
            existing_error.occurrence_count += 1
            existing_error.last_occurred_at = datetime.now(timezone.utc)
            existing_error.student_answer = student_answer
            existing_error.distractor_rationale = distractor_rationale
            existing_error.misconception_id = misconception.id
            existing_error.error_category = category
            session.add(existing_error)
            await session.flush()
            await session.refresh(existing_error)
            return existing_error

        # 5. Create fresh StudentErrorLog ticket
        new_error = StudentErrorLog(
            student_id=student_id,
            exam_template_id=question.exam_template_id,
            topic_id=question.topic_id,
            question_id=question.id,
            attempt_id=attempt_id,
            misconception_id=misconception.id,
            error_category=category,
            student_answer=student_answer,
            correct_answer=correct_answer,
            distractor_rationale=distractor_rationale,
            repair_status=RepairStatus.ACTIVE,
            occurrence_count=1,
        )
        session.add(new_error)
        await session.flush()
        await session.refresh(new_error)
        return new_error

    @classmethod
    async def resolve_error(
        cls,
        session: AsyncSession,
        student_id: str,
        error_log_id: str,
    ) -> StudentErrorLog:
        """
        Manually or pedagogically marks an error ticket as REPAIRED.
        """
        stmt = select(StudentErrorLog).where(
            StudentErrorLog.id == error_log_id,
            StudentErrorLog.student_id == student_id,
        )
        res = await session.exec(stmt)
        error_log = res.first()
        if not error_log:
            raise ValueError(f"Error log with ID '{error_log_id}' not found for student")

        error_log.repair_status = RepairStatus.REPAIRED
        error_log.repaired_at = datetime.now(timezone.utc)
        session.add(error_log)
        await session.flush()
        await session.refresh(error_log)
        return error_log

    @classmethod
    async def auto_resolve_topic_errors(
        cls,
        session: AsyncSession,
        student_id: str,
        topic_id: str,
    ) -> int:
        """
        Retires active error tickets for a topic when the student demonstrates subsequent mastery.
        """
        stmt = select(StudentErrorLog).where(
            StudentErrorLog.student_id == student_id,
            StudentErrorLog.topic_id == topic_id,
            StudentErrorLog.repair_status == RepairStatus.ACTIVE,
        )
        res = await session.exec(stmt)
        active_errors = list(res.all())

        now_utc = datetime.now(timezone.utc)
        for err in active_errors:
            err.repair_status = RepairStatus.REPAIRED
            err.repaired_at = now_utc
            session.add(err)

        if active_errors:
            await session.flush()

        return len(active_errors)

    @classmethod
    async def list_student_errors(
        cls,
        session: AsyncSession,
        student_id: str,
        topic_id: Optional[str] = None,
        exam_template_id: Optional[str] = None,
        repair_status: Optional[RepairStatus] = None,
        error_category: Optional[ErrorCategory] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ErrorListResponse:
        """
        Returns a paginated list of student errors enriched with question and misconception details.
        """
        base_stmt = select(StudentErrorLog).where(StudentErrorLog.student_id == student_id)

        if topic_id:
            base_stmt = base_stmt.where(StudentErrorLog.topic_id == topic_id)
        if exam_template_id:
            base_stmt = base_stmt.where(StudentErrorLog.exam_template_id == exam_template_id)
        if repair_status:
            base_stmt = base_stmt.where(StudentErrorLog.repair_status == repair_status)
        if error_category:
            base_stmt = base_stmt.where(StudentErrorLog.error_category == error_category)

        # Count queries
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await session.exec(count_stmt)).one()

        active_count_stmt = select(func.count()).where(
            StudentErrorLog.student_id == student_id,
            StudentErrorLog.repair_status == RepairStatus.ACTIVE,
        )
        active_total = (await session.exec(active_count_stmt)).one()

        repaired_count_stmt = select(func.count()).where(
            StudentErrorLog.student_id == student_id,
            StudentErrorLog.repair_status == RepairStatus.REPAIRED,
        )
        repaired_total = (await session.exec(repaired_count_stmt)).one()

        # Paginated fetch
        paginated_stmt = base_stmt.order_by(StudentErrorLog.last_occurred_at.desc()).offset(offset).limit(limit)
        results = await session.exec(paginated_stmt)
        error_logs = list(results.all())

        detail_list: List[StudentErrorDetailResponse] = []
        for err in error_logs:
            question = await QuestionBankService.get_question(session, err.question_id)
            misconception = None
            if err.misconception_id:
                misc_stmt = select(Misconception).where(Misconception.id == err.misconception_id)
                misc_res = await session.exec(misc_stmt)
                misconception = misc_res.first()

            detail = StudentErrorDetailResponse(
                id=err.id,
                student_id=err.student_id,
                exam_template_id=err.exam_template_id,
                topic_id=err.topic_id,
                question_id=err.question_id,
                attempt_id=err.attempt_id,
                misconception_id=err.misconception_id,
                error_category=err.error_category,
                student_answer=err.student_answer,
                correct_answer=err.correct_answer,
                distractor_rationale=err.distractor_rationale,
                repair_status=err.repair_status,
                occurrence_count=err.occurrence_count,
                first_detected_at=err.first_detected_at,
                last_occurred_at=err.last_occurred_at,
                repaired_at=err.repaired_at,
                question_prompt=question.prompt if question else None,
                question_explanation=question.explanation if question else None,
                misconception=MisconceptionResponse.model_validate(misconception) if misconception else None,
            )
            detail_list.append(detail)

        return ErrorListResponse(
            total=total,
            active_count=active_total,
            repaired_count=repaired_total,
            errors=detail_list,
        )

    @classmethod
    async def get_error_detail(
        cls,
        session: AsyncSession,
        student_id: str,
        error_log_id: str,
    ) -> Optional[StudentErrorDetailResponse]:
        """
        Fetches detailed error report for a single error log ID.
        """
        stmt = select(StudentErrorLog).where(
            StudentErrorLog.id == error_log_id,
            StudentErrorLog.student_id == student_id,
        )
        res = await session.exec(stmt)
        err = res.first()
        if not err:
            return None

        question = await QuestionBankService.get_question(session, err.question_id)
        misconception = None
        if err.misconception_id:
            misc_stmt = select(Misconception).where(Misconception.id == err.misconception_id)
            misc_res = await session.exec(misc_stmt)
            misconception = misc_res.first()

        return StudentErrorDetailResponse(
            id=err.id,
            student_id=err.student_id,
            exam_template_id=err.exam_template_id,
            topic_id=err.topic_id,
            question_id=err.question_id,
            attempt_id=err.attempt_id,
            misconception_id=err.misconception_id,
            error_category=err.error_category,
            student_answer=err.student_answer,
            correct_answer=err.correct_answer,
            distractor_rationale=err.distractor_rationale,
            repair_status=err.repair_status,
            occurrence_count=err.occurrence_count,
            first_detected_at=err.first_detected_at,
            last_occurred_at=err.last_occurred_at,
            repaired_at=err.repaired_at,
            question_prompt=question.prompt if question else None,
            question_explanation=question.explanation if question else None,
            misconception=MisconceptionResponse.model_validate(misconception) if misconception else None,
        )

    @classmethod
    async def list_topic_misconceptions(
        cls,
        session: AsyncSession,
        topic_id: str,
    ) -> List[Misconception]:
        """
        Lists all misconception knowledge nodes for a topic.
        """
        stmt = select(Misconception).where(Misconception.topic_id == topic_id)
        res = await session.exec(stmt)
        return list(res.all())
