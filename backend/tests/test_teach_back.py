import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.llm import LLMGateway
from backend.app.core.llm.providers.mock import MockLLMProvider
from backend.app.curriculum.models import (
    BloomLevel,
    ExamTemplate,
    LearningObjective,
    Subject,
    Topic,
    TopicPrerequisite,
)
from backend.app.teach_back.models import (
    MasteryAssessmentLevel,
    TeachBackAudienceLevel,
    TeachBackEvaluation,
    TeachBackSession,
)
from backend.app.teach_back.rubric import (
    DEFAULT_RUBRIC_DIMENSIONS,
    build_rubric_system_prompt,
    calculate_overall_score,
    determine_mastery_level,
)
from backend.app.teach_back.schemas import (
    PrerequisiteGap,
    RubricCriterionScore,
    TeachBackEvaluateRequest,
    TeachBackLLMEvaluationOutput,
)
from backend.app.teach_back.service import TeachBackService


# ==============================================================================
# 1. Rubric & Mathematical Scoring Unit Tests (PRD Cap 17, FR-017)
# ==============================================================================

def test_rubric_scoring_normalized_calculation():
    """
    Verifies that multi-criterion weighted scoring scales cleanly between 0.0 and 100.0.
    """
    # 1. Perfect 5/5 across all criteria
    perfect_scores = [
        RubricCriterionScore(criterion_name="Accuracy", score=5, weight=0.30, feedback="Flawless"),
        RubricCriterionScore(criterion_name="Completeness", score=5, weight=0.25, feedback="All covered"),
        RubricCriterionScore(criterion_name="Intuition", score=5, weight=0.20, feedback="Simple"),
        RubricCriterionScore(criterion_name="Rigor", score=5, weight=0.15, feedback="Great math"),
        RubricCriterionScore(criterion_name="Prereqs", score=5, weight=0.10, feedback="Solid foundation"),
    ]
    assert calculate_overall_score(perfect_scores) == 100.0

    # 2. Minimum 1/5 across all criteria
    min_scores = [
        RubricCriterionScore(criterion_name="Accuracy", score=1, weight=0.30, feedback="Poor"),
        RubricCriterionScore(criterion_name="Completeness", score=1, weight=0.25, feedback="Poor"),
        RubricCriterionScore(criterion_name="Intuition", score=1, weight=0.20, feedback="Poor"),
        RubricCriterionScore(criterion_name="Rigor", score=1, weight=0.15, feedback="Poor"),
        RubricCriterionScore(criterion_name="Prereqs", score=1, weight=0.10, feedback="Poor"),
    ]
    assert calculate_overall_score(min_scores) == 20.0  # (1/5) * 100 = 20.0

    # 3. Mixed criteria scores:
    # (4/5)*0.30 + (3/5)*0.25 + (5/5)*0.20 + (2/5)*0.15 + (4/5)*0.10
    # = 0.24 + 0.15 + 0.20 + 0.06 + 0.08 = 0.73 * 100 = 73.0
    mixed_scores = [
        RubricCriterionScore(criterion_name="Accuracy", score=4, weight=0.30, feedback="Good"),
        RubricCriterionScore(criterion_name="Completeness", score=3, weight=0.25, feedback="Fair"),
        RubricCriterionScore(criterion_name="Intuition", score=5, weight=0.20, feedback="Excellent"),
        RubricCriterionScore(criterion_name="Rigor", score=2, weight=0.15, feedback="Missing formula"),
        RubricCriterionScore(criterion_name="Prereqs", score=4, weight=0.10, feedback="Good"),
    ]
    assert calculate_overall_score(mixed_scores) == 73.0


