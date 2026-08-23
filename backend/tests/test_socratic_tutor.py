import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.errors.models import ErrorCategory
from backend.app.errors.service import ErrorBankService
from backend.app.mastery.models import MasteryStatus, StudentTopicMastery
from backend.app.questions.models import (
    DifficultyLevel,
    QuestionType,
)
from backend.app.questions.schemas import (
    QuestionCreate,
    QuestionOptionCreate,
)
from backend.app.questions.service import QuestionBankService
from backend.app.rag.models import Document, DocumentChunk, DocumentStatus, DocumentType
from backend.app.tutor.models import HintLevel, TutorRole
from backend.app.tutor.schemas import (
    SocraticPromptRequest,
    TutorSessionCreate,
)
from backend.app.tutor.service import SocraticTutorService


# ==============================================================================
# 1. Prompt Engineering & Scaffolding Unit Tests (PRD §14.3, §14.5, FR-008)
# ==============================================================================

def test_socratic_hint_instructions_formatting():
    """Verifies that all 4 scaffolding hint tiers produce correct pedagogical instructions."""
    name1, tier1, inst1 = SocraticTutorService._format_hint_instructions(HintLevel.CONCEPTUAL)
    assert tier1 == 1
    assert "CONCEPTUAL" in name1
    assert "fundamental" in inst1

    name2, tier2, inst2 = SocraticTutorService._format_hint_instructions(HintLevel.STRATEGIC)
    assert tier2 == 2
    assert "direction" in inst2 or "strategy" in inst2

    name3, tier3, inst3 = SocraticTutorService._format_hint_instructions(HintLevel.STEP)
    assert tier3 == 3
    assert "algebraic" in inst3

    name4, tier4, inst4 = SocraticTutorService._format_hint_instructions(HintLevel.EXPLANATION)
    assert tier4 == 4
    assert "derivation" in inst4


def test_socratic_prompt_invariants():
    """Verifies that the Socratic system prompt strictly contains non-leakage and KaTeX rules."""
    prompt = SocraticTutorService.SYSTEM_PROMPT_TEMPLATE.format(
        hint_level_name="CONCEPTUAL HINT",
        hint_tier=1,
        hint_level_instruction="Guide conceptually.",
        mastery_probability=0.45,
        mastery_status="practicing",
        misconception_guidance="No misconceptions.",
        grounded_sources="Chunk: F = ma",
        question_context="",
    )
    assert "NEVER REVEAL THE FINAL ANSWER" in prompt
    assert "KaTeX" in prompt
    assert "45.0%" in prompt
    assert "Chunk: F = ma" in prompt


# ==============================================================================
# 2. Integration Tests: Multi-Turn Socratic Dialogue & State Injection
# ==============================================================================

