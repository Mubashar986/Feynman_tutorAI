from datetime import datetime, timedelta, timezone
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.mastery.models import MasteryStatus, StudentTopicMastery
from backend.app.readiness.calculator import ReadinessScoreCalculator
from backend.app.readiness.models import ExamReadinessSnapshot
from backend.app.readiness.service import ExamReadinessService
from backend.app.revision.models import SpacedReviewCard
from backend.app.simulation.models import (
    BlueprintTopicDistribution,
    ExamBlueprint,
    SimulationReport,
    SimulationSession,
    SimulationStatus,
)


# ==============================================================================
# 1. Pure Mathematical Engine Tests
# ==============================================================================

def test_readiness_calculator_psychometric_fusion():
    topics = [
        {"target_weight": 0.60, "p_mastery": 0.90, "retrievability": 0.80},
        {"target_weight": 0.40, "p_mastery": 0.50, "retrievability": 0.60},
    ]

    # Mastery: (0.60 * 0.90 + 0.40 * 0.50) * 100 = (0.54 + 0.20) * 100 = 74.0%
    mastery_score = ReadinessScoreCalculator.calculate_topic_mastery_component(topics)
    assert mastery_score == 74.0

    # Retention: (0.60 * 0.80 + 0.40 * 0.60) * 100 = (0.48 + 0.24) * 100 = 72.0%
    retention_score = ReadinessScoreCalculator.calculate_retention_component(topics)
    assert retention_score == 72.0

    # Simulation with decay rate: reports [80.0, 70.0]
    sim_reports = [{"percentage_score": 80.0}, {"percentage_score": 70.0}]
    sim_score = ReadinessScoreCalculator.calculate_simulation_component(sim_reports)
    assert sim_score is not None
    assert 70.0 < sim_score <= 80.0

    # Full Composite calculation (40% Mastery, 20% Retention, 25% Sim, 15% Pacing)
    composite, breakdown = ReadinessScoreCalculator.calculate_composite_readiness(
        mastery_score=74.0,
        retention_score=72.0,
        simulation_score=sim_score,
        pacing_score=85.0,
    )
    assert 0.0 <= composite <= 100.0
    assert breakdown.mastery_score == 74.0
    assert breakdown.retention_score == 72.0


def test_readiness_calculator_sigmoid_pass_probability():
    # Centered at passing threshold (60%) -> P(Pass) = 50%
    prob_at_threshold = ReadinessScoreCalculator.calculate_pass_probability(60.0, passing_threshold=60.0)
    assert prob_at_threshold == 0.50

    # High readiness (80%) -> P(Pass) > 85%
    prob_high = ReadinessScoreCalculator.calculate_pass_probability(80.0, passing_threshold=60.0)
    assert prob_high > 0.85

    # Low readiness (40%) -> P(Pass) < 15%
    prob_low = ReadinessScoreCalculator.calculate_pass_probability(40.0, passing_threshold=60.0)
    assert prob_low < 0.15


def test_readiness_calculator_high_roi_ranking():
    topics = [
        {
            "topic_id": "top_1",
            "topic_title": "Core Mechanics",
            "target_weight": 0.50,  # 50% exam weight
            "p_mastery": 0.20,       # Low mastery
            "retrievability": 0.50,
            "estimated_hours": 2.0,
        },
        {
            "topic_id": "top_2",
            "topic_title": "Minor Elective",
            "target_weight": 0.05,  # 5% exam weight
            "p_mastery": 0.10,       # Low mastery
            "retrievability": 0.50,
            "estimated_hours": 2.0,
        },
        {
            "topic_id": "top_3",
            "topic_title": "Electromagnetism",
            "target_weight": 0.45,  # 45% exam weight
            "p_mastery": 0.95,       # High mastery
            "retrievability": 0.90,
            "estimated_hours": 3.0,
        },
    ]

    recs = ReadinessScoreCalculator.rank_high_roi_topics(topics, top_n=2)
    assert len(recs) == 2
    # Core Mechanics (50% weight, 20% mastery) must be ranked #1
    assert recs[0].topic_id == "top_1"
    assert recs[0].potential_score_gain > 30.0


