from datetime import datetime, timedelta, timezone
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.errors.service import ErrorBankService
from backend.app.questions.schemas import QuestionCreate, QuestionOptionCreate
from backend.app.questions.service import QuestionBankService
from backend.app.revision.models import CardState, ReviewRating
from backend.app.revision.schemas import (
    CardSeedRequest,
    ReviewSubmitRequest,
)
from backend.app.revision.service import SpacedRepetitionService
from backend.app.revision.sm2 import SM2Engine


# ==============================================================================
# 1. SM-2 & Retrievability Mathematical Unit Tests (PRD FR-007, Cap 7)
# ==============================================================================

def test_sm2_initial_learning_progression():
    """
    Verifies that fresh cards progress sequentially from 1d -> 6d -> (6 * EF)d.
    """
    # 1. First review with GOOD (q=3)
    rep, interval, ef, state, stab = SM2Engine.calculate_next_interval(
        repetitions=0,
        interval_days=0.0,
        ease_factor=2.50,
        rating=ReviewRating.GOOD,
    )
    assert rep == 1
    assert interval == 1.0
    assert ef == 2.50
    assert state == CardState.LEARNING

    # 2. Second review with GOOD (q=3)
    rep, interval, ef, state, stab = SM2Engine.calculate_next_interval(
        repetitions=1,
        interval_days=1.0,
        ease_factor=2.50,
        rating=ReviewRating.GOOD,
    )
    assert rep == 2
    assert interval == 6.0
    assert ef == 2.50
    assert state == CardState.REVIEW

    # 3. Third review with GOOD (q=3)
    rep, interval, ef, state, stab = SM2Engine.calculate_next_interval(
        repetitions=2,
        interval_days=6.0,
        ease_factor=2.50,
        rating=ReviewRating.GOOD,
    )
    assert rep == 3
    assert interval == 15.0  # 6 * 2.5 = 15.0
    assert ef == 2.50
    assert state == CardState.REVIEW


def test_sm2_ease_factor_bounds_and_lapse():
    """
    Verifies ease factor clamping [1.30, 2.80] and relapse handling on AGAIN.
    """
    # Repeated AGAIN failures should never drop EF below 1.30
    ef = 1.40
    rep, interval, new_ef, state, stab = SM2Engine.calculate_next_interval(
        repetitions=5,
        interval_days=30.0,
        ease_factor=ef,
        rating=ReviewRating.AGAIN,
    )
    assert rep == 0
    assert interval == 1.0
    assert new_ef == 1.30  # Clamped to min 1.30
    assert state == CardState.RELEARNING

    # Repeated EASY reviews should never exceed 2.80
    ef = 2.75
    rep, interval, new_ef, state, stab = SM2Engine.calculate_next_interval(
        repetitions=2,
        interval_days=6.0,
        ease_factor=ef,
        rating=ReviewRating.EASY,
    )
    assert new_ef == 2.80  # Clamped to max 2.80


def test_ebbinghaus_retrievability_decay():
    """
    Verifies exponential forgetting formula R(t) = exp(-t / S).
    """
    # At t = 0, R(0) = 1.0
    assert SM2Engine.calculate_retrievability(0.0, 10.0) == 1.0

    # At t = S, R(S) = exp(-1) = 0.3679
    r = SM2Engine.calculate_retrievability(10.0, 10.0)
    assert round(r, 2) == 0.37

    # At t = 2S, R(2S) = exp(-2) = 0.1353
    r2 = SM2Engine.calculate_retrievability(20.0, 10.0)
    assert round(r2, 2) == 0.14


# ==============================================================================
# 2. Service & Priority Queue Integration Tests (Constraints #2, #5, #8)
# ==============================================================================

