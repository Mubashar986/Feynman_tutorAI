import uuid
import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.advanced_modes.fallacies import (
    FALLACY_TAXONOMY_MAP,
    build_adversarial_challenge_prompt,
    build_defense_evaluation_prompt,
    build_why_wrong_diagnostic_prompt,
)
from backend.app.advanced_modes.models import (
    AdversarialChallenge,
    AdversarialSession,
    AdversarialSessionStatus,
    DefenseOutcome,
    FallacyCategory,
    WhyWrongDiagnostic,
)
from backend.app.advanced_modes.schemas import (
    AdversarialChallengeOutput,
    AdversarialChallengeRequest,
    AdversarialDefendRequest,
    DefenseEvaluationOutput,
    WhyWrongDiagnosticOutput,
    WhyWrongDiagnosticRequest,
)
from backend.app.advanced_modes.service import (
    AdversarialTutorService,
    WhyWrongDiagnosticService,
)
from backend.app.core.llm import LLMGateway
from backend.app.curriculum.models import ExamTemplate, LearningObjective, Subject, Topic


# ==============================================================================
# 1. Unit Tests: Taxonomy, Prompt Invariants & Logic
# ==============================================================================

def test_fallacy_taxonomy_registry():
    assert len(FALLACY_TAXONOMY_MAP) == 7
    for cat in FallacyCategory:
        assert cat in FALLACY_TAXONOMY_MAP
        assert "title" in FALLACY_TAXONOMY_MAP[cat]
        assert "description" in FALLACY_TAXONOMY_MAP[cat]
        assert "typical_trap" in FALLACY_TAXONOMY_MAP[cat]


def test_adversarial_challenge_prompt_builder():
    prompt = build_adversarial_challenge_prompt(
        topic_title="Newtonian Mechanics",
        topic_description="Forces and kinematics in one and two dimensions",
        learning_objectives=[
            {"code": "9702.1.1", "description": "State Newton's First Law", "formula_latex": "F_{net} = 0 \\implies v = \\text{const}"}
        ],
    )
    assert "Newtonian Mechanics" in prompt
    assert "9702.1.1" in prompt
    assert "KaTeX" in prompt
    assert "COUNTEREXAMPLE" in prompt


def test_defense_evaluation_prompt_builder():
    prompt = build_defense_evaluation_prompt(
        topic_title="Circular Motion",
        student_thesis="Centripetal force is a distinct new physical force pulling outward.",
        counterexample_scenario="A satellite in orbit only experiences gravitational force pulling inward.",
        challenge_question="Where does the outward force originate if the only interaction is gravity?",
    )
    assert "Circular Motion" in prompt
    assert "Centripetal force" in prompt
    assert "satellite in orbit" in prompt
    assert "defended_successfully" in prompt
    assert "logical_collapse" in prompt


def test_why_wrong_diagnostic_prompt_builder():
    prompt = build_why_wrong_diagnostic_prompt(
        topic_title="Thermodynamics",
        topic_description="First and second laws of thermodynamics",
        learning_objectives=[{"code": "9702.2.1", "description": "First Law of Thermodynamics", "formula_latex": "\\Delta U = q + w"}],
    )
    assert "Thermodynamics" in prompt
    assert "9702.2.1" in prompt
    assert "boundary_condition_blindness" in prompt
    assert "state_vs_rate_confusion" in prompt


# ==============================================================================
# 2. Service Integration Tests: Adversarial & Diagnostic Lifecycles
# ==============================================================================

