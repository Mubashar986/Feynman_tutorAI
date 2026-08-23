import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.errors.classifier import ErrorDiagnosticClassifier
from backend.app.errors.models import ErrorCategory, RepairStatus
from backend.app.errors.service import ErrorBankService
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
# 1. Error Diagnostic Classifier Unit Tests (PRD §12, FR-006, FR-012)
# ==============================================================================

def test_classifier_calculation_error():
    rationale = "Multiplied force by mass instead of dividing"
    category, code, title, desc, guidance = ErrorDiagnosticClassifier.classify_error(
        distractor_rationale=rationale,
        topic_title="Newtonian Dynamics",
    )
    assert category == ErrorCategory.CALCULATION
    assert "Multiplied" in title
    assert code.startswith("MISC_")


def test_classifier_misread_error():
    rationale = "Overlooked unit conversion from km/h to m/s"
    category, code, title, desc, guidance = ErrorDiagnosticClassifier.classify_error(
        distractor_rationale=rationale,
        topic_title="Kinematics",
    )
    assert category == ErrorCategory.MISREAD
    assert "conversion" in title or "Overlooked" in title


def test_classifier_representational_error():
    rationale = "Confused velocity-time slope with area under curve"
    category, code, title, desc, guidance = ErrorDiagnosticClassifier.classify_error(
        distractor_rationale=rationale,
        topic_title="Graphs of Motion",
    )
    assert category == ErrorCategory.REPRESENTATIONAL


def test_classifier_conceptual_fallback():
    rationale = "Believed normal force is always equal to gravitational weight"
    category, code, title, desc, guidance = ErrorDiagnosticClassifier.classify_error(
        distractor_rationale=rationale,
        topic_title="Forces in Equilibrium",
    )
    assert category == ErrorCategory.CONCEPTUAL


# ==============================================================================
# 2. Integration Tests: Automatic Mistake Logging & Remediation Lifecycle
# ==============================================================================