@pytest.mark.asyncio
async def test_spaced_repetition_service_lifecycle_and_error_boost(db_session: AsyncSession):
    # 1. Setup Syllabus & Questions
    exam = ExamTemplate(code=f"REV_{uuid.uuid4().hex[:6]}", title="Revision Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Thermodynamics", order=1)
    db_session.add(topic)
    await db_session.flush()

    # Question 1: Standard Question
    q1_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="State First Law of Thermodynamics.",
        explanation="$\\Delta U = Q - W$.",
        options=[
            QuestionOptionCreate(option_key="A", content="Delta U = Q - W", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="Delta U = Q + W", is_correct=False, order=2),
        ],
    )
    q1 = await QuestionBankService.create_question(db_session, q1_create)

    # Question 2: Question with Active Error
    q2_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="What is an adiabatic process?",
        explanation="No heat transfer: $Q = 0$.",
        options=[
            QuestionOptionCreate(option_key="A", content="Q = 0", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="W = 0", is_correct=False, distractor_rationale="Confused adiabatic with isochoric", order=2),
        ],
    )
    q2 = await QuestionBankService.create_question(db_session, q2_create)

    student_id = f"stud_rev_{uuid.uuid4().hex[:8]}"

    # Log active error for Question 2
    await ErrorBankService.log_error(
        session=db_session,
        student_id=student_id,
        question=q2,
        selected_option_key="B",
    )

    # 2. Initialize / Seed Cards
    card1 = await SpacedRepetitionService.get_or_create_card(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_id=q1.id,
    )
    card2 = await SpacedRepetitionService.get_or_create_card(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_id=q2.id,
    )

    # 3. Query Due Cards (Both are due now)
    due_resp = await SpacedRepetitionService.get_due_cards(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam.id,
    )
    assert due_resp.total_due == 2
    # Verify Error Bank Priority Booster: Card 2 (with active error) MUST be ranked FIRST
    assert due_resp.due_cards[0].question_id == q2.id
    assert due_resp.due_cards[0].has_active_error is True
    assert due_resp.due_cards[1].question_id == q1.id
    assert due_resp.due_cards[1].has_active_error is False

    # 4. Submit Review for Card 1 (GOOD)
    rev_resp = await SpacedRepetitionService.submit_review(
        session=db_session,
        student_id=student_id,
        review_in=ReviewSubmitRequest(card_id=card1.id, rating=ReviewRating.GOOD),
    )
    assert rev_resp.new_interval_days == 1.0
    assert rev_resp.card_state == CardState.LEARNING

    # 5. Verify Metrics
    metrics = await SpacedRepetitionService.get_revision_metrics(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam.id,
    )
    assert metrics.total_cards == 2
    assert metrics.learning_cards == 1
    assert metrics.new_cards == 1
    assert metrics.average_retention_rate == 1.0


# ==============================================================================
# 3. REST API Endpoints & Tenant Isolation Tests (Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_spaced_repetition_api_endpoints_and_isolation(async_client: AsyncClient, db_session: AsyncSession):
    exam = ExamTemplate(code=f"API_REV_{uuid.uuid4().hex[:6]}", title="API Revision Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Chemistry")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Equilibrium", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="What is Le Chatelier's principle?",
        explanation="System shifts to counteract disturbance.",
        options=[
            QuestionOptionCreate(option_key="A", content="Shifts to counteract", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="No change", is_correct=False, order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    await db_session.commit()

    # Register Student A
    email_a = f"rev.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Rev Student A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    # Register Student B
    email_b = f"rev.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Rev Student B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # Student A seeds flashcards
    seed_resp = await async_client.post(
        "/api/v1/revision/cards/seed",
        json={"exam_template_id": exam.id, "topic_id": topic.id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert seed_resp.status_code == 201
    assert seed_resp.json()["seeded_count"] == 1

    # Student A fetches due cards
    due_resp = await async_client.get(
        "/api/v1/revision/due",
        params={"exam_template_id": exam.id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert due_resp.status_code == 200
    cards = due_resp.json()["due_cards"]
    assert len(cards) == 1
    card_a_id = cards[0]["id"]

    # Student A reviews card with EASY
    review_resp = await async_client.post(
        "/api/v1/revision/review",
        json={"card_id": card_a_id, "rating": 4},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["new_interval_days"] == 3.0  # EASY initial bonus

    # Student B attempts to review Student A's card (Constraint #2 Isolation Check)
    snoop_resp = await async_client.post(
        "/api/v1/revision/review",
        json={"card_id": card_a_id, "rating": 3},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert snoop_resp.status_code == 404
