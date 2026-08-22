import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.learning_state.models import LearningState, StudentLearningState
from backend.app.learning_state.service import (
    LearningStateMachineService,
    InvalidStateTransitionException,
    VALID_TRANSITIONS,
)


# ==============================================================================
# 1. State Machine Unit Tests & Guard Predicates
# ==============================================================================

def test_valid_transitions_coverage():
    """Verify that all 9 states are covered in the FSM transition table."""
    assert len(VALID_TRANSITIONS) == 9
    assert LearningState.NOT_STARTED in VALID_TRANSITIONS
    assert LearningState.CALIBRATION in VALID_TRANSITIONS
    assert LearningState.FOUNDATION in VALID_TRANSITIONS
    assert LearningState.PRACTICING in VALID_TRANSITIONS
    assert LearningState.ASSESSMENT in VALID_TRANSITIONS
    assert LearningState.DIAGNOSIS in VALID_TRANSITIONS
    assert LearningState.REPAIR in VALID_TRANSITIONS
    assert LearningState.MASTERY in VALID_TRANSITIONS
    assert LearningState.REVISION in VALID_TRANSITIONS


def test_validate_transition_legal_paths():
    """Verify that legal transitions pass validation without exception."""
    # NOT_STARTED transitions
    LearningStateMachineService.validate_transition(LearningState.NOT_STARTED, LearningState.CALIBRATION)
    LearningStateMachineService.validate_transition(LearningState.NOT_STARTED, LearningState.FOUNDATION)

    # CALIBRATION transitions
    LearningStateMachineService.validate_transition(LearningState.CALIBRATION, LearningState.FOUNDATION)
    LearningStateMachineService.validate_transition(LearningState.CALIBRATION, LearningState.PRACTICING)
    LearningStateMachineService.validate_transition(LearningState.CALIBRATION, LearningState.DIAGNOSIS)

    # FOUNDATION transitions
    LearningStateMachineService.validate_transition(LearningState.FOUNDATION, LearningState.PRACTICING)
    LearningStateMachineService.validate_transition(LearningState.FOUNDATION, LearningState.ASSESSMENT)

    # PRACTICING transitions
    LearningStateMachineService.validate_transition(LearningState.PRACTICING, LearningState.ASSESSMENT)
    LearningStateMachineService.validate_transition(LearningState.PRACTICING, LearningState.DIAGNOSIS)
    LearningStateMachineService.validate_transition(LearningState.PRACTICING, LearningState.REPAIR)

    # ASSESSMENT transitions
    LearningStateMachineService.validate_transition(
        LearningState.ASSESSMENT,
        LearningState.MASTERY,
        evidence_payload={"score": 0.90, "passing_threshold": 0.80},
    )
    LearningStateMachineService.validate_transition(LearningState.ASSESSMENT, LearningState.DIAGNOSIS)
    LearningStateMachineService.validate_transition(LearningState.ASSESSMENT, LearningState.REPAIR)

    # DIAGNOSIS transitions
    LearningStateMachineService.validate_transition(LearningState.DIAGNOSIS, LearningState.REPAIR)
    LearningStateMachineService.validate_transition(LearningState.DIAGNOSIS, LearningState.FOUNDATION)

    # REPAIR transitions
    LearningStateMachineService.validate_transition(LearningState.REPAIR, LearningState.PRACTICING)
    LearningStateMachineService.validate_transition(LearningState.REPAIR, LearningState.ASSESSMENT)

    # MASTERY transitions
    LearningStateMachineService.validate_transition(LearningState.MASTERY, LearningState.REVISION)
    LearningStateMachineService.validate_transition(LearningState.MASTERY, LearningState.DIAGNOSIS)

    # REVISION transitions
    LearningStateMachineService.validate_transition(LearningState.REVISION, LearningState.MASTERY)
    LearningStateMachineService.validate_transition(LearningState.REVISION, LearningState.DIAGNOSIS)
    LearningStateMachineService.validate_transition(LearningState.REVISION, LearningState.REPAIR)


