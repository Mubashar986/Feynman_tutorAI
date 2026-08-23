import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.mastery.bkt import BKTParameters, BKTEngine
from backend.app.mastery.models import MasteryStatus
from backend.app.mastery.schemas import RecordAttemptRequest
from backend.app.mastery.service import MasteryEngineService
from backend.app.questions.models import (
    DifficultyLevel,
    QuestionType,
)
from backend.app.questions.schemas import (
    QuestionCreate,
    QuestionOptionCreate,
)
from backend.app.questions.service import QuestionBankService


# ==============================================================================
# 1. BKT Mathematical Engine Unit Tests (PRD FR-003, Cap 3)
# ==============================================================================

def test_bkt_posterior_correct_answer():
    """Verifies that a correct answer on an MCQ updates mastery probability according to BKT Bayes formula."""
    params = BKTParameters(p_init=0.10, p_transit=0.15, p_guess=0.20, p_slip=0.10)
    
    # Prior = 0.10
    posterior = BKTEngine.compute_posterior(prior_probability=0.10, is_correct=True, params=params)
    
    # Step 1: P(L|Corr) = (0.10 * 0.90) / ((0.10 * 0.90) + (0.90 * 0.20)) = 0.09 / (0.09 + 0.18) = 0.3333
    # Step 2: P(L_1) = 0.3333 + (1 - 0.3333) * 0.15 = 0.3333 + 0.1000 = 0.4333
    assert abs(posterior - 0.4333) < 0.001


def test_bkt_posterior_incorrect_answer_slip():
    """Verifies that a high-mastery student making an error drops smoothly rather than crashing."""
    params = BKTParameters(p_init=0.10, p_transit=0.15, p_guess=0.20, p_slip=0.10)
    
    # Prior = 0.95
    posterior = BKTEngine.compute_posterior(prior_probability=0.95, is_correct=False, params=params)
    
    # Step 1: P(L|Incorr) = (0.95 * 0.10) / ((0.95 * 0.10) + (0.05 * 0.80)) = 0.095 / (0.095 + 0.040) = 0.7037
    # Step 2: P(L_1) = 0.7037 + (1 - 0.7037) * 0.15 = 0.7481
    assert abs(posterior - 0.7481) < 0.001


def test_bkt_consecutive_correct_streak_to_mastery():
    """Verifies that 3 consecutive correct answers from novice prior cross the MASTERED threshold (>=0.85)."""
    p = 0.10
    params = BKTParameters()

    # Attempt 1
    p1 = BKTEngine.compute_posterior(p, is_correct=True, params=params)
    status1 = BKTEngine.get_mastery_status(p1)
    diff1 = BKTEngine.get_target_difficulty(p1)
    assert p1 > 0.40
    assert status1 == MasteryStatus.PRACTICING
    assert diff1 == DifficultyLevel.MEDIUM

    # Attempt 2
    p2 = BKTEngine.compute_posterior(p1, is_correct=True, params=params)
    status2 = BKTEngine.get_mastery_status(p2)
    diff2 = BKTEngine.get_target_difficulty(p2)
    assert p2 > 0.70
    assert status2 == MasteryStatus.PROFICIENT
    assert diff2 == DifficultyLevel.HARD

    # Attempt 3
    p3 = BKTEngine.compute_posterior(p2, is_correct=True, params=params)
    status3 = BKTEngine.get_mastery_status(p3)
    diff3 = BKTEngine.get_target_difficulty(p3)
    assert p3 >= 0.85
    assert status3 == MasteryStatus.MASTERED
    assert diff3 in (DifficultyLevel.HARD, DifficultyLevel.CHALLENGE)


def test_bkt_numerical_question_guess_damping():
    """Verifies that answering a numerical question yields a higher mastery gain due to lower guess chance."""
    prior = 0.10
    
    # MCQ Guess = 0.20
    p_mcq, _, _ = BKTEngine.update_mastery(prior, is_correct=True, question_type=QuestionType.MCQ_SINGLE)
    
    # Numerical Guess = 0.05
    p_num, _, _ = BKTEngine.update_mastery(prior, is_correct=True, question_type=QuestionType.NUMERICAL)
    
    # Numerical correct answer should provide significantly stronger proof of knowledge
    assert p_num > p_mcq


# ==============================================================================
# 2. Integration Tests: Service & Database Persistence (Constraints #1, #2)
# ==============================================================================

