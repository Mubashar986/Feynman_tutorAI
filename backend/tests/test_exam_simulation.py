from datetime import datetime, timedelta, timezone
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.questions.models import Question, QuestionOption, QuestionType, ValidationStatus
from backend.app.simulation.assembler import StratifiedBlueprintAssembler
from backend.app.simulation.grader import AutoGradingService
from backend.app.simulation.models import (
    BlueprintTopicDistribution,
    ExamBlueprint,
    SimulationAnswer,
    SimulationSession,
    SimulationStatus,
)
from backend.app.simulation.schemas import (
    BlueprintCreateRequest,
    BlueprintTopicWeightInput,
    SaveAnswerRequest,
    SimulationStartRequest,
)
from backend.app.simulation.service import ExamSimulationService


# ==============================================================================
# 1. Unit & Service Tests: Blueprint & Stratified Assembly
# ==============================================================================

@pytest.mark.asyncio
async def test_blueprint_creation_and_topic_quotas(db_session: AsyncSession):
    exam = ExamTemplate(code=f"BP_EXAM_{uuid.uuid4().hex[:6]}", title="Blueprint Test Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic_1 = Topic(subject_id=subject.id, title="Kinematics", order=1)
    topic_2 = Topic(subject_id=subject.id, title="Dynamics", order=2)
    db_session.add(topic_1)
    db_session.add(topic_2)
    await db_session.commit()

    req = BlueprintCreateRequest(
        exam_template_id=exam.id,
        code=f"BP_CODE_{uuid.uuid4().hex[:6]}",
        title="Physics Paper 1 Mock",
        duration_minutes=60,
        total_questions=10,
        total_marks=10.0,
        passing_percentage=60.0,
        topic_distributions=[
            BlueprintTopicWeightInput(topic_id=topic_1.id, target_weight=0.60),
            BlueprintTopicWeightInput(topic_id=topic_2.id, target_weight=0.40),
        ],
    )

    res = await ExamSimulationService.create_blueprint(db_session, req)
    assert res.id is not None
    assert res.total_questions == 10
    assert len(res.topic_distributions) == 2

    # Check quotas: 60% of 10 = 6, 40% of 10 = 4
    dist_map = {d.topic_id: d.target_question_count for d in res.topic_distributions}
    assert dist_map[topic_1.id] == 6
    assert dist_map[topic_2.id] == 4


@pytest.mark.asyncio
async def test_stratified_paper_assembler(db_session: AsyncSession):
    # 1. Setup Syllabus Data
    exam = ExamTemplate(code=f"STRAT_EXAM_{uuid.uuid4().hex[:6]}", title="Stratified Assembly Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic_a = Topic(subject_id=subject.id, title="Waves", order=1)
    topic_b = Topic(subject_id=subject.id, title="Electricity", order=2)
    db_session.add(topic_a)
    db_session.add(topic_b)
    await db_session.flush()

    # 2. Add Questions for Topic A (4 questions) and Topic B (4 questions)
    for i in range(4):
        qa = Question(
            exam_template_id=exam.id,
            topic_id=topic_a.id,
            prompt=f"Waves Question {i+1}",
            explanation=f"Waves explanation {i+1}",
            question_type=QuestionType.MCQ_SINGLE,
            validation_status=ValidationStatus.VALIDATED,
        )
        qb = Question(
            exam_template_id=exam.id,
            topic_id=topic_b.id,
            prompt=f"Electricity Question {i+1}",
            explanation=f"Electricity explanation {i+1}",
            question_type=QuestionType.MCQ_SINGLE,
            validation_status=ValidationStatus.VALIDATED,
        )
        db_session.add(qa)
        db_session.add(qb)
    await db_session.commit()

    # 3. Create Blueprint: Total 4 questions (50% Waves, 50% Electricity)
    blueprint = ExamBlueprint(
        exam_template_id=exam.id,
        code=f"BP_STRAT_{uuid.uuid4().hex[:6]}",
        title="Balanced Physics Mock",
        duration_minutes=45,
        total_questions=4,
        total_marks=4.0,
    )
    db_session.add(blueprint)
    await db_session.flush()

    dist_a = BlueprintTopicDistribution(blueprint_id=blueprint.id, topic_id=topic_a.id, target_weight=0.5, target_question_count=2)
    dist_b = BlueprintTopicDistribution(blueprint_id=blueprint.id, topic_id=topic_b.id, target_weight=0.5, target_question_count=2)
    db_session.add(dist_a)
    db_session.add(dist_b)
    await db_session.commit()

    # 4. Run Assembler
    paper = await StratifiedBlueprintAssembler.assemble_paper(db_session, blueprint)
    assert len(paper) == 4
    topic_a_count = sum(1 for q in paper if q.topic_id == topic_a.id)
    topic_b_count = sum(1 for q in paper if q.topic_id == topic_b.id)
    assert topic_a_count == 2
    assert topic_b_count == 2
    assert len(set(q.id for q in paper)) == 4


# ==============================================================================
# 2. Service & Auto-Grading Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_deterministic_auto_grading_mcq_and_numerical(db_session: AsyncSession):
    # 1. Setup Syllabus Data
    exam = ExamTemplate(code=f"GRADE_EXAM_{uuid.uuid4().hex[:6]}", title="Grading Test Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Mechanics", order=1)
    db_session.add(topic)
    await db_session.flush()

    # 2. Add 1 MCQ Question and 1 Numerical Question
    q_mcq = Question(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="What is the unit of Force?",
        explanation="Force is measured in Newtons.",
        question_type=QuestionType.MCQ_SINGLE,
        points=1.0,
        validation_status=ValidationStatus.VALIDATED,
    )
    db_session.add(q_mcq)
    await db_session.flush()

    opt_correct = QuestionOption(question_id=q_mcq.id, option_key="A", content="Newton ($N$)", is_correct=True, order=1)
    opt_wrong = QuestionOption(question_id=q_mcq.id, option_key="B", content="Joule ($J$)", is_correct=False, order=2)
    db_session.add(opt_correct)
    db_session.add(opt_wrong)

    q_num = Question(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="Calculate acceleration if $F = 20\\text{ N}$ and $m = 4\\text{ kg}$.",
        explanation="Acceleration $a = F/m = 20/4 = 5.0\\text{ m/s}^2$.",
        question_type=QuestionType.NUMERICAL,
        points=2.0,
        validation_status=ValidationStatus.VALIDATED,
    )
    db_session.add(q_num)
    await db_session.flush()

    opt_num_correct = QuestionOption(question_id=q_num.id, option_key="NUM", content="5.0", is_correct=True, order=1)
    db_session.add(opt_num_correct)
    await db_session.commit()

    blueprint = ExamBlueprint(
        exam_template_id=exam.id,
        code=f"BP_GRADE_{uuid.uuid4().hex[:6]}",
        title="Grading Mock",
        duration_minutes=30,
        total_questions=2,
        total_marks=3.0,
        passing_percentage=60.0,
    )
    db_session.add(blueprint)
    await db_session.commit()

    student_id = f"student_{uuid.uuid4().hex[:8]}"

    # 3. Create Simulation Session
    sim_session = SimulationSession(
        student_id=student_id,
        blueprint_id=blueprint.id,
        exam_template_id=exam.id,
        status=SimulationStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        question_ids=[q_mcq.id, q_num.id],
    )
    db_session.add(sim_session)
    await db_session.flush()

    # 4. Student Submits: Correct MCQ Option A + Correct Numerical 5.02 (within 0.05 tolerance)
    ans_1 = SimulationAnswer(
        session_id=sim_session.id,
        student_id=student_id,
        question_id=q_mcq.id,
        selected_option_id=opt_correct.id,
        answered_at=datetime.now(timezone.utc),
    )
    ans_2 = SimulationAnswer(
        session_id=sim_session.id,
        student_id=student_id,
        question_id=q_num.id,
        numerical_response=5.02,
        answered_at=datetime.now(timezone.utc),
    )
    db_session.add(ans_1)
    db_session.add(ans_2)
    await db_session.commit()

    # 5. Run Auto-Grader
    report = await AutoGradingService.grade_session(db_session, sim_session)
    assert report.earned_marks == 3.0
    assert report.total_marks_available == 3.0
    assert report.percentage_score == 100.0
    assert report.is_passed is True
    assert len(report.topic_breakdown) == 1
    assert report.topic_breakdown[0]["percentage"] == 100.0


@pytest.mark.asyncio
async def test_server_enforced_timer_expiry(db_session: AsyncSession):
    exam = ExamTemplate(code=f"EXP_EXAM_{uuid.uuid4().hex[:6]}", title="Expiry Test Exam")
    db_session.add(exam)
    await db_session.flush()

    blueprint = ExamBlueprint(
        exam_template_id=exam.id,
        code=f"BP_EXP_{uuid.uuid4().hex[:6]}",
        title="Expired Mock",
        duration_minutes=30,
        total_questions=1,
        total_marks=1.0,
    )
    db_session.add(blueprint)
    await db_session.commit()

    student_id = f"student_{uuid.uuid4().hex[:8]}"

    # Session created with expires_at in the past
    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    sim_session = SimulationSession(
        student_id=student_id,
        blueprint_id=blueprint.id,
        exam_template_id=exam.id,
        status=SimulationStatus.IN_PROGRESS,
        started_at=past_time - timedelta(minutes=30),
        expires_at=past_time,
        question_ids=["q_dummy_1"],
    )
    db_session.add(sim_session)
    await db_session.commit()

    # Attempting to save an answer after expiry must raise ValueError
    with pytest.raises(ValueError, match="expired"):
        await ExamSimulationService.save_answer(
            session=db_session,
            student_id=student_id,
            session_id=sim_session.id,
            request_in=SaveAnswerRequest(question_id="q_dummy_1", numerical_response=42.0),
        )


# ==============================================================================
# 3. REST API, Sanitization & Tenant Isolation Tests (Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_full_simulation_api_suite_and_tenant_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Setup Syllabus Data
    exam = ExamTemplate(code=f"API_SIM_{uuid.uuid4().hex[:6]}", title="API Simulation Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Optics", order=1)
    db_session.add(topic)
    await db_session.flush()

    q1 = Question(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="What is the speed of light in vacuum?",
        question_type=QuestionType.MCQ_SINGLE,
        points=1.0,
        explanation="Light speed in vacuum is $c = 3 \\times 10^8\\text{ m/s}$.",
        validation_status=ValidationStatus.VALIDATED,
    )
    db_session.add(q1)
    await db_session.flush()

    opt_a = QuestionOption(question_id=q1.id, option_key="A", content="$3 \\times 10^8\\text{ m/s}$", is_correct=True, order=1)
    opt_b = QuestionOption(question_id=q1.id, option_key="B", content="$3 \\times 10^6\\text{ m/s}$", is_correct=False, order=2)
    db_session.add(opt_a)
    db_session.add(opt_b)

    blueprint = ExamBlueprint(
        exam_template_id=exam.id,
        code=f"BP_API_{uuid.uuid4().hex[:6]}",
        title="Full Simulation Paper 1",
        duration_minutes=60,
        total_questions=1,
        total_marks=1.0,
        passing_percentage=50.0,
    )
    db_session.add(blueprint)
    await db_session.flush()

    dist = BlueprintTopicDistribution(blueprint_id=blueprint.id, topic_id=topic.id, target_weight=1.0, target_question_count=1)
    db_session.add(dist)
    await db_session.commit()

    # 2. Register Student A & Student B
    email_a = f"sim.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Sim Student A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    email_b = f"sim.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Sim Student B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # 3. Student A Starts Mock Exam (POST /api/v1/simulations/start)
    start_res = await async_client.post(
        "/api/v1/simulations/start",
        json={"blueprint_id": blueprint.id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert start_res.status_code == 201
    paper_data = start_res.json()
    session_id = paper_data["id"]
    assert paper_data["total_questions"] == 1
    assert paper_data["status"] == "in_progress"

    # Verify Sanitization: Options must NOT contain 'is_correct'
    options_delivered = paper_data["questions"][0]["options"]
    for opt in options_delivered:
        assert "is_correct" not in opt
        assert "distractor_explanation" not in opt

    # 4. Student A Auto-Saves Answer (POST /api/v1/simulations/{session_id}/save-answer)
    save_res = await async_client.post(
        f"/api/v1/simulations/{session_id}/save-answer",
        json={"question_id": q1.id, "selected_option_id": opt_a.id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "saved"

    # 5. Student A Submits Paper (POST /api/v1/simulations/{session_id}/submit)
    submit_res = await async_client.post(
        f"/api/v1/simulations/{session_id}/submit",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert submit_res.status_code == 200
    scorecard = submit_res.json()
    assert scorecard["earned_marks"] == 1.0
    assert scorecard["percentage_score"] == 100.0
    assert scorecard["is_passed"] is True
    assert len(scorecard["question_results"]) == 1
    assert scorecard["question_results"][0]["is_correct"] is True

    # 6. Student A Fetches Report (GET /api/v1/simulations/{session_id}/report)
    report_res = await async_client.get(
        f"/api/v1/simulations/{session_id}/report",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert report_res.status_code == 200
    assert report_res.json()["percentage_score"] == 100.0

    # 7. Student B Snoop Attempt on Student A's Session (Constraint #2 Isolation Check)
    snoop_res = await async_client.get(
        f"/api/v1/simulations/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert snoop_res.status_code == 404

    # 8. Unauthenticated Request Blocked (401)
    unauth_res = await async_client.post(
        "/api/v1/simulations/start",
        json={"blueprint_id": blueprint.id},
    )
    assert unauth_res.status_code == 401
