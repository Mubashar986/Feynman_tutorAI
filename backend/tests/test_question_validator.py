import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.curriculum.models import ExamTemplate, Subject, Topic
from backend.app.questions.models import (
    BloomTaxonomy,
    DifficultyLevel,
    Question,
    QuestionType,
    ValidationStatus,
)
from backend.app.questions.schemas import (
    BatchValidationRequest,
    BlindSolveSchema,
    QualityAuditSchema,
    QuestionCreate,
    QuestionOptionCreate,
    QuestionRubricItemCreate,
)
from backend.app.questions.service import QuestionBankService
from backend.app.questions.validator import (
    DUPLICATE_SIMILARITY_THRESHOLD,
    QUESTION_COLLECTION_NAME,
    QuestionValidationService,
)
from backend.app.core.vector import get_vector_store
from backend.app.core.vector.base import VectorPoint
from backend.app.core.llm.embedding import get_embedding_provider


# ==============================================================================
# 1. Blind Solver Gate Tests (PRD Constraint #4, FR-015)
# ==============================================================================

@pytest.mark.asyncio
async def test_blind_solver_agreement_success(db_session: AsyncSession, monkeypatch):
    # Setup Question
    exam = ExamTemplate(code=f"VAL_{uuid.uuid4().hex[:6]}", title="Validation Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Dynamics", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.MEDIUM,
        bloom_level=BloomTaxonomy.APPLY,
        prompt="A mass $m=5\\text{ kg}$ experiences a net force $F=20\\text{ N}$. Calculate the acceleration $a$.",
        explanation="Using Newton's second law: $a = \\frac{F}{m} = \\frac{20}{5} = 4\\text{ m/s}^2$.",
        options=[
            QuestionOptionCreate(option_key="A", content="4 m/s^2", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="100 m/s^2", is_correct=False, distractor_rationale="Multiplied instead of dividing", order=2),
            QuestionOptionCreate(option_key="C", content="0.25 m/s^2", is_correct=False, distractor_rationale="Inverted ratio", order=3),
            QuestionOptionCreate(option_key="D", content="15 m/s^2", is_correct=False, distractor_rationale="Subtracted mass from force", order=4),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)

    # Mock solver output agreeing with Option A
    mock_solve_result = BlindSolveSchema(
        is_solvable=True,
        derived_solution="From F = ma, a = F/m = 20 / 5 = 4 m/s^2",
        derived_answer="4 m/s^2",
        matched_option_key="A",
        confidence_score=0.99,
        critique=None,
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        if schema == BlindSolveSchema:
            return mock_solve_result
        raise NotImplementedError

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    is_solvable, solver_agrees, derived_ans, matched_key, critique = await QuestionValidationService._run_blind_solver(question)

    assert is_solvable is True
    assert solver_agrees is True
    assert derived_ans == "4 m/s^2"
    assert matched_key == "A"
    assert critique is None


@pytest.mark.asyncio
async def test_blind_solver_disagreement_detection(db_session: AsyncSession, monkeypatch):
    # Setup Question with incorrect answer key
    exam = ExamTemplate(code=f"DIS_{uuid.uuid4().hex[:6]}", title="Disagreement Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Dynamics", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.MEDIUM,
        bloom_level=BloomTaxonomy.APPLY,
        prompt="A mass $m=5\\text{ kg}$ experiences a net force $F=20\\text{ N}$. Calculate the acceleration $a$.",
        explanation="Wrong author explanation",
        options=[
            QuestionOptionCreate(option_key="A", content="4 m/s^2", is_correct=False, order=1),
            QuestionOptionCreate(option_key="B", content="100 m/s^2", is_correct=True, distractor_rationale="Author marked wrong answer!", order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)

    # Solver correctly derives 4 m/s^2 (Option A) while author marked Option B as correct
    mock_solve_result = BlindSolveSchema(
        is_solvable=True,
        derived_solution="a = F/m = 20 / 5 = 4 m/s^2",
        derived_answer="4 m/s^2",
        matched_option_key="A",
        confidence_score=0.95,
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        return mock_solve_result

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    is_solvable, solver_agrees, derived_ans, matched_key, critique = await QuestionValidationService._run_blind_solver(question)

    assert is_solvable is True
    assert solver_agrees is False  # Solver found A, but question declared B as correct!


# ==============================================================================
# 2. Semantic Deduplication Gate Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_semantic_deduplication_detection(db_session: AsyncSession):
    exam = ExamTemplate(code=f"DED_{uuid.uuid4().hex[:6]}", title="Dedup Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Kinematics", order=1)
    db_session.add(topic)
    await db_session.flush()

    # Pre-index an existing question in vector store
    existing_prompt = "What is the speed of light in a vacuum?"
    embedder = get_embedding_provider()
    vec = await embedder.embed_text(existing_prompt)

    vector_store = get_vector_store()
    await vector_store.create_collection(QUESTION_COLLECTION_NAME, embedder.dimension)
    await vector_store.upsert_points(
        QUESTION_COLLECTION_NAME,
        [
            VectorPoint(
                id="existing_q_123",
                vector=vec,
                payload={
                    "question_id": "existing_q_123",
                    "exam_template_id": exam.id,
                    "topic_id": topic.id,
                    "prompt": existing_prompt,
                },
            )
        ],
    )

    # Question 1: Identical prompt (Duplicate)
    dup_q = Question(
        id=str(uuid.uuid4()),
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt=existing_prompt,
        explanation="Speed of light is 3e8 m/s",
    )

    max_sim, matches = await QuestionValidationService._check_duplicates(dup_q)
    assert max_sim >= 0.99
    assert len(matches) >= 1
    assert matches[0].matched_question_id == "existing_q_123"

    # Question 2: Completely different prompt (Unique)
    unique_q = Question(
        id=str(uuid.uuid4()),
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="State the first law of thermodynamics and explain conservation of energy.",
        explanation="Energy cannot be created or destroyed.",
    )

    max_sim_uniq, matches_uniq = await QuestionValidationService._check_duplicates(unique_q)
    assert max_sim_uniq < DUPLICATE_SIMILARITY_THRESHOLD


# ==============================================================================
# 3. End-to-End Single Question Validation & State Promotion (Constraint #4)
# ==============================================================================

@pytest.mark.asyncio
async def test_full_question_validation_promotion(db_session: AsyncSession, monkeypatch):
    exam = ExamTemplate(code=f"FULL_{uuid.uuid4().hex[:6]}", title="Full Validation Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Optics", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        difficulty=DifficultyLevel.HARD,
        bloom_level=BloomTaxonomy.ANALYZE,
        validation_status=ValidationStatus.PENDING_VALIDATION,
        prompt="Calculate the refractive index $n$ if the angle of incidence is $\\theta_1 = 30^\\circ$ and angle of refraction is $\\theta_2 = 19.5^\\circ$.",
        explanation="Using Snell's law: $n = \\frac{\\sin(30^\\circ)}{\\sin(19.5^\\circ)} = \\frac{0.5}{0.3338} \\approx 1.50$.",
        options=[
            QuestionOptionCreate(option_key="A", content="1.50", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="0.67", is_correct=False, distractor_rationale="Inverted Snell ratio", order=2),
            QuestionOptionCreate(option_key="C", content="1.33", is_correct=False, distractor_rationale="Confused with water index", order=3),
            QuestionOptionCreate(option_key="D", content="2.00", is_correct=False, distractor_rationale="Used sin(30) * 4", order=4),
        ],
        rubric_items=[
            QuestionRubricItemCreate(criterion="Correctly states Snell's law", points=1.0, order=1),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    assert question.validation_status == ValidationStatus.PENDING_VALIDATION

    # Mock LLM Gateway for Blind Solver and Quality Audit
    mock_solve = BlindSolveSchema(
        is_solvable=True,
        derived_solution="n = sin(30) / sin(19.5) = 1.50",
        derived_answer="1.50",
        matched_option_key="A",
        confidence_score=0.98,
    )
    mock_audit = QualityAuditSchema(
        katex_score=25,
        clarity_score=24,
        distractor_score=24,
        derivation_score=25,
        overall_critique="Exemplary physics problem with accurate KaTeX and diagnostic distractors.",
        suggested_improvements=[],
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        if schema == BlindSolveSchema:
            return mock_solve
        elif schema == QualityAuditSchema:
            return mock_audit
        raise NotImplementedError

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    # Run validation
    report = await QuestionValidationService.validate_question(db_session, question.id)

    # Invariant Checks
    assert report.question_id == question.id
    assert report.is_solvable is True
    assert report.solver_agrees is True
    assert report.quality_scores.total_score == 98
    assert report.validation_status == ValidationStatus.VALIDATED

    # Verify DB persistence
    refreshed_q = await QuestionBankService.get_question(db_session, question.id)
    assert refreshed_q.validation_status == ValidationStatus.VALIDATED


@pytest.mark.asyncio
async def test_question_validation_rejection_on_math_failure(db_session: AsyncSession, monkeypatch):
    exam = ExamTemplate(code=f"REJ_{uuid.uuid4().hex[:6]}", title="Rejection Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Optics", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        question_type=QuestionType.MCQ_SINGLE,
        prompt="Broken question with missing parameters and impossible geometry.",
        explanation="Broken derivation.",
        options=[
            QuestionOptionCreate(option_key="A", content="Impossible", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="Undefined", is_correct=False, order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)

    # Solver detects unsolvable
    mock_solve = BlindSolveSchema(
        is_solvable=False,
        derived_solution="Missing refractive index of first medium",
        derived_answer="Cannot solve",
        matched_option_key=None,
        confidence_score=0.0,
        critique="Problem is physically under-specified",
    )
    mock_audit = QualityAuditSchema(
        katex_score=10,
        clarity_score=10,
        distractor_score=10,
        derivation_score=10,
        overall_critique="Poor quality and missing information.",
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        if schema == BlindSolveSchema:
            return mock_solve
        elif schema == QualityAuditSchema:
            return mock_audit

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    report = await QuestionValidationService.validate_question(db_session, question.id)

    assert report.is_solvable is False
    assert report.validation_status == ValidationStatus.REJECTED

    refreshed_q = await QuestionBankService.get_question(db_session, question.id)
    assert refreshed_q.validation_status == ValidationStatus.REJECTED


# ==============================================================================
# 4. Batch Validation Pipeline & REST API Verification
# ==============================================================================

@pytest.mark.asyncio
async def test_batch_validation_pipeline(db_session: AsyncSession, monkeypatch):
    exam = ExamTemplate(code=f"BATCH_{uuid.uuid4().hex[:6]}", title="Batch Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Thermodynamics", order=1)
    db_session.add(topic)
    await db_session.flush()

    # Create 3 questions in PENDING_VALIDATION
    for i in range(3):
        q = QuestionCreate(
            exam_template_id=exam.id,
            topic_id=topic.id,
            prompt=f"Thermodynamics Problem {i}: Calculate work done $\\Delta W = P\\Delta V$.",
            explanation=f"Work done is {i * 10} J.",
            options=[
                QuestionOptionCreate(option_key="A", content=f"{i * 10} J", is_correct=True, order=1),
                QuestionOptionCreate(option_key="B", content="0 J", is_correct=False, distractor_rationale="Assumed isochoric", order=2),
            ],
        )
        await QuestionBankService.create_question(db_session, q)

    mock_solve = BlindSolveSchema(
        is_solvable=True,
        derived_solution="Computed correctly",
        derived_answer="Answer",
        matched_option_key="A",
        confidence_score=0.95,
    )
    mock_audit = QualityAuditSchema(
        katex_score=25,
        clarity_score=23,
        distractor_score=22,
        derivation_score=24,
        overall_critique="Good problem",
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        if schema == BlindSolveSchema:
            return mock_solve
        elif schema == QualityAuditSchema:
            return mock_audit

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    batch_resp = await QuestionValidationService.batch_validate(
        session=db_session,
        topic_id=topic.id,
        limit=10,
    )

    assert batch_resp.total_processed == 3
    assert batch_resp.validated_count == 3
    assert batch_resp.rejected_count == 0
    assert len(batch_resp.reports) == 3


@pytest.mark.asyncio
async def test_validation_api_endpoints_and_rbac(async_client: AsyncClient, db_session: AsyncSession, monkeypatch):
    exam = ExamTemplate(code=f"API_{uuid.uuid4().hex[:6]}", title="API Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Waves", order=1)
    db_session.add(topic)
    await db_session.flush()

    q_create = QuestionCreate(
        exam_template_id=exam.id,
        topic_id=topic.id,
        prompt="Wave speed $v=f\\lambda$. Given $f=100\\text{ Hz}, \\lambda=2\\text{ m}$, find $v$.",
        explanation="$v = 100 \\times 2 = 200\\text{ m/s}$.",
        options=[
            QuestionOptionCreate(option_key="A", content="200 m/s", is_correct=True, order=1),
            QuestionOptionCreate(option_key="B", content="50 m/s", is_correct=False, distractor_rationale="Divided frequency by wavelength", order=2),
        ],
    )
    question = await QuestionBankService.create_question(db_session, q_create)
    await db_session.commit()

    # Register Instructor & Student
    inst_email = f"val.inst.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": inst_email, "password": "Password123!", "full_name": "Instructor Val", "role": "instructor"},
    )
    login_inst = await async_client.post(
        "/api/v1/auth/login",
        json={"email": inst_email, "password": "Password123!"},
    )
    inst_token = login_inst.json()["access_token"]

    stud_email = f"val.stud.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": stud_email, "password": "Password123!", "full_name": "Student Val", "role": "student"},
    )
    login_stud = await async_client.post(
        "/api/v1/auth/login",
        json={"email": stud_email, "password": "Password123!"},
    )
    stud_token = login_stud.json()["access_token"]

    mock_solve = BlindSolveSchema(
        is_solvable=True,
        derived_solution="v = f * lambda = 200 m/s",
        derived_answer="200 m/s",
        matched_option_key="A",
        confidence_score=0.99,
    )
    mock_audit = QualityAuditSchema(
        katex_score=25,
        clarity_score=25,
        distractor_score=25,
        derivation_score=25,
        overall_critique="Perfect physics item",
    )

    async def mock_generate_structured(self, schema, prompt, system_prompt=None, **kwargs):
        if schema == BlindSolveSchema:
            return mock_solve
        elif schema == QualityAuditSchema:
            return mock_audit

    from backend.app.core.llm.gateway import LLMGateway
    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    # 1. Student calls validate -> 403 Forbidden
    resp_stud = await async_client.post(
        f"/api/v1/questions/{question.id}/validate",
        headers={"Authorization": f"Bearer {stud_token}"},
    )
    assert resp_stud.status_code == 403

    # 2. Instructor calls validate -> 200 OK
    resp_inst = await async_client.post(
        f"/api/v1/questions/{question.id}/validate",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_inst.status_code == 200
    report_data = resp_inst.json()
    assert report_data["validation_status"] == "validated"
    assert report_data["is_solvable"] is True
    assert report_data["solver_agrees"] is True
    assert report_data["quality_scores"]["total_score"] == 100

    # 3. Instructor calls batch-validate -> 200 OK
    resp_batch = await async_client.post(
        "/api/v1/questions/batch-validate",
        json={"topic_id": topic.id, "limit": 10},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_batch.status_code == 200
    batch_data = resp_batch.json()
    assert "total_processed" in batch_data
