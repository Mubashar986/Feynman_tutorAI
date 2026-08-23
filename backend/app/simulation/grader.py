import logging
import math
from typing import Dict, List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import Topic
from backend.app.questions.models import Question, QuestionOption, QuestionType
from backend.app.simulation.models import (
    ExamBlueprint,
    SimulationAnswer,
    SimulationReport,
    SimulationSession,
    SimulationStatus,
)

logger = logging.getLogger("adaptive_exam_platform.simulation.grader")


class AutoGradingService:
    """
    Deterministic scoring and topic performance aggregator for simulated exams (PRD FR-020).
    """

    @classmethod
    async def grade_session(
        cls,
        session: AsyncSession,
        sim_session: SimulationSession,
    ) -> SimulationReport:
        # 1. Fetch Blueprint
        blueprint = (await session.exec(select(ExamBlueprint).where(ExamBlueprint.id == sim_session.blueprint_id))).first()
        passing_percentage = blueprint.passing_percentage if blueprint else 60.0

        # 2. Fetch Questions & Options
        question_ids = sim_session.question_ids or []
        questions_db = []
        if question_ids:
            q_stmt = select(Question).where(Question.id.in_(question_ids))
            questions_db = (await session.exec(q_stmt)).all()
        q_map: Dict[str, Question] = {q.id: q for q in questions_db}

        # Fetch options for all MCQ questions
        opt_stmt = select(QuestionOption).where(QuestionOption.question_id.in_(question_ids))
        options_db = (await session.exec(opt_stmt)).all()
        q_options_map: Dict[str, List[QuestionOption]] = {}
        for opt in options_db:
            q_options_map.setdefault(opt.question_id, []).append(opt)

        # 3. Fetch Student Answers
        ans_stmt = select(SimulationAnswer).where(SimulationAnswer.session_id == sim_session.id)
        answers_db = (await session.exec(ans_stmt)).all()
        ans_map: Dict[str, SimulationAnswer] = {a.question_id: a for a in answers_db}

        # 4. Deterministic Item-by-Item Grading
        total_marks_available = 0.0
        earned_marks = 0.0

        # Topic aggregation containers: {topic_id: {"total_q": int, "total_marks": float, "earned_marks": float}}
        topic_stats: Dict[str, Dict[str, float]] = {}

        for q_id in question_ids:
            question = q_map.get(q_id)
            if not question:
                continue

            q_marks = question.points or 1.0
            total_marks_available += q_marks

            # Init topic stat
            t_stat = topic_stats.setdefault(
                question.topic_id,
                {"total_q": 0, "total_marks": 0.0, "earned_marks": 0.0},
            )
            t_stat["total_q"] += 1
            t_stat["total_marks"] += q_marks

            answer = ans_map.get(q_id)
            is_correct = False
            awarded = 0.0

            if answer:
                if question.question_type in (QuestionType.MCQ_SINGLE, QuestionType.MCQ_MULTI):
                    opts = q_options_map.get(q_id, [])
                    correct_opts = [o for o in opts if o.is_correct]
                    if correct_opts and answer.selected_option_id:
                        if answer.selected_option_id in [o.id for o in correct_opts]:
                            is_correct = True
                            awarded = q_marks

                elif question.question_type == QuestionType.NUMERICAL:
                    opts = q_options_map.get(q_id, [])
                    correct_opts = [o for o in opts if o.is_correct]
                    if correct_opts and answer.numerical_response is not None:
                        try:
                            val_sub = float(answer.numerical_response)
                            # Parse float from correct option content or explanation
                            val_true = float(correct_opts[0].content.strip().replace("$", ""))
                            if math.isclose(val_sub, val_true, abs_tol=0.05, rel_tol=1e-2):
                                is_correct = True
                                awarded = q_marks
                        except (ValueError, TypeError):
                            is_correct = False
                else:
                    # Free response or other: fallback exact match if text provided
                    if answer.text_response and question.correct_answer_value:
                        if answer.text_response.strip().lower() == question.correct_answer_value.strip().lower():
                            is_correct = True
                            awarded = q_marks

                # Update answer record
                answer.is_correct = is_correct
                answer.marks_awarded = awarded
                session.add(answer)

            if is_correct:
                earned_marks += awarded
                t_stat["earned_marks"] += awarded

        # 5. Build Topic Performance Breakdown
        topic_ids = list(topic_stats.keys())
        topics_db = []
        if topic_ids:
            topics_db = (await session.exec(select(Topic).where(Topic.id.in_(topic_ids)))).all()
        topic_title_map = {t.id: t.title for t in topics_db}

        topic_breakdown = []
        for t_id, stats in topic_stats.items():
            t_tot = stats["total_marks"]
            t_earn = stats["earned_marks"]
            t_pct = (t_earn / t_tot * 100.0) if t_tot > 0 else 0.0
            topic_breakdown.append(
                {
                    "topic_id": t_id,
                    "topic_title": topic_title_map.get(t_id, "Syllabus Topic"),
                    "total_questions": stats["total_q"],
                    "total_marks": t_tot,
                    "earned_marks": t_earn,
                    "percentage": round(t_pct, 2),
                }
            )

        percentage_score = round((earned_marks / total_marks_available * 100.0), 2) if total_marks_available > 0 else 0.0
        is_passed = percentage_score >= passing_percentage

        # 6. Persist or Update SimulationReport
        existing_report = (
            await session.exec(select(SimulationReport).where(SimulationReport.session_id == sim_session.id))
        ).first()

        if existing_report:
            existing_report.total_marks_available = total_marks_available
            existing_report.earned_marks = earned_marks
            existing_report.percentage_score = percentage_score
            existing_report.is_passed = is_passed
            existing_report.topic_breakdown = topic_breakdown
            report = existing_report
        else:
            report = SimulationReport(
                session_id=sim_session.id,
                student_id=sim_session.student_id,
                blueprint_id=sim_session.blueprint_id,
                total_marks_available=total_marks_available,
                earned_marks=earned_marks,
                percentage_score=percentage_score,
                is_passed=is_passed,
                topic_breakdown=topic_breakdown,
            )
            session.add(report)

        # 7. Update Session Status to GRADED
        sim_session.status = SimulationStatus.GRADED
        session.add(sim_session)
        await session.commit()
        await session.refresh(report)

        logger.info(
            f"Graded simulation session {sim_session.id} for student {sim_session.student_id}: "
            f"{earned_marks}/{total_marks_available} ({percentage_score}%) — Passed: {is_passed}"
        )

        return report
