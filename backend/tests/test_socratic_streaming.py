import json
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.rag.models import Document, DocumentChunk, DocumentStatus, DocumentType
from backend.app.tutor.models import HintLevel, TutorRole
from backend.app.tutor.schemas import (
    SocraticPromptRequest,
    TutorSessionCreate,
)
from backend.app.tutor.service import SocraticTutorService


# ==============================================================================
# 1. Async Generator & SSE Wire Frame Unit Tests (PRD §14, §17, FR-008)
# ==============================================================================

@pytest.mark.asyncio
async def test_socratic_streaming_generator_events(db_session: AsyncSession):
    # Setup Exam, Topic, and Document Chunk
    exam = ExamTemplate(code=f"STR_{uuid.uuid4().hex[:6]}", title="Streaming Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Quantum Physics", order=1)
    db_session.add(topic)
    await db_session.flush()

    doc = Document(
        title="Modern Physics 101",
        original_filename="quantum.txt",
        file_type=DocumentType.TEXT,
        file_size_bytes=512,
        sha256_hash=uuid.uuid4().hex,
        storage_path="/tmp/fake_quantum",
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
        content="Photoelectric effect equation: $E_{max} = hf - \\Phi$, where $\\Phi$ is the work function.",
        clean_content="Photoelectric effect equation: $E_{max} = hf - \\Phi$, where $\\Phi$ is the work function.",
        token_count=20,
    )
    db_session.add(chunk)
    await db_session.flush()

    student_id = f"stud_stream_{uuid.uuid4().hex[:8]}"

    # Create Tutor Session
    sess = await SocraticTutorService.create_session(
        session=db_session,
        student_id=student_id,
        session_in=TutorSessionCreate(
            exam_template_id=exam.id,
            topic_id=topic.id,
            title="Photoelectric Review",
        ),
    )

    # Stream tokens using mock_chunks
    mock_tokens = ["Recall", " Einstein's", " formula: ", "$E = hf - \\Phi$.", " What is $\\Phi$?"]
    collected_frames = []

    stream_gen = SocraticTutorService.stream_socratic_message(
        session=db_session,
        student_id=student_id,
        session_id=sess.id,
        message_in=SocraticPromptRequest(message="What is work function?", hint_level=HintLevel.CONCEPTUAL),
        mock_chunks=mock_tokens,
    )

    async for frame in stream_gen:
        collected_frames.append(frame)

    # 1. Verify Event Sequence
    assert len(collected_frames) == 1 + len(mock_tokens) + 1  # 1 citations + 5 deltas + 1 done

    # Event 1: Citations
    assert collected_frames[0].startswith("event: citations\ndata: ")

    # Events 2-6: Delta tokens
    for i, token in enumerate(mock_tokens):
        frame = collected_frames[1 + i]
        assert frame.startswith("event: delta\ndata: ")
        data = json.loads(frame.replace("event: delta\ndata: ", "").strip())
        assert data["text"] == token

    # Event 7: Done event
    assert collected_frames[-1].startswith("event: done\ndata: ")
    done_data = json.loads(collected_frames[-1].replace("event: done\ndata: ", "").strip())
    assert "message_id" in done_data
    assert done_data["session_id"] == sess.id

    # 2. Verify Database Persistence of turn
    history = await SocraticTutorService.get_session_history(db_session, student_id, sess.id)
    assert history is not None
    assert len(history.messages) == 2  # 1 user + 1 assistant
    assert history.messages[0].role == TutorRole.USER
    assert history.messages[1].role == TutorRole.ASSISTANT
    assert "$E = hf - \\Phi$" in history.messages[1].content


# ==============================================================================
# 2. REST API Streaming Endpoint Tests (Constraint #2, #5, #8)
# ==============================================================================

@pytest.mark.asyncio
async def test_socratic_streaming_api_endpoint(async_client: AsyncClient, db_session: AsyncSession):
    exam = ExamTemplate(code=f"API_STR_{uuid.uuid4().hex[:6]}", title="API Stream Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Optics", order=1)
    db_session.add(topic)
    await db_session.flush()
    await db_session.commit()

    # Register Student A
    email_a = f"stream.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Stream Student A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    # Register Student B
    email_b = f"stream.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Stream Student B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # Student A creates a session
    create_resp = await async_client.post(
        "/api/v1/tutor/sessions",
        json={"exam_template_id": exam.id, "topic_id": topic.id, "title": "Snell's Law Stream"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    # Student A connects to the SSE streaming endpoint
    stream_resp = await async_client.post(
        f"/api/v1/tutor/sessions/{session_id}/stream",
        json={"message": "What is Snell's law formula?", "hint_level": "conceptual"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    assert stream_resp.headers["cache-control"] == "no-cache"

    body_text = stream_resp.text
    assert "event: citations" in body_text
    assert "event: done" in body_text

    # Student B attempts to stream to Student A's session (Constraint #2 Isolation Check)
    snoop_resp = await async_client.post(
        f"/api/v1/tutor/sessions/{session_id}/stream",
        json={"message": "Snoop attempt", "hint_level": "conceptual"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert snoop_resp.status_code == 200
    assert "event: error" in snoop_resp.text