# ==============================================================================
# 2. Service & Multi-Source Telemetry Aggregation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_readiness_service_multi_source_aggregation_and_snapshot(db_session: AsyncSession):
    # 1. Create Exam & Syllabus
    exam = ExamTemplate(code=f"READ_EXAM_{uuid.uuid4().hex[:6]}", title="Readiness Test Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic_1 = Topic(subject_id=subject.id, title="Optics", order=1, estimated_hours=4.0)
    topic_2 = Topic(subject_id=subject.id, title="Thermodynamics", order=2, estimated_hours=3.0)
    db_session.add(topic_1)
    db_session.add(topic_2)
    await db_session.flush()

    # 2. Create Blueprint (70% Optics, 30% Thermodynamics, passing 65%)
    blueprint = ExamBlueprint(
        exam_template_id=exam.id,
        code=f"BP_READ_{uuid.uuid4().hex[:6]}",
        title="Physics Blueprint",
        duration_minutes=60,
        total_questions=10,
        total_marks=10.0,
        passing_percentage=65.0,
    )
    db_session.add(blueprint)
    await db_session.flush()

    dist_1 = BlueprintTopicDistribution(blueprint_id=blueprint.id, topic_id=topic_1.id, target_weight=0.70, target_question_count=7)
    dist_2 = BlueprintTopicDistribution(blueprint_id=blueprint.id, topic_id=topic_2.id, target_weight=0.30, target_question_count=3)
    db_session.add(dist_1)
    db_session.add(dist_2)
    await db_session.flush()

    student_id = f"student_{uuid.uuid4().hex[:8]}"

    # 3. Add Student Mastery: Optics (0.85 mastery), Thermo (0.30 mastery)
    m1 = StudentTopicMastery(
        student_id=student_id,
        exam_template_id=exam.id,
        topic_id=topic_1.id,
        mastery_probability=0.85,
        status=MasteryStatus.MASTERED,
    )
    m2 = StudentTopicMastery(
        student_id=student_id,
        exam_template_id=exam.id,
        topic_id=topic_2.id,
        mastery_probability=0.30,
        status=MasteryStatus.PRACTICING,
    )
    db_session.add(m1)
    db_session.add(m2)

    # 4. Add Spaced Repetition Item for Optics
    sr1 = SpacedReviewCard(
        student_id=student_id,
        exam_template_id=exam.id,
        topic_id=topic_1.id,
        question_id=f"q_{uuid.uuid4().hex[:6]}",
        stability=30.0,
        last_reviewed_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    db_session.add(sr1)

    # 5. Add Completed Simulation Session & Report
    sim_session = SimulationSession(
        student_id=student_id,
        blueprint_id=blueprint.id,
        exam_template_id=exam.id,
        status=SimulationStatus.GRADED,
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        submitted_at=datetime.now(timezone.utc) - timedelta(hours=1),
        question_ids=["q1", "q2"],
    )
    db_session.add(sim_session)
    await db_session.flush()

    sim_report = SimulationReport(
        session_id=sim_session.id,
        student_id=student_id,
        blueprint_id=blueprint.id,
        total_marks_available=10.0,
        earned_marks=8.0,
        percentage_score=80.0,
        is_passed=True,
    )
    db_session.add(sim_report)
    await db_session.commit()

    # 6. Execute Readiness Assessment
    report = await ExamReadinessService.calculate_readiness(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam.id,
    )

    assert report.exam_template_id == exam.id
    assert report.overall_readiness_score > 60.0
    assert report.pass_probability > 0.50
    assert len(report.topic_breakdown) == 2
    assert len(report.high_roi_recommendations) > 0

    # Verify database snapshot was saved
    snapshots = (
        await db_session.exec(
            select(ExamReadinessSnapshot).where(
                ExamReadinessSnapshot.student_id == student_id,
                ExamReadinessSnapshot.exam_template_id == exam.id,
            )
        )
    ).all()
    assert len(snapshots) == 1
    assert snapshots[0].overall_readiness_score == report.overall_readiness_score


# ==============================================================================
# 3. REST API & Tenant Isolation Tests (PRD Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_readiness_api_endpoints_and_tenant_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Setup Syllabus Data
    exam = ExamTemplate(code=f"API_READ_{uuid.uuid4().hex[:6]}", title="API Readiness Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Chemistry")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Organic Reactions", order=1)
    db_session.add(topic)
    await db_session.commit()

    # 2. Register Student A & Student B
    email_a = f"read.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Readiness Student A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    email_b = f"read.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Readiness Student B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # 3. Student A Evaluates Readiness (GET /api/v1/readiness/{exam_id})
    res_a = await async_client.get(
        f"/api/v1/readiness/{exam.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200
    report_data = res_a.json()
    assert report_data["exam_template_id"] == exam.id
    assert "overall_readiness_score" in report_data
    assert "pass_probability" in report_data
    assert "components" in report_data

    # 4. Student A Checks History (GET /api/v1/readiness/{exam_id}/history)
    hist_a = await async_client.get(
        f"/api/v1/readiness/{exam.id}/history",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert hist_a.status_code == 200
    assert hist_a.json()["total_snapshots"] >= 1

    # 5. Student B Checks History -> Must be isolated (0 snapshots for Student B)
    hist_b = await async_client.get(
        f"/api/v1/readiness/{exam.id}/history",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert hist_b.status_code == 200
    assert hist_b.json()["total_snapshots"] == 0

    # 6. Unauthenticated Request Blocked (401)
    unauth_res = await async_client.get(f"/api/v1/readiness/{exam.id}")
    assert unauth_res.status_code == 401
