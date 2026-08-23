from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import Topic
from backend.app.questions.models import Question, QuestionOption
from backend.app.simulation.assembler import StratifiedBlueprintAssembler
from backend.app.simulation.grader import AutoGradingService
from backend.app.simulation.models import (
    BlueprintTopicDistribution,
    ExamBlueprint,
    SimulationAnswer,
    SimulationReport,
    SimulationSession,
    SimulationStatus,
)
from backend.app.simulation.schemas import (
    BlueprintCreateRequest,
    BlueprintResponse,
    BlueprintTopicDistributionResponse,
    QuestionResultDetail,
    SanitizedOption,
    SanitizedQuestion,
    SaveAnswerRequest,
    SaveAnswerResponse,
    SimulationSessionListResponse,
    SimulationSessionResponse,
    SimulationSessionSummary,
    SimulationStartRequest,
    SimulationSubmitResponse,
    TopicPerformanceSummary,
)

logger = logging.getLogger("adaptive_exam_platform.simulation.service")


class ExamSimulationService:
    """
    Domain orchestrator for Exam Blueprint configurations, Mock Exam sessions, and auto-grading.
    """

    # ==========================================================================
    # 1. Blueprint Management
    # ==========================================================================

    @classmethod
    async def create_blueprint(
        cls,
        session: AsyncSession,
        request_in: BlueprintCreateRequest,
    ) -> BlueprintResponse:
        # 1. Check duplicate code
        existing = (await session.exec(select(ExamBlueprint).where(ExamBlueprint.code == request_in.code))).first()
        if existing:
            raise ValueError(f"Blueprint with code '{request_in.code}' already exists.")

        # 2. Create Blueprint
        blueprint = ExamBlueprint(
            exam_template_id=request_in.exam_template_id,
            code=request_in.code,
            title=request_in.title,
            description=request_in.description,
            duration_minutes=request_in.duration_minutes,
            total_questions=request_in.total_questions,
            total_marks=request_in.total_marks,
            passing_percentage=request_in.passing_percentage,
        )
        session.add(blueprint)
        await session.flush()

        # 3. Create Topic Distributions
        dist_responses = []
        topic_ids = [d.topic_id for d in request_in.topic_distributions]
        topics_db = []
        if topic_ids:
            topics_db = (await session.exec(select(Topic).where(Topic.id.in_(topic_ids)))).all()
        topic_title_map = {t.id: t.title for t in topics_db}

        for dist_in in request_in.topic_distributions:
            q_count = max(1, round(request_in.total_questions * dist_in.target_weight))
            dist_row = BlueprintTopicDistribution(
                blueprint_id=blueprint.id,
                topic_id=dist_in.topic_id,
                target_weight=dist_in.target_weight,
                target_question_count=q_count,
            )
            session.add(dist_row)
            await session.flush()
            dist_responses.append(
                BlueprintTopicDistributionResponse(
                    id=dist_row.id,
                    topic_id=dist_row.topic_id,
                    topic_title=topic_title_map.get(dist_row.topic_id),
                    target_weight=dist_row.target_weight,
                    target_question_count=dist_row.target_question_count,
                )
            )

        await session.commit()
        await session.refresh(blueprint)

        return BlueprintResponse(
            id=blueprint.id,
            exam_template_id=blueprint.exam_template_id,
            code=blueprint.code,
            title=blueprint.title,
            description=blueprint.description,
            duration_minutes=blueprint.duration_minutes,
            total_questions=blueprint.total_questions,
            total_marks=blueprint.total_marks,
            passing_percentage=blueprint.passing_percentage,
            topic_distributions=dist_responses,
            created_at=blueprint.created_at,
        )

    @classmethod
    async def get_blueprint(
        cls,
        session: AsyncSession,
        blueprint_id: str,
    ) -> BlueprintResponse:
        blueprint = (await session.exec(select(ExamBlueprint).where(ExamBlueprint.id == blueprint_id))).first()
        if not blueprint:
            raise ValueError(f"Exam Blueprint '{blueprint_id}' not found.")

        dist_rows = (
            await session.exec(
                select(BlueprintTopicDistribution).where(BlueprintTopicDistribution.blueprint_id == blueprint.id)
            )
        ).all()

        topic_ids = [d.topic_id for d in dist_rows]
        topics_db = []
        if topic_ids:
            topics_db = (await session.exec(select(Topic).where(Topic.id.in_(topic_ids)))).all()
        topic_title_map = {t.id: t.title for t in topics_db}

        dist_responses = [
            BlueprintTopicDistributionResponse(
                id=d.id,
                topic_id=d.topic_id,
                topic_title=topic_title_map.get(d.topic_id),
                target_weight=d.target_weight,
                target_question_count=d.target_question_count,
            )
            for d in dist_rows
        ]

        return BlueprintResponse(
            id=blueprint.id,
            exam_template_id=blueprint.exam_template_id,
            code=blueprint.code,
            title=blueprint.title,
            description=blueprint.description,
            duration_minutes=blueprint.duration_minutes,
            total_questions=blueprint.total_questions,
            total_marks=blueprint.total_marks,
            passing_percentage=blueprint.passing_percentage,
            topic_distributions=dist_responses,
            created_at=blueprint.created_at,
        )

    @classmethod
    async def list_blueprints(
        cls,
        session: AsyncSession,
        exam_template_id: Optional[str] = None,
    ) -> List[BlueprintResponse]:
        stmt = select(ExamBlueprint)
        if exam_template_id:
            stmt = stmt.where(ExamBlueprint.exam_template_id == exam_template_id)
        blueprints = (await session.exec(stmt)).all()

        results = []
        for b in blueprints:
            res = await cls.get_blueprint(session, b.id)
            results.append(res)
        return results

    # ==========================================================================
    # 2. Simulation Lifecycle & Paper Assembly
    # ==========================================================================

    @classmethod
    async def start_simulation(
        cls,
        session: AsyncSession,
        student_id: str,
        request_in: SimulationStartRequest,
    ) -> SimulationSessionResponse:
        blueprint = (await session.exec(select(ExamBlueprint).where(ExamBlueprint.id == request_in.blueprint_id))).first()
        if not blueprint:
            raise ValueError(f"Exam Blueprint '{request_in.blueprint_id}' not found.")

        # 1. Assemble Paper via Stratified Sampling
        questions = await StratifiedBlueprintAssembler.assemble_paper(session, blueprint)
        if not questions:
            raise ValueError("No questions available to assemble a mock exam paper.")

        question_ids = [q.id for q in questions]

        # 2. Calculate Server-Side Timestamps (UTC)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=blueprint.duration_minutes)

        # 3. Create Simulation Session
        sim_session = SimulationSession(
            student_id=student_id,
            blueprint_id=blueprint.id,
            exam_template_id=blueprint.exam_template_id,
            status=SimulationStatus.IN_PROGRESS,
            started_at=now,
            expires_at=expires_at,
            question_ids=question_ids,
        )
        session.add(sim_session)
        await session.commit()
        await session.refresh(sim_session)

        return await cls._build_session_response(session, sim_session, blueprint, questions)

    @classmethod
    async def get_active_simulation(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
    ) -> SimulationSessionResponse:
        sim_session = (
            await session.exec(
                select(SimulationSession).where(
                    SimulationSession.id == session_id,
                    SimulationSession.student_id == student_id,
                )
            )
        ).first()
        if not sim_session:
            raise ValueError(f"Simulation session '{session_id}' not found.")

        blueprint = (await session.exec(select(ExamBlueprint).where(ExamBlueprint.id == sim_session.blueprint_id))).first()
        if not blueprint:
            raise ValueError("Associated blueprint not found.")

        # Check for expiry
        now = datetime.now(timezone.utc)
        expires = sim_session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if sim_session.status == SimulationStatus.IN_PROGRESS and now > expires:
            sim_session.status = SimulationStatus.EXPIRED
            session.add(sim_session)
            await session.commit()

        # Fetch questions
        questions_db = []
        if sim_session.question_ids:
            q_stmt = select(Question).where(Question.id.in_(sim_session.question_ids))
            questions_db = (await session.exec(q_stmt)).all()
            # Preserve original order
            q_order = {qid: i for i, qid in enumerate(sim_session.question_ids)}
            questions_db.sort(key=lambda q: q_order.get(q.id, 999))

        return await cls._build_session_response(session, sim_session, blueprint, questions_db)

    @classmethod
    async def save_answer(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
        request_in: SaveAnswerRequest,
    ) -> SaveAnswerResponse:
        sim_session = (
            await session.exec(
                select(SimulationSession).where(
                    SimulationSession.id == session_id,
                    SimulationSession.student_id == student_id,
                )
            )
        ).first()
        if not sim_session:
            raise ValueError(f"Simulation session '{session_id}' not found.")

        # Verify time limit & active status
        now = datetime.now(timezone.utc)
        expires = sim_session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if sim_session.status != SimulationStatus.IN_PROGRESS or now > expires:
            if sim_session.status == SimulationStatus.IN_PROGRESS:
                sim_session.status = SimulationStatus.EXPIRED
                session.add(sim_session)
                await session.commit()
            raise ValueError("Exam session has expired or is already submitted.")

        if request_in.question_id not in (sim_session.question_ids or []):
            raise ValueError("Question does not belong to this exam paper.")

        # Upsert answer record
        existing = (
            await session.exec(
                select(SimulationAnswer).where(
                    SimulationAnswer.session_id == sim_session.id,
                    SimulationAnswer.question_id == request_in.question_id,
                )
            )
        ).first()

        if existing:
            existing.selected_option_id = request_in.selected_option_id
            existing.numerical_response = request_in.numerical_response
            existing.text_response = request_in.text_response
            existing.answered_at = now
            session.add(existing)
        else:
            answer = SimulationAnswer(
                session_id=sim_session.id,
                student_id=student_id,
                question_id=request_in.question_id,
                selected_option_id=request_in.selected_option_id,
                numerical_response=request_in.numerical_response,
                text_response=request_in.text_response,
                answered_at=now,
            )
            session.add(answer)

        await session.commit()

        return SaveAnswerResponse(
            session_id=sim_session.id,
            question_id=request_in.question_id,
            saved_at=now,
            status="saved",
        )

    @classmethod
    async def submit_simulation(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
    ) -> SimulationSubmitResponse:
        sim_session = (
            await session.exec(
                select(SimulationSession).where(
                    SimulationSession.id == session_id,
                    SimulationSession.student_id == student_id,
                )
            )
        ).first()
        if not sim_session:
            raise ValueError(f"Simulation session '{session_id}' not found.")

        now = datetime.now(timezone.utc)
        if not sim_session.submitted_at:
            sim_session.submitted_at = now
            sim_session.status = SimulationStatus.SUBMITTED
            session.add(sim_session)
            await session.commit()

        # Grade the paper
        report = await AutoGradingService.grade_session(session, sim_session)
        return await cls._build_submit_response(session, sim_session, report)

    @classmethod
    async def get_simulation_report(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
    ) -> SimulationSubmitResponse:
        sim_session = (
            await session.exec(
                select(SimulationSession).where(
                    SimulationSession.id == session_id,
                    SimulationSession.student_id == student_id,
                )
            )
        ).first()
        if not sim_session:
            raise ValueError(f"Simulation session '{session_id}' not found.")

        report = (
            await session.exec(select(SimulationReport).where(SimulationReport.session_id == sim_session.id))
        ).first()
        if not report:
            # If submitted or expired but not yet graded, grade now
            report = await AutoGradingService.grade_session(session, sim_session)

        return await cls._build_submit_response(session, sim_session, report)

    @classmethod
    async def list_student_simulations(
        cls,
        session: AsyncSession,
        student_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> SimulationSessionListResponse:
        stmt = (
            select(SimulationSession)
            .where(SimulationSession.student_id == student_id)
            .order_by(desc(SimulationSession.started_at))
            .offset(offset)
            .limit(limit)
        )
        sessions_db = (await session.exec(stmt)).all()

        summaries = []
        for s in sessions_db:
            blueprint = (await session.exec(select(ExamBlueprint).where(ExamBlueprint.id == s.blueprint_id))).first()
            report = (await session.exec(select(SimulationReport).where(SimulationReport.session_id == s.id))).first()
            summaries.append(
                SimulationSessionSummary(
                    id=s.id,
                    blueprint_id=s.blueprint_id,
                    blueprint_title=blueprint.title if blueprint else "Mock Exam",
                    status=s.status,
                    total_marks_available=report.total_marks_available if report else None,
                    earned_marks=report.earned_marks if report else None,
                    percentage_score=report.percentage_score if report else None,
                    is_passed=report.is_passed if report else None,
                    started_at=s.started_at,
                    submitted_at=s.submitted_at,
                )
            )

        total = len((await session.exec(select(SimulationSession).where(SimulationSession.student_id == student_id))).all())
        return SimulationSessionListResponse(simulations=summaries, total=total)

    # ==========================================================================
    # Helper Projection Builders
    # ==========================================================================

    @classmethod
    async def _build_session_response(
        cls,
        session: AsyncSession,
        sim_session: SimulationSession,
        blueprint: ExamBlueprint,
        questions: List[Question],
    ) -> SimulationSessionResponse:
        now = datetime.now(timezone.utc)
        expires = sim_session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        remaining = max(0, int((expires - now).total_seconds()))

        # Fetch options for sanitized projection
        q_ids = [q.id for q in questions]
        opt_stmt = select(QuestionOption).where(QuestionOption.question_id.in_(q_ids))
        options_db = (await session.exec(opt_stmt)).all()
        q_opts_map: Dict[str, List[QuestionOption]] = {}
        for opt in options_db:
            q_opts_map.setdefault(opt.question_id, []).append(opt)

        # Fetch topics for titles
        t_ids = list({q.topic_id for q in questions})
        topics_db = (await session.exec(select(Topic).where(Topic.id.in_(t_ids)))).all()
        topic_map = {t.id: t.title for t in topics_db}

        sanitized_questions = []
        for q in questions:
            opts = q_opts_map.get(q.id, [])
            opts.sort(key=lambda o: o.order)
            sanitized_opts = [
                SanitizedOption(
                    id=o.id,
                    option_key=o.option_key,
                    option_text=o.content,
                    order=o.order,
                )
                for o in opts
            ]
            sanitized_questions.append(
                SanitizedQuestion(
                    id=q.id,
                    topic_id=q.topic_id,
                    topic_title=topic_map.get(q.topic_id),
                    prompt=q.prompt,
                    question_type=q.question_type,
                    marks=q.points or 1.0,
                    options=sanitized_opts,
                )
            )

        # Fetch saved answers
        ans_stmt = select(SimulationAnswer).where(SimulationAnswer.session_id == sim_session.id)
        answers = (await session.exec(ans_stmt)).all()
        saved_map = {
            a.question_id: {
                "selected_option_id": a.selected_option_id,
                "numerical_response": a.numerical_response,
                "text_response": a.text_response,
            }
            for a in answers
        }

        return SimulationSessionResponse(
            id=sim_session.id,
            blueprint_id=blueprint.id,
            exam_template_id=blueprint.exam_template_id,
            status=sim_session.status,
            duration_minutes=blueprint.duration_minutes,
            total_questions=len(sanitized_questions),
            total_marks=blueprint.total_marks,
            started_at=sim_session.started_at,
            expires_at=sim_session.expires_at,
            time_remaining_seconds=remaining,
            questions=sanitized_questions,
            saved_answers=saved_map,
        )

    @classmethod
    async def _build_submit_response(
        cls,
        session: AsyncSession,
        sim_session: SimulationSession,
        report: SimulationReport,
    ) -> SimulationSubmitResponse:
        # Time spent
        start = sim_session.started_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        end_time = sim_session.submitted_at or sim_session.expires_at
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        time_spent = int((end_time - start).total_seconds())

        # Load questions & options for detailed question result breakdown
        q_ids = sim_session.question_ids or []
        questions_db = (await session.exec(select(Question).where(Question.id.in_(q_ids)))).all()
        q_map = {q.id: q for q in questions_db}

        opt_stmt = select(QuestionOption).where(QuestionOption.question_id.in_(q_ids))
        options_db = (await session.exec(opt_stmt)).all()
        opt_map = {o.id: o for o in options_db}

        ans_stmt = select(SimulationAnswer).where(SimulationAnswer.session_id == sim_session.id)
        answers_db = (await session.exec(ans_stmt)).all()
        ans_map = {a.question_id: a for a in answers_db}

        t_ids = list({q.topic_id for q in questions_db})
        topics_db = (await session.exec(select(Topic).where(Topic.id.in_(t_ids)))).all()
        topic_map = {t.id: t.title for t in topics_db}

        question_results = []
        for q_id in q_ids:
            q = q_map.get(q_id)
            if not q:
                continue

            ans = ans_map.get(q_id)
            sel_opt = opt_map.get(ans.selected_option_id) if (ans and ans.selected_option_id) else None
            correct_opts = [o for o in options_db if o.question_id == q_id and o.is_correct]
            corr_opt = correct_opts[0] if correct_opts else None

            question_results.append(
                QuestionResultDetail(
                    question_id=q.id,
                    topic_id=q.topic_id,
                    topic_title=topic_map.get(q.topic_id),
                    prompt=q.prompt,
                    question_type=q.question_type,
                    selected_option_id=ans.selected_option_id if ans else None,
                    selected_option_key=sel_opt.option_key if sel_opt else None,
                    correct_option_id=corr_opt.id if corr_opt else None,
                    correct_option_key=corr_opt.option_key if corr_opt else None,
                    student_numerical=ans.numerical_response if ans else None,
                    correct_numerical=None,
                    is_correct=ans.is_correct if ans else False,
                    marks_awarded=ans.marks_awarded if ans else 0.0,
                    marks_available=q.points or 1.0,
                    explanation=q.explanation,
                )
            )

        topic_summaries = [TopicPerformanceSummary(**t) for t in (report.topic_breakdown or [])]

        return SimulationSubmitResponse(
            session_id=sim_session.id,
            blueprint_id=sim_session.blueprint_id,
            status=sim_session.status,
            total_marks_available=report.total_marks_available,
            earned_marks=report.earned_marks,
            percentage_score=report.percentage_score,
            is_passed=report.is_passed,
            time_spent_seconds=time_spent,
            topic_breakdown=topic_summaries,
            question_results=question_results,
            submitted_at=sim_session.submitted_at or sim_session.expires_at,
        )
