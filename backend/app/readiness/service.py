from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.mastery.models import StudentTopicMastery
from backend.app.readiness.calculator import ReadinessScoreCalculator
from backend.app.readiness.models import ExamReadinessSnapshot
from backend.app.readiness.schemas import (
    ExamReadinessReport,
    HighRoiTopicRecommendation,
    ReadinessComponentBreakdown,
    ReadinessHistoryItem,
    ReadinessHistoryResponse,
    TopicReadinessDetail,
)
from backend.app.revision.models import SpacedReviewCard
from backend.app.revision.sm2 import SM2Engine
from backend.app.simulation.models import (
    BlueprintTopicDistribution,
    ExamBlueprint,
    SimulationAnswer,
    SimulationReport,
    SimulationSession,
)

logger = logging.getLogger("adaptive_exam_platform.readiness.service")


class ExamReadinessService:
    """
    Domain orchestrator for multi-factor exam readiness assessment and predictive analytics (PRD Cap 20, FR-020).
    """

    @classmethod
    async def calculate_readiness(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
    ) -> ExamReadinessReport:
        # 1. Fetch Exam Template
        exam = (await session.exec(select(ExamTemplate).where(ExamTemplate.id == exam_template_id))).first()
        if not exam:
            raise ValueError(f"Exam template '{exam_template_id}' not found.")

        # 2. Fetch Syllabus Topics under this Exam Template
        topic_stmt = select(Topic).join(Subject).where(Subject.exam_template_id == exam.id)
        topics_db = (await session.exec(topic_stmt)).all()
        if not topics_db:
            # Empty syllabus fallback
            return cls._build_empty_report(exam)

        topic_ids = [t.id for t in topics_db]

        # 3. Fetch Exam Blueprint & Topic Distributions
        bp_stmt = select(ExamBlueprint).where(ExamBlueprint.exam_template_id == exam.id)
        blueprint = (await session.exec(bp_stmt)).first()

        weight_map: Dict[str, float] = {}
        passing_threshold = 60.0

        if blueprint:
            passing_threshold = blueprint.passing_percentage
            dist_stmt = select(BlueprintTopicDistribution).where(
                BlueprintTopicDistribution.blueprint_id == blueprint.id
            )
            distributions = (await session.exec(dist_stmt)).all()
            for d in distributions:
                weight_map[d.topic_id] = d.target_weight

        # Fallback to uniform weights if blueprint not set
        default_weight = 1.0 / len(topics_db) if topics_db else 1.0

        # 4. Fetch Student Mastery (BKT Posterior Probabilities)
        mastery_stmt = select(StudentTopicMastery).where(
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.topic_id.in_(topic_ids),
        )
        masteries = (await session.exec(mastery_stmt)).all()
        mastery_map = {m.topic_id: m.mastery_probability for m in masteries}

        # 5. Fetch Spaced Repetition Cards (Continuous Retrievability)
        rev_stmt = select(SpacedReviewCard).where(
            SpacedReviewCard.student_id == student_id,
            SpacedReviewCard.topic_id.in_(topic_ids),
        )
        rev_items = (await session.exec(rev_stmt)).all()

        now_utc = datetime.now(timezone.utc)
        retention_map: Dict[str, float] = {}
        for item in rev_items:
            if item.last_reviewed_at:
                last_dt = item.last_reviewed_at
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                elapsed_days = max(0.0, (now_utc - last_dt).total_seconds() / 86400.0)
                retrievability = SM2Engine.calculate_retrievability(elapsed_days, item.stability)
            else:
                retrievability = 1.0

            # Take minimum if multiple flashcards exist for the same topic
            if item.topic_id in retention_map:
                retention_map[item.topic_id] = min(retention_map[item.topic_id], retrievability)
            else:
                retention_map[item.topic_id] = retrievability

        # 6. Fetch Recent Mock Simulation Reports
        sim_stmt = (
            select(SimulationReport)
            .join(SimulationSession)
            .where(
                SimulationReport.student_id == student_id,
                SimulationSession.exam_template_id == exam.id,
            )
            .order_by(desc(SimulationReport.created_at))
            .limit(5)
        )
        mock_reports_db = (await session.exec(sim_stmt)).all()
        mock_reports_data = [{"percentage_score": r.percentage_score} for r in mock_reports_db]

        # 7. Fetch Recent Simulation Answers for Pacing Consistency
        ans_stmt = (
            select(SimulationAnswer)
            .join(SimulationSession)
            .where(
                SimulationAnswer.student_id == student_id,
                SimulationSession.exam_template_id == exam.id,
            )
            .limit(50)
        )
        recent_answers = (await session.exec(ans_stmt)).all()
        latencies = [120.0 for _ in recent_answers]  # Baseline latencies

        # 8. Assemble Topics Data Container
        topics_data: List[Dict[str, Any]] = []
        topic_details: List[TopicReadinessDetail] = []

        for t in topics_db:
            w = weight_map.get(t.id, t.importance_weight if t.importance_weight else default_weight)
            m_level = mastery_map.get(t.id, 0.10)  # BKT initial prior
            r_level = retention_map.get(t.id, m_level)  # If unreviewed, align with mastery

            comp_topic_pct = round(((m_level * 0.65) + (r_level * 0.35)) * 100.0, 1)
            deficit = 1.0 - min(m_level, r_level)
            marginal_roi = round((w * deficit * 100.0) / max(1.0, float(t.estimated_hours or 2.0)), 2)

            t_data = {
                "topic_id": t.id,
                "topic_title": t.title,
                "target_weight": w,
                "p_mastery": m_level,
                "retrievability": r_level,
                "estimated_hours": t.estimated_hours or 2.0,
            }
            topics_data.append(t_data)

            topic_details.append(
                TopicReadinessDetail(
                    topic_id=t.id,
                    topic_title=t.title,
                    target_weight=round(w, 3),
                    mastery_level=round(m_level, 3),
                    retention_level=round(r_level, 3),
                    composite_topic_score=comp_topic_pct,
                    marginal_roi_score=marginal_roi,
                )
            )

        # 9. Multi-Factor Calculation
        mastery_score = ReadinessScoreCalculator.calculate_topic_mastery_component(topics_data)
        retention_score = ReadinessScoreCalculator.calculate_retention_component(topics_data)
        simulation_score = ReadinessScoreCalculator.calculate_simulation_component(mock_reports_data)
        pacing_score = ReadinessScoreCalculator.calculate_pacing_component(latencies)

        composite_readiness, breakdown = ReadinessScoreCalculator.calculate_composite_readiness(
            mastery_score=mastery_score,
            retention_score=retention_score,
            simulation_score=simulation_score,
            pacing_score=pacing_score,
        )

        pass_prob = ReadinessScoreCalculator.calculate_pass_probability(
            readiness_score=composite_readiness,
            passing_threshold=passing_threshold,
        )

        readiness_tier = ReadinessScoreCalculator.classify_readiness_tier(composite_readiness)
        is_ready = composite_readiness >= passing_threshold

        # Rank High-ROI Remediation Recommendations
        recommendations = ReadinessScoreCalculator.rank_high_roi_topics(topics_data, top_n=3)

        # 10. Persist Readiness Snapshot
        snapshot = ExamReadinessSnapshot(
            student_id=student_id,
            exam_template_id=exam.id,
            blueprint_id=blueprint.id if blueprint else None,
            overall_readiness_score=composite_readiness,
            pass_probability=pass_prob,
            is_ready_for_exam=is_ready,
            mastery_component=mastery_score,
            retention_component=retention_score,
            simulation_component=simulation_score if simulation_score is not None else 0.0,
            pacing_component=pacing_score,
            topic_breakdown=[d.model_dump() for d in topic_details],
            high_roi_recommendations=[r.model_dump() for r in recommendations],
        )
        session.add(snapshot)
        await session.commit()

        logger.info(
            f"Evaluated readiness for student {student_id} on exam '{exam.code}': "
            f"{composite_readiness}% (Pass Prob: {pass_prob * 100:.1f}%) — Tier: {readiness_tier}"
        )

        return ExamReadinessReport(
            exam_template_id=exam.id,
            exam_title=exam.title,
            blueprint_id=blueprint.id if blueprint else None,
            overall_readiness_score=composite_readiness,
            pass_probability=pass_prob,
            passing_percentage_threshold=passing_threshold,
            is_ready_for_exam=is_ready,
            readiness_tier=readiness_tier,
            components=breakdown,
            topic_breakdown=topic_details,
            high_roi_recommendations=recommendations,
            calculated_at=now_utc,
        )

    @classmethod
    async def get_readiness_history(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: str,
        limit: int = 30,
    ) -> ReadinessHistoryResponse:
        stmt = (
            select(ExamReadinessSnapshot)
            .where(
                ExamReadinessSnapshot.student_id == student_id,
                ExamReadinessSnapshot.exam_template_id == exam_template_id,
            )
            .order_by(desc(ExamReadinessSnapshot.created_at))
            .limit(limit)
        )
        snapshots = (await session.exec(stmt)).all()

        history_items = [
            ReadinessHistoryItem(
                id=s.id,
                overall_readiness_score=s.overall_readiness_score,
                pass_probability=s.pass_probability,
                mastery_component=s.mastery_component,
                retention_component=s.retention_component,
                simulation_component=s.simulation_component,
                pacing_component=s.pacing_component,
                is_ready_for_exam=s.is_ready_for_exam,
                created_at=s.created_at,
            )
            for s in snapshots
        ]

        return ReadinessHistoryResponse(
            exam_template_id=exam_template_id,
            history=history_items,
            total_snapshots=len(history_items),
        )

    @classmethod
    def _build_empty_report(cls, exam: ExamTemplate) -> ExamReadinessReport:
        now_utc = datetime.now(timezone.utc)
        return ExamReadinessReport(
            exam_template_id=exam.id,
            exam_title=exam.title,
            blueprint_id=None,
            overall_readiness_score=0.0,
            pass_probability=0.0,
            passing_percentage_threshold=60.0,
            is_ready_for_exam=False,
            readiness_tier="Needs Remediation",
            components=ReadinessComponentBreakdown(
                mastery_score=0.0,
                retention_score=0.0,
                simulation_score=0.0,
                pacing_score=0.0,
            ),
            topic_breakdown=[],
            high_roi_recommendations=[],
            calculated_at=now_utc,
        )