def test_rubric_mastery_tier_classification():
    """
    Verifies that numerical composite scores map to the correct pedagogical mastery tiers.
    """
    assert determine_mastery_level(92.0) == MasteryAssessmentLevel.MASTERED
    assert determine_mastery_level(85.0) == MasteryAssessmentLevel.MASTERED
    assert determine_mastery_level(84.9) == MasteryAssessmentLevel.COMPETENT
    assert determine_mastery_level(70.0) == MasteryAssessmentLevel.COMPETENT
    assert determine_mastery_level(69.9) == MasteryAssessmentLevel.DEVELOPING
    assert determine_mastery_level(50.0) == MasteryAssessmentLevel.DEVELOPING
    assert determine_mastery_level(49.9) == MasteryAssessmentLevel.NEEDS_REVIEW
    assert determine_mastery_level(15.0) == MasteryAssessmentLevel.NEEDS_REVIEW


def test_dynamic_prompt_builder_contains_invariants():
    """
    Verifies that the generated prompt includes topic learning objectives, KaTeX rules, and audience level.
    """
    lo = [{"code": "9702.4.1", "description": "Define momentum as mass times velocity", "formula_latex": "p = mv"}]
    prereqs = [{"id": "top_kinematics", "title": "Kinematics", "description": "Velocity and acceleration"}]

    prompt_child = build_rubric_system_prompt(
        topic_title="Linear Momentum",
        topic_description="Conservation of momentum in collisions",
        learning_objectives=lo,
        prerequisites=prereqs,
        audience_level=TeachBackAudienceLevel.CHILD_10YO,
    )
    assert "Linear Momentum" in prompt_child
    assert "9702.4.1" in prompt_child
    assert "p = mv" in prompt_child
    assert "10-year-old child" in prompt_child
    assert "KaTeX" in prompt_child
    assert "top_kinematics" in prompt_child


# ==============================================================================
# 2. Service & Multi-Criterion Evaluation Integration Tests (PRD FR-010, FR-017)
# ==============================================================================

