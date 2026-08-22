import io
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import UploadFile

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.questions.generator import QuestionGeneratorService
from backend.app.questions.models import (
    BloomTaxonomy,
    DifficultyLevel,
    QuestionType,
    ValidationStatus,
)
from backend.app.questions.schemas import (
    GeneratedOptionSchema,
    GeneratedQuestionBatchSchema,
    GeneratedQuestionSchema,
    GeneratedRubricSchema,
    QuestionGenerateRequest,
)
from backend.app.rag.indexer import VectorIndexerService
from backend.app.rag.service import DocumentService


# ==============================================================================
# 1. Prompt Construction Unit Tests (Constraint #5, Bloom Taxonomy)
# ==============================================================================

def test_build_generation_prompts():
    request = QuestionGenerateRequest(
        exam_template_id="et_physics",
        topic_id="top_circular_motion",
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.HARD,
        bloom_level=BloomTaxonomy.ANALYZE,
        count=2,
        custom_prompt_guidance="Focus on centripetal acceleration on banked tracks.",
    )
    grounded_context = "--- BEGIN GROUNDED CURRICULUM SOURCES ---\n[Source 1: A-Level Physics | Circular Motion | Page 45]\n$a_c = \\frac{v^2}{r}$..."

    system_prompt, user_prompt = QuestionGeneratorService._build_prompts(request, grounded_context)

    # 1. Check system prompt contains KaTeX & distractor rules
    assert "KaTeX" in system_prompt
    assert "distractor_rationale" in system_prompt
    assert "Senior Standardized STEM Exam Author" in system_prompt

    # 2. Check user prompt contains request directives
    assert "mcq_single" in user_prompt
    assert "hard" in user_prompt
    assert "analyze" in user_prompt
    assert "banked tracks" in user_prompt
    assert "BEGIN GROUNDED CURRICULUM SOURCES" in user_prompt


# ==============================================================================
# 2. End-to-End Pipeline & DB Persistence Tests (Constraints #1, #4, #5, #10)
# ==============================================================================