@pytest.mark.asyncio
async def test_mastery_service_attempt_lifecycle(db_session: AsyncSession):
    # 1. Setup prerequisite Exam, Subject, Topic & Question
    exam = ExamTemplate(code=f"MST_{uuid.uuid4().hex[:6]}", title="Mastery Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Kinematics", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.MEDIUM,
        prompt="Velocity $v = u + at$. Calculate $v$ for $u=0, a=9.8, t=2$.",
        explanation="$v = 0 + 9.8(2) = 19.6\\text{ m/s}$.",
        options=[
            QuestionOptionCreate(option_key="A", content="19.6 m/s", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="9.8 m/s", is_correct=False, order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    student_id = f"stud_{uuid.uuid4().hex[:8]}"

    # 2. First Attempt (Correct)
    resp1 = await MasteryEngineService.record_attempt(
        session=db_session,
        student_id=student_id,
        attempt_in=RecordAttemptRequest(
            question_id=question.id,
            selected_option_key="A",
            is_correct=True,
            time_spent_seconds=45,
        ),
    )

    assert resp1.student_id == student_id
    assert resp1.topic_id == topic.id
    assert resp1.prior_mastery_probability == 0.10
    assert resp1.posterior_mastery_probability > 0.40
    assert resp1.status == MasteryStatus.PRACTICING
    assert resp1.current_streak == 1
    assert resp1.best_streak == 1
    assert resp1.total_attempts == 1
    assert resp1.correct_attempts == 1

    # 3. Second Attempt (Correct)
    resp2 = await MasteryEngineService.record_attempt(
        session=db_session,
        student_id=student_id,
        attempt_in=RecordAttemptRequest(
            question_id=question.id,
            selected_option_key="A",
            is_correct=True,
            time_spent_seconds=30,
        ),
    )
    assert resp2.posterior_mastery_probability > resp1.posterior_mastery_probability
    assert resp2.current_streak == 2
    assert resp2.best_streak == 2

    # 4. Third Attempt (Incorrect Slip)
    resp3 = await MasteryEngineService.record_attempt(
        session=db_session,
        student_id=student_id,
        attempt_in=RecordAttemptRequest(
            question_id=question.id,
            selected_option_key="B",
            is_correct=False,
            time_spent_seconds=15,
        ),
    )
    assert resp3.current_streak == 0  # Streak reset
    assert resp3.best_streak == 2     # Best streak preserved
    assert resp3.total_attempts == 3
    assert resp3.correct_attempts == 2

    # 5. Verify database records
    mastery_record = await MasteryEngineService.get_topic_mastery(db_session, student_id, topic.id)
    assert mastery_record is not None
    assert mastery_record.total_attempts == 3
    assert mastery_record.best_streak == 2


# ==============================================================================
# 3. REST API & Student Isolation Tests (Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_mastery_api_endpoints_and_isolation(async_client: AsyncClient, db_session: AsyncSession):
    # Setup Exam & Topic
    exam = ExamTemplate(code=f"ISO_{uuid.uuid4().hex[:6]}", title="Isolation Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Circuits", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="Ohm's Law: $V = IR$. Find $V$ for $I=2\\text{ A}, R=5\\text{ }\\Omega$.",
        explanation="$V = 2 \\times 5 = 10\\text{ V}$.",
        options=[
            QuestionOptionCreate(option_key="A", content="10 V", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="2.5 V", is_correct=False, order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    await db_session.commit()

    # Register Student A
    email_a = f"stud.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Student A", "role": "student"},
    )
    login_a = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email_a, "password": "Password123!"},
    )
    token_a = login_a.json()["access_token"]

    # Register Student B
    email_b = f"stud.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Student B", "role": "student"},
    )
    login_b = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email_b, "password": "Password123!"},
    )
    token_b = login_b.json()["access_token"]

    # Student A records 2 correct attempts
    for _ in range(2):
        resp_a = await async_client.post(
            "/api/v1/mastery/record-attempt",
            json={"question_id": question.id, "selected_option_key": "A", "is_correct": True, "time_spent_seconds": 20},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert resp_a.status_code == 200

    # Check Student A topic mastery
    get_a = await async_client.get(
        f"/api/v1/mastery/topics/{topic.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_a.status_code == 200
    data_a = get_a.json()
    assert data_a["total_attempts"] == 2
    assert data_a["mastery_probability"] > 0.70
    assert data_a["status"] == "proficient"

    # Check Student B topic mastery (Constraint #2 Isolation Check: Student B should have NO attempts)
    get_b = await async_client.get(
        f"/api/v1/mastery/topics/{topic.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_b.status_code == 404  # Student B has never touched this topic

    # Check Student A exam syllabus mastery overview
    overview_a = await async_client.get(
        f"/api/v1/mastery/exams/{exam.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert overview_a.status_code == 200
    overview_data = overview_a.json()
    assert overview_data["total"] == 1
    assert overview_data["topic_masteries"][0]["topic_id"] == topic.id