@pytest.mark.asyncio
async def test_adversarial_service_challenge_and_defense_lifecycle(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    # 1. Setup Syllabus Data
    exam = ExamTemplate(code=f"ADV_EXAM_{uuid.uuid4().hex[:6]}", title="Adversarial Test Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Work, Energy and Power", order=1)
    db_session.add(topic)
    await db_session.flush()

    lo = LearningObjective(
        topic_id=topic.id,
        code="9702.3.1",
        description="Work done by a force: $W = Fd \\cos\\theta$",
        formula_latex="W = Fd \\cos\\theta",
    )
    db_session.add(lo)
    await db_session.commit()

    student_id = f"student_{uuid.uuid4().hex[:8]}"

    # 2. Mock LLM Gateway for Challenge Generation
    async def mock_challenge_gen(self, messages, response_model, system_prompt=None, tier=None, temperature=None, **kwargs):
        return AdversarialChallengeOutput(
            counterexample_title="Carrying a Heavy Box Horizontally",
            counterexample_scenario="A student carries a $20\\text{ kg}$ box horizontally at constant speed. Force is upward ($mg$), displacement is horizontal ($\\theta = 90^\\circ$).",
            edge_case_condition="Angle $\\theta = 90^\\circ$ between force vector and displacement vector.",
            challenge_question="You claimed carrying heavy objects always does work on the object. Does the upward supporting force do work on the box during horizontal motion?",
            underlying_principle="Work is scalar product $W = \\vec{F} \\cdot \\vec{d} = Fd \\cos\\theta$.",
        )

    monkeypatch.setattr(LLMGateway, "generate_structured", mock_challenge_gen)

    # 3. Generate Challenge
    challenge_req = AdversarialChallengeRequest(
        exam_template_id=exam.id,
        topic_id=topic.id,
        student_thesis="Carrying heavy weights across a flat room does massive physical work on the weight because you exert upward force against gravity.",
    )
    challenge_res = await AdversarialTutorService.generate_challenge(
        session=db_session,
        student_id=student_id,
        request_in=challenge_req,
    )

    assert challenge_res.session_id is not None
    assert challenge_res.challenge_id is not None
    assert challenge_res.counterexample_title == "Carrying a Heavy Box Horizontally"
    assert "90^\\circ" in challenge_res.edge_case_condition

    # 4. Mock LLM Gateway for Defense Evaluation
    async def mock_defense_eval(self, messages, response_model, system_prompt=None, tier=None, temperature=None, **kwargs):
        return DefenseEvaluationOutput(
            robustness_score=85.0,
            defense_outcome=DefenseOutcome.VALID_ADAPTATION,
            valid_points=[
                "Correctly acknowledged that $\\cos(90^\\circ) = 0$, so no work is done on the box by the upward force.",
                "Clarified that biological metabolic energy is spent in muscles, but mechanical work on the box is zero.",
            ],
            logical_flaws=[],
            feedback="Excellent distinction between biological muscle fatigue and thermodynamic mechanical work.",
            model_synthesis_latex="$$W = Fd \\cos(90^\\circ) = 0\\text{ J}$$",
        )

    monkeypatch.setattr(LLMGateway, "generate_structured", mock_defense_eval)

    # 5. Evaluate Defense
    defend_req = AdversarialDefendRequest(
        session_id=challenge_res.session_id,
        challenge_id=challenge_res.challenge_id,
        student_defense="I realize my initial claim confused biological fatigue with mechanical work. Since the upward force is perpendicular to displacement ($\\theta = 90^\\circ$), $\\cos(90^\\circ) = 0$, so mechanical work on the box is zero.",
    )
    defense_res = await AdversarialTutorService.evaluate_defense(
        session=db_session,
        student_id=student_id,
        request_in=defend_req,
    )

    assert defense_res.robustness_score == 85.0
    assert defense_res.defense_outcome == DefenseOutcome.VALID_ADAPTATION
    assert len(defense_res.valid_points) == 2
    assert "$$W = Fd" in defense_res.model_synthesis_latex


@pytest.mark.asyncio
async def test_why_wrong_diagnostic_service_lifecycle(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    # 1. Setup Syllabus & Question Data
    exam = ExamTemplate(code=f"DIAG_EXAM_{uuid.uuid4().hex[:6]}", title="Diagnostic Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Gravitation", order=1)
    db_session.add(topic)
    await db_session.flush()

    lo = LearningObjective(
        topic_id=topic.id,
        code="9702.4.1",
        description="Newton's Law of Gravitation: $F = G \\frac{M m}{r^2}$",
        formula_latex="F = G \\frac{M m}{r^2}",
    )
    db_session.add(lo)
    await db_session.commit()

    student_id = f"student_{uuid.uuid4().hex[:8]}"

    # 2. Mock LLM Gateway for Why-You-Are-Wrong Diagnostic
    async def mock_diag_gen(self, messages, response_model, system_prompt=None, tier=None, temperature=None, **kwargs):
        return WhyWrongDiagnosticOutput(
            fallacy_category=FallacyCategory.INVERSE_RELATION_CONFUSION,
            why_incorrect_explanation="You assumed that doubling the orbital radius halves the gravitational force, but gravity obeys an inverse-square law $F \\propto 1/r^2$. Doubling $r$ decreases force by a factor of $2^2 = 4$.",
            mental_trap_description="Linear scaling bias: instinctively assuming direct inverse proportionality ($1/r$) instead of quadratic attenuation ($1/r^2$).",
            recognition_rule="Whenever distance $r$ changes in gravitation or electrostatics, square the scaling factor: $r' = 2r \\implies F' = \\frac{1}{2^2} F = \\frac{1}{4}F$.",
            repair_action_summary="Practice 3 inverse-square scaling problems comparing $r \\to 2r, 3r, r/2$.",
            correct_derivation_latex="$$F' = G \\frac{Mm}{(2r)^2} = \\frac{1}{4} G \\frac{Mm}{r^2} = \\frac{1}{4}F$$",
        )

    monkeypatch.setattr(LLMGateway, "generate_structured", mock_diag_gen)

    # 3. Request Diagnosis
    diag_req = WhyWrongDiagnosticRequest(
        topic_id=topic.id,
        question_prompt="If the distance between two planets is doubled, what happens to the gravitational force between them?",
        selected_option_key="B",
        selected_answer_text="The force is halved ($F/2$).",
        correct_answer_text="The force is quartered ($F/4$).",
    )

    diag_res = await WhyWrongDiagnosticService.diagnose_incorrect_answer(
        session=db_session,
        student_id=student_id,
        request_in=diag_req,
    )

    assert diag_res.id is not None
    assert diag_res.fallacy_category == FallacyCategory.INVERSE_RELATION_CONFUSION
    assert "inverse-square" in diag_res.why_incorrect_explanation
    assert "Linear scaling bias" in diag_res.mental_trap_description
    assert "$$F' = G" in diag_res.correct_derivation_latex


# ==============================================================================
# 3. REST API & Tenant Isolation Tests (Constraint #2, FR-022)
# ==============================================================================

@pytest.mark.asyncio
async def test_adversarial_and_why_wrong_full_api_suite_and_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    # Mock LLM Gateway for both Adversarial Challenge and Diagnostic Output
    async def mock_gateway_call(self, messages, response_model, system_prompt=None, tier=None, temperature=None, **kwargs):
        if response_model == AdversarialChallengeOutput:
            return AdversarialChallengeOutput(
                counterexample_title="Relativistic Speed Limit",
                counterexample_scenario="A particle is accelerated by a constant force for infinite time. Classical $v = at$ implies $v \\to \\infty > c$.",
                edge_case_condition="Extreme time limit $t \\to \\infty$ approaching speed of light $c$.",
                challenge_question="How does your constant acceleration equation hold when $v$ approaches $c$?",
                underlying_principle="Special relativity limits velocity to $c$.",
            )
        elif response_model == DefenseEvaluationOutput:
            return DefenseEvaluationOutput(
                robustness_score=92.0,
                defense_outcome=DefenseOutcome.DEFENDED_SUCCESSFULLY,
                valid_points=["Correctly identified that classical kinematics is only valid for $v \\ll c$."],
                logical_flaws=[],
                feedback="Flawless defense bounding classical mechanics.",
                model_synthesis_latex="$$p = \\gamma m v = \\frac{mv}{\\sqrt{1 - v^2/c^2}}$$",
            )
        elif response_model == WhyWrongDiagnosticOutput:
            return WhyWrongDiagnosticOutput(
                fallacy_category=FallacyCategory.STATE_VS_RATE_CONFUSION,
                why_incorrect_explanation="At the highest point of a projectile, velocity is zero momentarily, but acceleration due to gravity remains $9.81\\text{ m/s}^2$ downward.",
                mental_trap_description="Confusing instantaneous state ($v=0$) with rate of change ($a = dv/dt = -g$).",
                recognition_rule="Kinematic apex rule: Zero velocity does NOT mean zero acceleration if net force is non-zero.",
                repair_action_summary="Review velocity vs acceleration graphs for vertical motion.",
                correct_derivation_latex="$$v_y(t_{\\text{apex}}) = 0, \\quad a_y = -g = -9.81\\text{ m/s}^2$$",
            )
        raise ValueError(f"Unexpected response model: {response_model}")

    monkeypatch.setattr(LLMGateway, "generate_structured", mock_gateway_call)

    # 1. Setup Syllabus Data
    exam = ExamTemplate(code=f"API_ADV_{uuid.uuid4().hex[:6]}", title="API Advanced Modes Exam")
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(exam_template_id=exam.id, title="Physics")
    db_session.add(subject)
    await db_session.flush()

    topic = Topic(subject_id=subject.id, title="Relativity & Kinematics", order=1)
    db_session.add(topic)
    await db_session.flush()

    lo = LearningObjective(
        topic_id=topic.id,
        code="9702.5.1",
        description="Classical vs Relativistic limits",
    )
    db_session.add(lo)
    await db_session.commit()

    # 2. Register Student A & Student B
    email_a = f"adv.a.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Adv Student A", "role": "student"},
    )
    login_a = await async_client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]

    email_b = f"adv.b.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Adv Student B", "role": "student"},
    )
    login_b = await async_client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # 3. Student A Initiates Adversarial Challenge (POST /api/v1/modes/adversarial/challenge)
    challenge_payload = {
        "exam_template_id": exam.id,
        "topic_id": topic.id,
        "student_thesis": "Under a constant non-zero net force, an object's speed increases linearly forever without any upper bound.",
    }
    post_ch_res = await async_client.post(
        "/api/v1/modes/adversarial/challenge",
        json=challenge_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert post_ch_res.status_code == 200
    ch_data = post_ch_res.json()
    assert ch_data["counterexample_title"] == "Relativistic Speed Limit"
    session_id = ch_data["session_id"]
    challenge_id = ch_data["challenge_id"]

    # 4. Student A Submits Defense (POST /api/v1/modes/adversarial/defend)
    defend_payload = {
        "session_id": session_id,
        "challenge_id": challenge_id,
        "student_defense": "My original statement only holds within the non-relativistic domain where $v \\ll c$. When approaching $c$, relativistic mass/momentum prevents exceeding $c$.",
    }
    post_def_res = await async_client.post(
        "/api/v1/modes/adversarial/defend",
        json=defend_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert post_def_res.status_code == 200
    def_data = post_def_res.json()
    assert def_data["robustness_score"] == 92.0
    assert def_data["defense_outcome"] == "defended_successfully"

    # 5. Student A Lists Sessions (GET /api/v1/modes/adversarial/sessions)
    list_res = await async_client.get(
        "/api/v1/modes/adversarial/sessions",
        params={"exam_template_id": exam.id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_res.status_code == 200
    assert len(list_res.json()["sessions"]) == 1
    assert list_res.json()["sessions"][0]["id"] == session_id

    # 6. Student A Gets Session Detail (GET /api/v1/modes/adversarial/sessions/{session_id})
    detail_res = await async_client.get(
        f"/api/v1/modes/adversarial/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "defended"
    assert len(detail_res.json()["challenges"]) == 1

    # 7. Student B Snoop Attempt on Student A's Session (Constraint #2 Isolation Check)
    snoop_res = await async_client.get(
        f"/api/v1/modes/adversarial/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert snoop_res.status_code == 404

    # 8. Student A Requests Why-You-Are-Wrong Diagnosis (POST /api/v1/modes/why-wrong/diagnose)
    diag_payload = {
        "topic_id": topic.id,
        "question_prompt": "What is the acceleration of a ball thrown vertically upward when it reaches its maximum height?",
        "selected_option_key": "A",
        "selected_answer_text": "Acceleration is $0\\text{ m/s}^2$ because it stops moving.",
        "correct_answer_text": "Acceleration is $9.81\\text{ m/s}^2$ downward.",
    }
    diag_res = await async_client.post(
        "/api/v1/modes/why-wrong/diagnose",
        json=diag_payload,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert diag_res.status_code == 200
    diag_data = diag_res.json()
    assert diag_data["fallacy_category"] == "state_vs_rate_confusion"
    assert "Kinematic apex rule" in diag_data["recognition_rule"]

    # 9. Student A Lists Diagnostics (GET /api/v1/modes/why-wrong/diagnostics)
    list_diag_res = await async_client.get(
        "/api/v1/modes/why-wrong/diagnostics",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_diag_res.status_code == 200
    assert len(list_diag_res.json()) >= 1
    assert list_diag_res.json()[0]["id"] == diag_data["id"]

    # 10. Unauthenticated Requests Blocked (401)
    unauth_res = await async_client.post(
        "/api/v1/modes/adversarial/challenge",
        json=challenge_payload,
    )
    assert unauth_res.status_code == 401