@pytest.mark.asyncio
async def test_question_generation_pipeline(db_session: AsyncSession, monkeypatch):
    # 1. Setup prerequisite Exam, Subject & Topic
    exam = ExamTemplate(
        code=f"PHYS_{uuid.uuid4().hex[:6]}",
        title="Physics 9702",
    )
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(
        exam_template_id=exam.id,
        title="Mechanics",
    )
    db_session.add(subject)
    await db_session.flush()

    topic_id = f"top_kinematics_{uuid.uuid4().hex[:6]}"
    topic = Topic(
        id=topic_id,
        subject_id=subject.id,
        title="Kinematics",
        order=1,
    )
    db_session.add(topic)
    await db_session.flush()

    # 2. Ingest & Index syllabus document
    doc_content = b"# Kinematics\n## Projectile Motion\nTime of flight is given by $T = \\frac{2u\\sin\\theta}{g}$."
    upload = UploadFile(filename="kinematics.md", file=io.BytesIO(doc_content))
    doc = await DocumentService.process_uploaded_document(
        session=db_session,
        file=upload,
        title="Kinematics Guide",
        topic_id=topic.id,
        exam_template_id=exam.id,
    )
    await VectorIndexerService.index_document(db_session, doc.id)
    await db_session.commit()

    # 3. Mock LLMGateway structured output
    mock_batch = GeneratedQuestionBatchSchema(
        questions=[
            GeneratedQuestionSchema(
                prompt=r"A projectile is launched with velocity $u=20\text{ m/s}$ at an angle $\theta=30^\circ$. Calculate the time of flight $T$ (take $g=9.8\text{ m/s}^2$).",
                hint=r"Recall $T = \frac{2u\sin\theta}{g}$.",
                explanation=r"Using $T = \frac{2(20)\sin(30^\circ)}{9.8} = \frac{20}{9.8} \approx 2.04\text{ s}$.",
                estimated_time_seconds=90,
                points=2.0,
                options=[
                    GeneratedOptionSchema(
                        option_key="A",
                        content="2.04 s",
                        is_correct=True,
                        order=1,
                    ),
                    GeneratedOptionSchema(
                        option_key="B",
                        content="4.08 s",
                        is_correct=False,
                        distractor_rationale="Forgot the sin(30 degrees) factor of 0.5",
                        order=2,
                    ),
                    GeneratedOptionSchema(
                        option_key="C",
                        content="3.53 s",
                        is_correct=False,
                        distractor_rationale="Used cos(30 degrees) instead of sin(30 degrees)",
                        order=3,
                    ),
                    GeneratedOptionSchema(
                        option_key="D",
                        content="1.02 s",
                        is_correct=False,
                        distractor_rationale="Forgot the factor of 2 in numerator",
                        order=4,
                    ),
                ],
                rubric_items=[
                    GeneratedRubricSchema(criterion="Applies kinematic formula correctly", points=1.0, order=1),
                    GeneratedRubricSchema(criterion="Computes numerical value with correct precision", points=1.0, order=2),
                ],
            )
        ]
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        return mock_batch

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    # 4. Execute Question Generation
    gen_request = QuestionGenerateRequest(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.HARD,
        bloom_level=BloomTaxonomy.APPLY,
        count=1,
    )

    response = await QuestionGeneratorService.generate_questions(
        session=db_session,
        request=gen_request,
    )

    # 5. Verify Response & Persistence Invariants (Constraints #1, #4)
    assert response.generated_count == 1
    assert response.grounded_sources_used >= 1

    persisted_q = response.questions[0]
    assert persisted_q.exam_template_id == exam.id
    assert persisted_q.topic_id == topic.id
    assert persisted_q.is_generated_by_ai is True
    # PRD Constraint #4: Must be staged in PENDING_VALIDATION
    assert persisted_q.validation_status == ValidationStatus.PENDING_VALIDATION
    assert len(persisted_q.options) == 4
    assert persisted_q.options[1].distractor_rationale == "Forgot the sin(30 degrees) factor of 0.5"
    assert len(persisted_q.rubric_items) == 2


# ==============================================================================
# 3. REST API Endpoint & RBAC Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_generate_endpoint_rbac(async_client: AsyncClient, db_session: AsyncSession, monkeypatch):
    # 1. Setup prerequisite Exam & Topic
    exam = ExamTemplate(code=f"GEN_{uuid.uuid4().hex[:6]}", title="Generation Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Main Subject")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Topic A", order=1)
    db_session.add(topic)
    await db_session.flush()
    await db_session.commit()

    # 2. Register Instructor & Student
    inst_email = f"gen.inst.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": inst_email, "password": "Password123!", "full_name": "Instructor Gen", "role": "instructor"},
    )
    login_inst = await async_client.post(
        "/api/v1/auth/login",
        json={"email": inst_email, "password": "Password123!"},
    )
    inst_token = login_inst.json()["access_token"]

    student_email = f"gen.stud.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": student_email, "password": "Password123!", "full_name": "Student Gen", "role": "student"},
    )
    login_stud = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_email, "password": "Password123!"},
    )
    student_token = login_stud.json()["access_token"]

    # 3. Mock LLMGateway
    mock_batch = GeneratedQuestionBatchSchema(
        questions=[
            GeneratedQuestionSchema(
                prompt="What is velocity?",
                explanation="Rate of change of displacement",
                options=[
                    GeneratedOptionSchema(option_key="A", content="dx/dt", is_correct=True),
                    GeneratedOptionSchema(option_key="B", content="d2x/dt2", is_correct=False, distractor_rationale="Confused with acceleration"),
                ],
            )
        ]
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        return mock_batch

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    payload = {
        "exam_template_id": exam.id,
        "topic_id": topic.id,
        "question_type": "mcq_single",
        "difficulty": "medium",
        "bloom_level": "understand",
        "count": 1,
    }

    # 4. Student calls /generate -> 403 Forbidden
    resp_stud = await async_client.post(
        "/api/v1/questions/generate",
        json=payload,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp_stud.status_code == 403

    # 5. Instructor calls /generate -> 201 Created
    resp_inst = await async_client.post(
        "/api/v1/questions/generate",
        json=payload,
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_inst.status_code == 201
    resp_data = resp_inst.json()
    assert resp_data["generated_count"] == 1
    assert resp_data["questions"][0]["validation_status"] == "pending_validation"
    assert resp_data["questions"][0]["is_generated_by_ai"] is True