def test_validate_transition_illegal_paths_rejected():
    """Verify that forbidden transitions throw InvalidStateTransitionException."""
    # Direct jump to Mastery without assessment
    with pytest.raises(InvalidStateTransitionException) as exc_info:
        LearningStateMachineService.validate_transition(LearningState.NOT_STARTED, LearningState.MASTERY)
    assert "Illegal transition" in exc_info.value.detail

    with pytest.raises(InvalidStateTransitionException):
        LearningStateMachineService.validate_transition(LearningState.FOUNDATION, LearningState.MASTERY)

    with pytest.raises(InvalidStateTransitionException):
        LearningStateMachineService.validate_transition(LearningState.DIAGNOSIS, LearningState.MASTERY)

    with pytest.raises(InvalidStateTransitionException):
        LearningStateMachineService.validate_transition(LearningState.CALIBRATION, LearningState.MASTERY)


def test_assessment_to_mastery_guard_rejects_failing_score():
    """Verify guard predicate blocks promotion to MASTERY if assessment score < threshold."""
    failing_evidence = {"score": 0.65, "passing_threshold": 0.80}
    with pytest.raises(InvalidStateTransitionException) as exc_info:
        LearningStateMachineService.validate_transition(
            LearningState.ASSESSMENT,
            LearningState.MASTERY,
            evidence_payload=failing_evidence,
        )
    assert "does not satisfy required mastery threshold" in exc_info.value.detail


# ==============================================================================
# 2. Database Service & Transactional Unit Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_service_get_or_create_state(db_session: AsyncSession):
    student_id = str(uuid.uuid4())
    exam_id = str(uuid.uuid4())
    topic_id = str(uuid.uuid4())

    # First call creates record
    state = await LearningStateMachineService.get_or_create_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam_id,
        topic_id=topic_id,
    )
    assert state.current_state == LearningState.NOT_STARTED
    assert state.mastery_score == 0.0

    # Second call returns existing record
    state2 = await LearningStateMachineService.get_or_create_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam_id,
        topic_id=topic_id,
    )
    assert state2.id == state.id


@pytest.mark.asyncio
async def test_service_transition_lifecycle_and_audit_log(db_session: AsyncSession):
    student_id = str(uuid.uuid4())
    exam_id = str(uuid.uuid4())
    topic_id = str(uuid.uuid4())
    actor_id = student_id

    # 1. NOT_STARTED -> FOUNDATION
    state, log1 = await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam_id,
        topic_id=topic_id,
        target_state=LearningState.FOUNDATION,
        trigger="STUDY_SESSION_STARTED",
        evidence_payload={"source": "textbook_chapter_1"},
        actor_id=actor_id,
    )
    assert state.current_state == LearningState.FOUNDATION
    assert log1.from_state == LearningState.NOT_STARTED
    assert log1.to_state == LearningState.FOUNDATION
    assert log1.trigger == "STUDY_SESSION_STARTED"

    # 2. FOUNDATION -> PRACTICING
    state, log2 = await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam_id,
        topic_id=topic_id,
        target_state=LearningState.PRACTICING,
        trigger="READING_COMPLETE",
        evidence_payload={"duration_mins": 30},
        actor_id=actor_id,
    )
    assert state.current_state == LearningState.PRACTICING
    assert log2.from_state == LearningState.FOUNDATION
    assert log2.to_state == LearningState.PRACTICING

    # 3. PRACTICING -> ASSESSMENT
    state, log3 = await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam_id,
        topic_id=topic_id,
        target_state=LearningState.ASSESSMENT,
        trigger="PRACTICE_DRILL_PASSED",
        evidence_payload={"questions_answered": 10},
        actor_id=actor_id,
    )
    assert state.current_state == LearningState.ASSESSMENT

    # 4. ASSESSMENT -> MASTERY
    state, log4 = await LearningStateMachineService.transition_state(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam_id,
        topic_id=topic_id,
        target_state=LearningState.MASTERY,
        trigger="EXAM_ASSESSMENT_PASSED",
        evidence_payload={"score": 0.95, "passing_threshold": 0.80},
        actor_id=actor_id,
        mastery_score=0.95,
    )
    assert state.current_state == LearningState.MASTERY
    assert state.mastery_score == 0.95
    assert state.consecutive_successes == 1

    # Verify audit log history
    history = await LearningStateMachineService.get_topic_history(
        session=db_session,
        student_id=student_id,
        exam_template_id=exam_id,
        topic_id=topic_id,
    )
    assert len(history) == 4
    # Most recent first
    assert history[0].to_state == LearningState.MASTERY
    assert history[3].to_state == LearningState.FOUNDATION