@pytest.mark.asyncio
async def test_socratic_session_and_message_lifecycle(db_session: AsyncSession):
    # 1. Setup Exam, Subject, Topic, Question, and Grounded Chunk
    exam = ExamTemplate(code=f"TUT_{uuid.uuid4().hex[:6]}", title="Tutor Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Work and Energy", order=1)
    db_session.add(topic)
    await db_session.flush()

    doc = Document(
        title="Physics Mechanics Chapter 5",
        original_filename="mechanics_ch5.txt",
        file_type=DocumentType.TEXT,
        file_size_bytes=1024,
        sha256_hash=uuid.uuid4().hex,
        storage_path="/tmp/fake_storage",
        status=DocumentStatus.INDEXED,
        exam_template_id=exam.id,
        topic_id=topic.id,
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        topic_id=topic.id,
        chunk_index=0,
        content="Work-Energy Theorem: The net work done on an object equals the change in kinetic energy: $W_{net} = \\Delta E_k$.",
        clean_content="Work-Energy Theorem: The net work done on an object equals the change in kinetic energy: $W_{net} = \\Delta E_k$.",
        token_count=25,
    )
    db_session.add(chunk)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="A block of mass $m=2\\text{ kg}$ is pushed with $F=10\\text{ N}$ across $d=5\\text{ m}$. Find work done.",
        explanation="$W = Fd = 10 \\times 5 = 50\\text{ J}$.",
        options=[
            QuestionOptionCreate(option_key="A", content="50 J", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="25 J", is_correct=False, distractor_rationale="Divided force by distance", order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    student_id = f"stud_tutor_{uuid.uuid4().hex[:8]}"

    # Setup Mastery State ($P = 0.40$)
    mastery = StudentTopicMastery(
        student_id=student_id,
        exam_template_id=exam.id,
        topic_id=topic.id,
        mastery_probability=0.40,
        status=MasteryStatus.PRACTICING,
        current_difficulty=DifficultyLevel.MEDIUM,
    )
    db_session.add(mastery)
    await db_session.flush()

    # Log active error misconception
    await ErrorBankService.log_error(
        session=db_session,
        student_id=student_id,
        question=question,
        selected_option_key="B",
    )

    # 2. Create Tutor Session
    session_create = TutorSessionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_id=question.id,
        title="Energy Work Review",
    )
    tutor_sess = await SocraticTutorService.create_session(db_session, student_id, session_create)
    assert tutor_sess.id is not None
    assert tutor_sess.title == "Energy Work Review"

    # 3. Send First Socratic Message Turn
    mock_reply = "Recall the Work-Energy definition: how is work $W$ calculated from force $F$ and displacement $d$?"
    resp1 = await SocraticTutorService.send_message(
        session=db_session,
        student_id=student_id,
        session_id=tutor_sess.id,
        message_in=SocraticPromptRequest(message="I don't know how to start.", hint_level=HintLevel.CONCEPTUAL),
        mock_llm_response=mock_reply,
    )

    assert resp1.session_id == tutor_sess.id
    assert resp1.message.role == TutorRole.ASSISTANT
    assert "Work-Energy definition" in resp1.message.content
    assert resp1.message.hint_level == HintLevel.CONCEPTUAL

    # 4. Send Second Message Turn (Multi-Turn Dialogue)
    mock_reply_2 = "Exactly! $W = F \\cdot d$. What are the values of $F$ and $d$ given in the problem statement?"
    resp2 = await SocraticTutorService.send_message(
        session=db_session,
        student_id=student_id,
        session_id=tutor_sess.id,
        message_in=SocraticPromptRequest(message="Is it force times distance?", hint_level=HintLevel.STRATEGIC),
        mock_llm_response=mock_reply_2,
    )
    assert resp2.message.hint_level == HintLevel.STRATEGIC

    # 5. Verify Full Turn History
    history = await SocraticTutorService.get_session_history(db_session, student_id, tutor_sess.id)
    assert history is not None
    assert len(history.messages) == 4  # 2 user messages + 2 assistant messages
    assert history.messages[0].role == TutorRole.USER
    assert history.messages[1].role == TutorRole.ASSISTANT
    assert history.messages[2].role == TutorRole.USER
    assert history.messages[3].role == TutorRole.ASSISTANT


# ==============================================================================
# 3. REST API & Multi-Student Tenant Isolation Tests (Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_socratic_api_endpoints_and_isolation(async_client: AsyncClient, db_session: AsyncSession):
    exam = ExamTemplate(code=f"API_TUT_{uuid.uuid4().hex[:6]}", title="API Tutor Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Thermodynamics", order=1)
    db_session.add(topic)
    await db_session.flush()
    await db_session.commit()

    # Register Student A
    email_a = f"tut.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Tutor Student A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    # Register Student B
    email_b = f"tut.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Tutor Student B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # Student A creates a session
    create_resp = await async_client.post(
        "/api/v1/tutor/sessions",
        json={"exam_template_id": exam.id, "topic_id": topic.id, "title": "First Law Tutorial"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    # Student A sends a message
    msg_resp = await async_client.post(
        f"/api/v1/tutor/sessions/{session_id}/message",
        json={"message": "What is the formula for the first law of thermodynamics?", "hint_level": "conceptual"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert msg_resp.status_code == 200
    assert msg_resp.json()["session_id"] == session_id
    assert "message" in msg_resp.json()

    # Student A lists sessions
    list_resp = await async_client.get(
        "/api/v1/tutor/sessions",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Student B attempts to access Student A's session (Constraint #2 Isolation Check)
    snoop_resp = await async_client.get(
        f"/api/v1/tutor/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert snoop_resp.status_code == 404  # Student B cannot see Student A's conversation

    # Student B lists sessions
    list_b = await async_client.get(
        "/api/v1/tutor/sessions",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0  # Student B has 0 sessions
