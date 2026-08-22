import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.questions.models import (
    BloomTaxonomy,
    DifficultyLevel,
    QuestionType,
    ValidationStatus,
)
from backend.app.questions.schemas import (
    QuestionCreate,
    QuestionOptionCreate,
    QuestionRubricItemCreate,
    QuestionUpdate,
)
from backend.app.questions.service import QuestionBankService


# ==============================================================================
# 1. Pydantic Invariants & Validation Tests
# ==============================================================================

def test_mcq_single_validation_invariants():
    # 1. Valid MCQ with 1 correct answer
    q_valid = QuestionCreate(
        exam_template_id="et_1",
        topic_id="top_1",
        question_type=QuestionType.MCQ_SINGLE,
        prompt="What is the acceleration due to gravity on Earth?",
        explanation="Standard acceleration is approx 9.81 m/s^2",
        options=[
            QuestionOptionCreate(option_key="A", content="9.81 m/s^2", is_correct=True),
            QuestionOptionCreate(option_key="B", content="5.0 m/s^2", is_correct=False),
        ],
    )
    assert q_valid.question_type == QuestionType.MCQ_SINGLE

    # 2. Invalid MCQ with 0 correct answers -> MUST RAISE ValueError
    with pytest.raises(ValueError, match="must have exactly 1 correct option"):
        QuestionCreate(
            exam_template_id="et_1",
            topic_id="top_1",
            question_type=QuestionType.MCQ_SINGLE,
            prompt="What is the acceleration?",
            explanation="Explanation",
            options=[
                QuestionOptionCreate(option_key="A", content="9.81 m/s^2", is_correct=False),
                QuestionOptionCreate(option_key="B", content="5.0 m/s^2", is_correct=False),
            ],
        )

    # 3. Invalid MCQ with 2 correct answers -> MUST RAISE ValueError
    with pytest.raises(ValueError, match="must have exactly 1 correct option"):
        QuestionCreate(
            exam_template_id="et_1",
            topic_id="top_1",
            question_type=QuestionType.MCQ_SINGLE,
            prompt="What is the acceleration?",
            explanation="Explanation",
            options=[
                QuestionOptionCreate(option_key="A", content="9.81 m/s^2", is_correct=True),
                QuestionOptionCreate(option_key="B", content="9.8 m/s^2", is_correct=True),
            ],
        )


# ==============================================================================
# 2. QuestionBankService CRUD & Eager Loading Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_question_service_lifecycle_and_cascade(db_session: AsyncSession):
    # 1. Setup prerequisite ExamTemplate, Subject & Topic
    exam = ExamTemplate(
        code=f"PHYS_{uuid.uuid4().hex[:6]}",
        title="Physics Exam",
    )
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(
        exam_template_id=exam.id,
        title="Physics Core",
    )
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(
        subject_id=subject.id,
        title="Classical Mechanics",
        order=1,
    )
    db_session.add(topic)
    await db_session.flush()

    # 2. Create Question with Options and Rubrics
    question_in = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.HARD,
        bloom_level=BloomTaxonomy.ANALYZE,
        prompt=r"A block of mass $m=2\text{ kg}$ slides down a frictionless incline of angle $\theta=30^\circ$. Find acceleration.",
        hint=r"Use $a = g \sin\theta$",
        explanation=r"Along the incline, $F = mg\sin\theta = ma \implies a = g\sin 30^\circ = 4.9\text{ m/s}^2$.",
        points=2.0,
        options=[
            QuestionOptionCreate(option_key="A", content="4.9 m/s^2", is_correct=True, order=1),
            QuestionOptionCreate(
                option_key="B",
                content="9.8 m/s^2",
                is_correct=False,
                distractor_rationale="Forgot to multiply by sin(30 degrees)",
                order=2,
            ),
            QuestionOptionCreate(
                option_key="C",
                content="8.49 m/s^2",
                is_correct=False,
                distractor_rationale="Multiplied by cos(30 degrees) instead of sin",
                order=3,
            ),
        ],
        rubric_items=[
            QuestionRubricItemCreate(criterion="Resolves force component along incline", points=1.0, order=1),
            QuestionRubricItemCreate(criterion="Calculates numerical acceleration correctly", points=1.0, order=2),
        ],
    )

    created_q = await QuestionBankService.create_question(db_session, question_in)
    assert created_q.id is not None
    assert len(created_q.options) == 3
    assert len(created_q.rubric_items) == 2

    # 3. Retrieve by ID (Eager Loading Check)
    fetched_q = await QuestionBankService.get_question(db_session, created_q.id)
    assert fetched_q is not None
    assert fetched_q.difficulty == DifficultyLevel.HARD
    assert fetched_q.options[1].distractor_rationale == "Forgot to multiply by sin(30 degrees)"
    assert fetched_q.rubric_items[0].criterion == "Resolves force component along incline"

    # 4. List with filters
    items, total = await QuestionBankService.list_questions(
        session=db_session,
        topic_id=topic.id,
        difficulty=DifficultyLevel.HARD,
    )
    assert total >= 1
    assert any(q.id == created_q.id for q in items)

    # 5. Update validation status
    updated_q = await QuestionBankService.update_question(
        session=db_session,
        question_id=created_q.id,
        update_in=QuestionUpdate(validation_status=ValidationStatus.VALIDATED),
    )
    assert updated_q.validation_status == ValidationStatus.VALIDATED

    # 6. Delete and verify cascade
    deleted = await QuestionBankService.delete_question(db_session, created_q.id)
    assert deleted is True

    # Verify not found
    after_del = await QuestionBankService.get_question(db_session, created_q.id)
    assert after_del is None