# ==============================================================================
# 3. FastAPI Endpoint Integration & Tenant Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_endpoint_transition_success(async_client: AsyncClient):
    # Register & Login Student
    email = "state.student@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "State Student", "role": "student"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exam_id = str(uuid.uuid4())
    topic_id = str(uuid.uuid4())

    # Perform valid transition: NOT_STARTED -> CALIBRATION
    payload = {
        "exam_template_id": exam_id,
        "topic_id": topic_id,
        "target_state": "calibration",
        "trigger": "INITIAL_DIAGNOSTIC_START",
        "evidence_payload": {"test_type": "baseline"},
    }
    resp = await async_client.post(
        "/api/v1/learning-state/transition",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_state"] == "calibration"
    assert data["exam_template_id"] == exam_id
    assert data["topic_id"] == topic_id

    # Fetch topic state via GET
    get_resp = await async_client.get(
        f"/api/v1/learning-state/topic/{topic_id}?exam_template_id={exam_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["current_state"] == "calibration"

    # Fetch topic history via GET
    hist_resp = await async_client.get(
        f"/api/v1/learning-state/topic/{topic_id}/history?exam_template_id={exam_id}",
        headers=headers,
    )
    assert hist_resp.status_code == 200
    logs = hist_resp.json()
    assert len(logs) == 1
    assert logs[0]["from_state"] == "not_started"
    assert logs[0]["to_state"] == "calibration"


@pytest.mark.asyncio
async def test_endpoint_illegal_transition_returns_400(async_client: AsyncClient):
    # Register & Login Student
    email = "illegal.student@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Illegal Student", "role": "student"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exam_id = str(uuid.uuid4())
    topic_id = str(uuid.uuid4())

    # Attempt illegal jump: NOT_STARTED -> MASTERY
    payload = {
        "exam_template_id": exam_id,
        "topic_id": topic_id,
        "target_state": "mastery",
        "trigger": "UNAUTHORIZED_PROMOTION",
        "evidence_payload": {},
    }
    resp = await async_client.post(
        "/api/v1/learning-state/transition",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 400
    assert "Illegal transition" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_tenant_isolation_cross_student_access_forbidden(async_client: AsyncClient):
    """
    Guarantees that Student A cannot query or mutate Student B's learning state (PRD Constraint #2).
    """
    # Student A
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "student.a@example.com", "password": "Password123!", "full_name": "Student A", "role": "student"},
    )
    login_a = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "student.a@example.com", "password": "Password123!"},
    )
    token_a = login_a.json()["access_token"]
    student_a_id = login_a.json()["user"]["id"]

    # Student B
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "student.b@example.com", "password": "Password123!", "full_name": "Student B", "role": "student"},
    )
    login_b = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "student.b@example.com", "password": "Password123!"},
    )
    token_b = login_b.json()["access_token"]

    exam_id = str(uuid.uuid4())
    topic_id = str(uuid.uuid4())

    # Student B attempts to fetch Student A's state -> MUST BE 403 FORBIDDEN
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp = await async_client.get(
        f"/api/v1/learning-state/topic/{topic_id}?exam_template_id={exam_id}&student_id={student_a_id}",
        headers=headers_b,
    )
    assert resp.status_code == 403
    assert "Students can only access their own learning state" in resp.json()["detail"]