@pytest.mark.asyncio
async def test_automatic_error_logging_on_attempt(db_session: AsyncSession):
    # 1. Setup Exam, Subject, Topic & Question with Distractor Rationales
    exam = ExamTemplate(code=f"ERR_{uuid.uuid4().hex[:6]}", title="Error Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Circular Motion", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.MEDIUM,
        prompt="Centripetal acceleration formula for radius $r=2\\text{ m}, v=4\\text{ m/s}$.",
        explanation="$a_c = v^2 / r = 16 / 2 = 8\\text{ m/s}^2$.",
        options=[
            QuestionOptionCreate(option_key="A", content="8 m/s^2", is_correct=True, order=1),
            QuestionOptionCreate(
                option_key="B",
                content="32 m/s^2",
                is_correct=False,
                distractor_rationale="Multiplied velocity squared by radius instead of dividing",
                order=2,
            ),
            QuestionOptionCreate(
                option_key="C",
                content="2 m/s^2",
                is_correct=False,
                distractor_rationale="Used v/r instead of v^2/r",
                order=3,
            ),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    student_id = f"stud_{uuid.uuid4().hex[:8]}"

    # 2. Student answers incorrectly with Option B
    attempt_resp = await MasteryEngineService.record_attempt(
        session=db_session,
        student_id=student_id,
        attempt_in=RecordAttemptRequest(
            question_id=question.id,
            selected_option_key="B",
            is_correct=False,
            time_spent_seconds=40,
        ),
    )
    assert attempt_resp.is_correct is False

    # 3. Verify ErrorBankService automatically captured the ticket
    error_list = await ErrorBankService.list_student_errors(
        session=db_session,
        student_id=student_id,
        topic_id=topic.id,
    )
    assert error_list.total == 1
    assert error_list.active_count == 1
    assert error_list.repaired_count == 0

    err_ticket = error_list.errors[0]
    assert err_ticket.question_id == question.id
    assert err_ticket.student_answer == "B"
    assert err_ticket.error_category == ErrorCategory.CALCULATION
    assert err_ticket.distractor_rationale == "Multiplied velocity squared by radius instead of dividing"
    assert err_ticket.repair_status == RepairStatus.ACTIVE
    assert err_ticket.occurrence_count == 1
    assert err_ticket.misconception is not None

    # 4. Student repeats the exact same mistake
    await MasteryEngineService.record_attempt(
        session=db_session,
        student_id=student_id,
        attempt_in=RecordAttemptRequest(
            question_id=question.id,
            selected_option_key="B",
            is_correct=False,
            time_spent_seconds=25,
        ),
    )

    # Occurrence count should increment to 2, total active tickets remains 1
    error_list_after = await ErrorBankService.list_student_errors(session=db_session, student_id=student_id)
    assert error_list_after.total == 1
    assert error_list_after.errors[0].occurrence_count == 2

    # 5. Student marks error as repaired
    repaired_err = await ErrorBankService.resolve_error(
        session=db_session,
        student_id=student_id,
        error_log_id=err_ticket.id,
    )
    assert repaired_err.repair_status == RepairStatus.REPAIRED
    assert repaired_err.repaired_at is not None


@pytest.mark.asyncio
async def test_auto_resolve_errors_on_topic_mastery(db_session: AsyncSession):
    # Setup prerequisite Topic & Question
    exam = ExamTemplate(code=f"MST_{uuid.uuid4().hex[:6]}", title="Mastery Auto Heal")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Gravitation", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="Gravitational force question",
        explanation="Explanation",
        options=[
            QuestionOptionCreate(option_key="A", content="G M m / r^2", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="G M m / r", is_correct=False, distractor_rationale="Inverted exponent", order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    student_id = f"stud_autoheal_{uuid.uuid4().hex[:6]}"

    # Student makes error
    await MasteryEngineService.record_attempt(
        session=db_session,
        student_id=student_id,
        attempt_in=RecordAttemptRequest(question_id=question.id, selected_option_key="B", is_correct=False),
    )

    errors_before = await ErrorBankService.list_student_errors(session=db_session, student_id=student_id)
    assert errors_before.active_count == 1

    # Student answers 4 consecutive correct questions to cross MASTERED threshold (>= 0.85)
    for _ in range(4):
        await MasteryEngineService.record_attempt(
            session=db_session,
            student_id=student_id,
            attempt_in=RecordAttemptRequest(question_id=question.id, selected_option_key="A", is_correct=True),
        )

    # Active error tickets should now be auto-resolved to REPAIRED
    errors_after = await ErrorBankService.list_student_errors(session=db_session, student_id=student_id)
    assert errors_after.active_count == 0
    assert errors_after.repaired_count == 1


# ==============================================================================
# 3. REST API & Student Tenant Isolation Tests (Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_error_bank_api_endpoints_and_isolation(async_client: AsyncClient, db_session: AsyncSession):
    exam = ExamTemplate(code=f"API_ERR_{uuid.uuid4().hex[:6]}", title="API Error Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Nuclear Physics", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="Alpha decay changes atomic number by what amount?",
        explanation="Alpha decay decreases atomic number by 2.",
        options=[
            QuestionOptionCreate(option_key="A", content="-2", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="-4", is_correct=False, distractor_rationale="Confused mass number decrease with atomic number", order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    await db_session.commit()

    # Register Student A
    email_a = f"err.stud.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Student Err A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    # Register Student B
    email_b = f"err.stud.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Student Err B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # Student A submits wrong answer via mastery endpoint
    await async_client.post(
        "/api/v1/mastery/record-attempt",
        json={"question_id": question.id, "selected_option_key": "B", "is_correct": False, "time_spent_seconds": 35},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # 1. Student A checks /api/v1/error-bank
    resp_a = await async_client.get(
        "/api/v1/error-bank",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert data_a["total"] == 1
    assert data_a["active_count"] == 1
    error_id = data_a["errors"][0]["id"]

    # 2. Student B checks /api/v1/error-bank (Constraint #2 Isolation Check)
    resp_b = await async_client.get(
        "/api/v1/error-bank",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    assert resp_b.json()["total"] == 0  # Student B has zero errors

    # 3. Student A views error detail
    detail_resp = await async_client.get(
        f"/api/v1/error-bank/{error_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["question_prompt"] == question.prompt

    # 4. Student A repairs error
    repair_resp = await async_client.post(
        f"/api/v1/error-bank/{error_id}/repair",
        json={"notes": "Understood alpha decay reduces mass number by 4 and atomic number by 2"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert repair_resp.status_code == 200
    assert repair_resp.json()["repair_status"] == "repaired"

    # 5. List misconceptions for topic
    misc_resp = await async_client.get(f"/api/v1/error-bank/misconceptions/topics/{topic.id}")
    assert misc_resp.status_code == 200
    assert len(misc_resp.json()) >= 1