# ==============================================================================
# 3. REST API Endpoint & RBAC Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_question_api_rbac_and_crud(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Setup Exam, Subject & Topic
    exam = ExamTemplate(
        code=f"MATH_{uuid.uuid4().hex[:6]}",
        title="Calculus Exam",
    )
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(
        exam_template_id=exam.id,
        title="Calculus Core",
    )
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(
        subject_id=subject.id,
        title="Derivatives",
        order=1,
    )


    db_session.add(topic)
    await db_session.flush()

    # 2. Register Instructor & Student
    inst_email = f"q.inst.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": inst_email, "password": "Password123!", "full_name": "Instructor Q", "role": "instructor"},
    )
    login_inst = await async_client.post(
        "/api/v1/auth/login",
        json={"email": inst_email, "password": "Password123!"},
    )
    inst_token = login_inst.json()["access_token"]

    student_email = f"q.stud.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": student_email, "password": "Password123!", "full_name": "Student Q", "role": "student"},
    )
    login_stud = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_email, "password": "Password123!"},
    )
    student_token = login_stud.json()["access_token"]

    # 3. Student tries to CREATE question -> 403 Forbidden
    payload = {
        "exam_template_id": exam.id,
        "topic_id": topic.id,
        "question_type": "mcq_single",
        "prompt": "Find d/dx of sin(x)",
        "explanation": "d/dx sin(x) = cos(x)",
        "options": [
            {"option_key": "A", "content": "cos(x)", "is_correct": True},
            {"option_key": "B", "content": "-cos(x)", "is_correct": False},
        ],
    }
    resp_student_create = await async_client.post(
        "/api/v1/questions",
        json=payload,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp_student_create.status_code == 403

    # 4. Instructor CREATES question -> 201 Created
    resp_inst_create = await async_client.post(
        "/api/v1/questions",
        json=payload,
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_inst_create.status_code == 201
    q_data = resp_inst_create.json()
    q_id = q_data["id"]
    assert q_data["prompt"] == "Find d/dx of sin(x)"
    assert len(q_data["options"]) == 2

    # 5. Public / Student reads question by ID -> 200 OK
    resp_get = await async_client.get(f"/api/v1/questions/{q_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == q_id

    # 6. Instructor UPDATES question -> 200 OK
    resp_update = await async_client.put(
        f"/api/v1/questions/{q_id}",
        json={"validation_status": "validated", "points": 5.0},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["validation_status"] == "validated"
    assert resp_update.json()["points"] == 5.0

    # 7. Instructor DELETES question -> 204 No Content
    resp_del = await async_client.delete(
        f"/api/v1/questions/{q_id}",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_del.status_code == 204