@pytest.mark.asyncio
async def test_teach_back_service_evaluation_lifecycle(db_session: AsyncSession):
    # 1. Seed Exam, Subject, Topics, Learning Objectives, Prerequisites
    exam = ExamTemplate(code=f"TB_EX_{uuid.uuid4().hex[:6]}", title="Teach-Back Physics Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    prereq_topic = Topic(subject_id=subject.id, title="Vectors & Components", order=1)
    db_session.add(prereq_topic)
    await db_session.flush()

    main_topic = Topic(subject_id=subject.id, title="Projectile Motion", order=2)
    db_session.add(main_topic)
    await db_session.flush()

    prereq_link = TopicPrerequisite(topic_id=main_topic.id, prerequisite_topic_id=prereq_topic.id)
    db_session.add(prereq_link)

    lo = LearningObjective(
        topic_id=main_topic.id,
        code="9702.2.1",
        description="Resolve velocity into horizontal and vertical components",
        formula_latex="v_x = u \\cos\\theta, v_y = u \\sin\\theta - gt",
        bloom_level=BloomLevel.APPLY,
    )
    db_session.add(lo)
    await db_session.commit()

    # 2. Configure Mock LLM Provider with structured Teach-Back evaluation payload
    mock_eval_dict = {
        "criteria_scores": [
            {"criterion_name": "Conceptual Accuracy", "score": 4, "weight": 0.30, "feedback": "Accurate trajectory concepts."},
            {"criterion_name": "Learning Objective Completeness", "score": 4, "weight": 0.25, "feedback": "Resolved both velocity components."},
            {"criterion_name": "Intuition & Feynman Simplicity", "score": 5, "weight": 0.20, "feedback": "Great cannonball analogy."},
            {"criterion_name": "Mathematical Rigor & KaTeX", "score": 4, "weight": 0.15, "feedback": "Clear KaTeX formula notation."},
            {"criterion_name": "Prerequisite Integration", "score": 4, "weight": 0.10, "feedback": "Connected to vector resolution."},
        ],
        "strengths": ["Clear breakdown of horizontal vs vertical motion", "Correct quadratic trajectory equation"],
        "misconceptions": ["Assumed air resistance was significant at low speeds without stating condition"],
        "missing_elements": ["Did not explicitly state horizontal acceleration $a_x = 0$"],
        "prerequisite_gaps": [
            {
                "prerequisite_topic_id": prereq_topic.id,
                "prerequisite_title": "Vectors & Components",
                "gap_description": "Review resolving angles when launching from an elevated cliff.",
                "severity": "low",
            }
        ],
        "pedagogical_feedback": "Excellent explanation of projectile motion! To make it even stronger, state $a_x = 0$ explicitly.",
        "model_correction_latex": "$$x(t) = (u \\cos\\theta)t, \\quad y(t) = (u \\sin\\theta)t - \\frac{1}{2}gt^2$$",
    }

    mock_llm = MockLLMProvider(default_json=mock_eval_dict)
    gateway = LLMGateway()
    gateway.register_provider(mock_llm, is_default=True)

    # 3. Execute Service Evaluation
    student_id = str(uuid.uuid4())
    req = TeachBackEvaluateRequest(
        exam_template_id=exam.id,
        topic_id=main_topic.id,
        concept_title="Feynman Projectile Motion",
        explanation="A cannonball shot at an angle moves in two separate directions at once: sideways with constant velocity and vertically under gravity $g$...",
        audience_level=TeachBackAudienceLevel.CHILD_10YO,
    )

    eval_response = await TeachBackService.evaluate_explanation(
        session=db_session,
        student_id=student_id,
        request_in=req,
        llm_gateway=gateway,
    )

    # 4. Assertions on Response and Database Records
    assert eval_response.topic_id == main_topic.id
    assert eval_response.overall_score == 84.0  # (4*0.3 + 4*0.25 + 5*0.2 + 4*0.15 + 4*0.1) / 5 * 100 = (0.24+0.2+0.2+0.12+0.08)*100 = 84.0
    assert eval_response.assessment_level == MasteryAssessmentLevel.COMPETENT
    assert len(eval_response.criteria_scores) == 5
    assert len(eval_response.strengths) == 2
    assert len(eval_response.misconceptions) == 1
    assert len(eval_response.prerequisite_gaps) == 1
    assert eval_response.prerequisite_gaps[0].prerequisite_topic_id == prereq_topic.id
    assert "$$x(t)" in eval_response.model_correction_latex


@pytest.mark.asyncio
async def test_teach_back_topic_rubric_retrieval(db_session: AsyncSession):
    exam = ExamTemplate(code=f"TB_RUB_{uuid.uuid4().hex[:6]}", title="Rubric Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Chemistry")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Thermodynamics", order=1)
    db_session.add(topic)
    await db_session.flush()

    lo = LearningObjective(
        topic_id=topic.id,
        code="CHEM.3.1",
        description="State First Law of Thermodynamics: $\\Delta U = Q - W$",
    )
    db_session.add(lo)
    await db_session.commit()

    rubric_resp = await TeachBackService.get_topic_rubric(db_session, topic.id)
    assert rubric_resp.topic_id == topic.id
    assert rubric_resp.topic_title == "Thermodynamics"
    assert len(rubric_resp.learning_objectives) == 1
    assert len(rubric_resp.rubric_dimensions) == 5


@pytest.mark.asyncio
async def test_teach_back_missing_topic_error(db_session: AsyncSession):
    req = TeachBackEvaluateRequest(
        exam_template_id=str(uuid.uuid4()),
        topic_id=str(uuid.uuid4()),
        explanation="Some explanation here...",
    )
    with pytest.raises(ValueError, match="not found"):
        await TeachBackService.evaluate_explanation(
            session=db_session,
            student_id=str(uuid.uuid4()),
            request_in=req,
        )


# ==============================================================================
# 3. REST API, Security & Tenant Isolation Tests (Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_teach_back_full_api_suite_and_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    # Mock LLMGateway.generate_structured to return deterministic evaluation for API tests
    async def mock_generate_structured(self, messages, response_model, system_prompt=None, tier=None, temperature=None, **kwargs):
        return TeachBackLLMEvaluationOutput(
            criteria_scores=[
                RubricCriterionScore(criterion_name="Conceptual Accuracy", score=5, weight=0.30, feedback="Great physics."),
                RubricCriterionScore(criterion_name="Learning Objective Completeness", score=4, weight=0.25, feedback="Well covered."),
                RubricCriterionScore(criterion_name="Intuition & Feynman Simplicity", score=4, weight=0.20, feedback="Clear analogy."),
                RubricCriterionScore(criterion_name="Mathematical Rigor & KaTeX", score=5, weight=0.15, feedback="Accurate KaTeX."),
                RubricCriterionScore(criterion_name="Prerequisite Integration", score=4, weight=0.10, feedback="Solid foundations."),
            ],
            strengths=["Clear explanation of refraction index and speed of light."],
            misconceptions=[],
            missing_elements=[],
            prerequisite_gaps=[],
            pedagogical_feedback="Superb explanation of Snell's Law!",
            model_correction_latex="$$n_1 \\sin\\theta_1 = n_2 \\sin\\theta_2$$",
        )

    monkeypatch.setattr(LLMGateway, "generate_structured", mock_generate_structured)

    # 1. Setup Syllabus Data
    exam = ExamTemplate(code=f"API_TB_{uuid.uuid4().hex[:6]}", title="API Teach-Back Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Optics & Refraction", order=1)
    db_session.add(topic)
    await db_session.flush()

    lo = LearningObjective(
        topic_id=topic.id,
        code="9702.6.1",
        description="Snell's Law of Refraction: $n_1 \\sin\\theta_1 = n_2 \\sin\\theta_2$",
    )
    db_session.add(lo)
    await db_session.commit()

    # 2. Register Student A & Student B
    email_a = f"tb.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "TeachBack Student A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    email_b = f"tb.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "TeachBack Student B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # 3. Test Topic Rubric Endpoint
    rubric_res = await async_client.get(
        f"/api/v1/teach-back/rubric/{topic.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert rubric_res.status_code == 200
    assert rubric_res.json()["topic_title"] == "Optics & Refraction"

    # 4. Student A Submits Explanation (POST /api/v1/teach-back/evaluate)
    eval_payload = {
        "exam_template_id": exam.id,
        "topic_id": topic.id,
        "concept_title": "Light Bending in Water",
        "explanation": "Light slows down when moving from air to water, causing the wave front to bend towards the normal according to Snell's law $n_1 \\sin\\theta_1 = n_2 \\sin\\theta_2$...",
        "audience_level": "high_school_peer",
    }
    post_res = await async_client.post(
        "/api/v1/teach-back/evaluate",
        json=eval_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert post_res.status_code == 200
    res_data = post_res.json()
    assert res_data["topic_id"] == topic.id
    assert res_data["concept_title"] == "Light Bending in Water"
    assert "overall_score" in res_data
    session_id = res_data["session_id"]

    # 5. Verify PRD Alias Endpoint (/api/v1/modes/teach-back/evaluate)
    alias_res = await async_client.post(
        "/api/v1/modes/teach-back/evaluate",
        json=eval_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert alias_res.status_code == 200

    # 6. Student A Lists Past Sessions (GET /api/v1/teach-back/sessions)
    list_res = await async_client.get(
        "/api/v1/teach-back/sessions",
        params={"exam_template_id": exam.id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_res.status_code == 200
    sessions_list = list_res.json()["sessions"]
    assert len(sessions_list) == 2
    session_ids = [s["id"] for s in sessions_list]
    assert session_id in session_ids

    # 7. Student A Fetches Session Detail (GET /api/v1/teach-back/sessions/{session_id})
    detail_res = await async_client.get(
        f"/api/v1/teach-back/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == res_data["id"]

    # 8. Student B Attempts to Access Student A's Session (Constraint #2 Isolation Check)
    snoop_res = await async_client.get(
        f"/api/v1/teach-back/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert snoop_res.status_code == 404

    # 9. Unauthenticated Request Blocked
    unauth_res = await async_client.post(
        "/api/v1/teach-back/evaluate",
        json=eval_payload,
    )
    assert unauth_res.status_code == 401
