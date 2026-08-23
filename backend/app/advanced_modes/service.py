import logging
from typing import List, Optional
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.advanced_modes.fallacies import (
    build_adversarial_challenge_prompt,
    build_defense_evaluation_prompt,
    build_why_wrong_diagnostic_prompt,
)
from backend.app.advanced_modes.models import (
    AdversarialChallenge,
    AdversarialSession,
    AdversarialSessionStatus,
    WhyWrongDiagnostic,
)
from backend.app.advanced_modes.schemas import (
    AdversarialChallengeOutput,
    AdversarialChallengeResponse,
    AdversarialChallengeSummary,
    AdversarialDefendRequest,
    AdversarialSessionDetailResponse,
    AdversarialSessionListResponse,
    DefenseEvaluationOutput,
    DefenseEvaluationResponse,
    WhyWrongDiagnosticOutput,
    WhyWrongDiagnosticRequest,
    WhyWrongDiagnosticResponse,
)
from backend.app.core.llm import LLMGateway, LLMMessage, MessageRole, ModelTier
from backend.app.curriculum.models import LearningObjective, Topic

logger = logging.getLogger("adaptive_exam_platform.advanced_modes.service")


# ==============================================================================
# 1. Adversarial Tutor Service (PRD Cap 18, FR-018)
# ==============================================================================

class AdversarialTutorService:
    """
    Orchestrates Devil's Advocate Socratic sparring dialogues and defense evaluation.
    """

    @classmethod
    async def generate_challenge(
        cls,
        session: AsyncSession,
        student_id: str,
        request_in,
        llm_gateway: Optional[LLMGateway] = None,
    ) -> AdversarialChallengeResponse:
        gateway = llm_gateway or LLMGateway()

        # 1. Fetch Syllabus Topic & Learning Objectives
        topic = (await session.exec(select(Topic).where(Topic.id == request_in.topic_id))).first()
        if not topic:
            raise ValueError(f"Topic with ID '{request_in.topic_id}' not found.")

        los = (await session.exec(select(LearningObjective).where(LearningObjective.topic_id == topic.id))).all()
        los_data = [{"code": lo.code, "description": lo.description, "formula_latex": lo.formula_latex} for lo in los]

        # 2. Build Counterfactual Prompt
        system_prompt = build_adversarial_challenge_prompt(
            topic_title=topic.title,
            topic_description=topic.description,
            learning_objectives=los_data,
        )

        user_content = (
            f"### STUDENT CLAIM / THESIS TO CHALLENGE:\n"
            f"{request_in.student_thesis}\n\n"
            f"Synthesize an authentic counterexample or edge-case condition where this claim fails or causes a contradiction."
        )

        # 3. Structured LLM Generation
        llm_out: AdversarialChallengeOutput = await gateway.generate_structured(
            messages=[LLMMessage(role=MessageRole.USER, content=user_content)],
            response_model=AdversarialChallengeOutput,
            system_prompt=system_prompt,
            tier=ModelTier.REASONING,
            temperature=0.2,
        )

        # 4. Atomic Database Persistence
        adv_session = AdversarialSession(
            student_id=student_id,
            exam_template_id=request_in.exam_template_id,
            topic_id=topic.id,
            student_thesis=request_in.student_thesis,
            status=AdversarialSessionStatus.CHALLENGE_ACTIVE,
        )
        session.add(adv_session)
        await session.flush()

        challenge = AdversarialChallenge(
            session_id=adv_session.id,
            student_id=student_id,
            counterexample_title=llm_out.counterexample_title,
            counterexample_scenario=llm_out.counterexample_scenario,
            edge_case_condition=llm_out.edge_case_condition,
            challenge_question=llm_out.challenge_question,
        )
        session.add(challenge)
        await session.commit()
        await session.refresh(challenge)

        return AdversarialChallengeResponse(
            session_id=adv_session.id,
            challenge_id=challenge.id,
            topic_id=topic.id,
            student_thesis=request_in.student_thesis,
            counterexample_title=challenge.counterexample_title,
            counterexample_scenario=challenge.counterexample_scenario,
            edge_case_condition=challenge.edge_case_condition,
            challenge_question=challenge.challenge_question,
            created_at=challenge.created_at,
        )

    @classmethod
    async def evaluate_defense(
        cls,
        session: AsyncSession,
        student_id: str,
        request_in: AdversarialDefendRequest,
        llm_gateway: Optional[LLMGateway] = None,
    ) -> DefenseEvaluationResponse:
        gateway = llm_gateway or LLMGateway()

        # 1. Fetch Session & Challenge enforcing student isolation
        adv_session = (
            await session.exec(
                select(AdversarialSession).where(
                    AdversarialSession.id == request_in.session_id,
                    AdversarialSession.student_id == student_id,
                )
            )
        ).first()
        if not adv_session:
            raise ValueError(f"Adversarial session '{request_in.session_id}' not found.")

        challenge = (
            await session.exec(
                select(AdversarialChallenge).where(
                    AdversarialChallenge.id == request_in.challenge_id,
                    AdversarialChallenge.session_id == adv_session.id,
                )
            )
        ).first()
        if not challenge:
            raise ValueError(f"Adversarial challenge '{request_in.challenge_id}' not found.")

        topic = (await session.exec(select(Topic).where(Topic.id == adv_session.topic_id))).first()
        topic_title = topic.title if topic else "Syllabus Topic"

        # 2. Build Defense Evaluation Prompt
        system_prompt = build_defense_evaluation_prompt(
            topic_title=topic_title,
            student_thesis=adv_session.student_thesis,
            counterexample_scenario=challenge.counterexample_scenario,
            challenge_question=challenge.challenge_question,
        )

        user_content = (
            f"### STUDENT DEFENSE SUBMISSION:\n"
            f"{request_in.student_defense}\n\n"
            f"Objectively evaluate the student's defense against the counterexample challenge."
        )

        # 3. Structured LLM Generation
        llm_out: DefenseEvaluationOutput = await gateway.generate_structured(
            messages=[LLMMessage(role=MessageRole.USER, content=user_content)],
            response_model=DefenseEvaluationOutput,
            system_prompt=system_prompt,
            tier=ModelTier.REASONING,
            temperature=0.2,
        )

        # 4. Atomic Database Update
        challenge.student_defense = request_in.student_defense
        challenge.robustness_score = llm_out.robustness_score
        challenge.defense_outcome = llm_out.defense_outcome
        challenge.feedback = llm_out.feedback
        session.add(challenge)

        adv_session.status = AdversarialSessionStatus.DEFENDED
        session.add(adv_session)
        await session.commit()
        await session.refresh(challenge)

        return DefenseEvaluationResponse(
            session_id=adv_session.id,
            challenge_id=challenge.id,
            robustness_score=challenge.robustness_score,
            defense_outcome=challenge.defense_outcome,
            valid_points=llm_out.valid_points,
            logical_flaws=llm_out.logical_flaws,
            feedback=challenge.feedback,
            model_synthesis_latex=llm_out.model_synthesis_latex,
            evaluated_at=challenge.created_at,
        )

    @classmethod
    async def list_student_sessions(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> AdversarialSessionListResponse:
        stmt = select(AdversarialSession).where(AdversarialSession.student_id == student_id)
        if exam_template_id:
            stmt = stmt.where(AdversarialSession.exam_template_id == exam_template_id)
        stmt = stmt.order_by(desc(AdversarialSession.created_at)).offset(offset).limit(limit)

        sessions_db = (await session.exec(stmt)).all()
        session_details = []

        for s in sessions_db:
            ch_stmt = select(AdversarialChallenge).where(AdversarialChallenge.session_id == s.id)
            challenges = (await session.exec(ch_stmt)).all()
            summaries = [AdversarialChallengeSummary.model_validate(c) for c in challenges]
            session_details.append(
                AdversarialSessionDetailResponse(
                    id=s.id,
                    student_id=s.student_id,
                    exam_template_id=s.exam_template_id,
                    topic_id=s.topic_id,
                    student_thesis=s.student_thesis,
                    status=s.status,
                    challenges=summaries,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )

        count_stmt = select(AdversarialSession).where(AdversarialSession.student_id == student_id)
        if exam_template_id:
            count_stmt = count_stmt.where(AdversarialSession.exam_template_id == exam_template_id)
        total = len((await session.exec(count_stmt)).all())

        return AdversarialSessionListResponse(sessions=session_details, total=total)

    @classmethod
    async def get_session_detail(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
    ) -> AdversarialSessionDetailResponse:
        s_stmt = select(AdversarialSession).where(
            AdversarialSession.id == session_id,
            AdversarialSession.student_id == student_id,
        )
        adv_session = (await session.exec(s_stmt)).first()
        if not adv_session:
            raise ValueError(f"Adversarial session '{session_id}' not found.")

        ch_stmt = select(AdversarialChallenge).where(AdversarialChallenge.session_id == adv_session.id)
        challenges = (await session.exec(ch_stmt)).all()
        summaries = [AdversarialChallengeSummary.model_validate(c) for c in challenges]

        return AdversarialSessionDetailResponse(
            id=adv_session.id,
            student_id=adv_session.student_id,
            exam_template_id=adv_session.exam_template_id,
            topic_id=adv_session.topic_id,
            student_thesis=adv_session.student_thesis,
            status=adv_session.status,
            challenges=summaries,
            created_at=adv_session.created_at,
            updated_at=adv_session.updated_at,
        )


# ==============================================================================
# 2. Why-You-Are-Wrong Diagnostic Service (PRD Cap 19, FR-019)
# ==============================================================================

class WhyWrongDiagnosticService:
    """
    Decomposes causal flaws and cognitive fallacies in incorrect student answers.
    """

    @classmethod
    async def diagnose_incorrect_answer(
        cls,
        session: AsyncSession,
        student_id: str,
        request_in: WhyWrongDiagnosticRequest,
        llm_gateway: Optional[LLMGateway] = None,
    ) -> WhyWrongDiagnosticResponse:
        gateway = llm_gateway or LLMGateway()

        # 1. Fetch Topic & Learning Objectives
        topic = (await session.exec(select(Topic).where(Topic.id == request_in.topic_id))).first()
        if not topic:
            raise ValueError(f"Topic with ID '{request_in.topic_id}' not found.")

        los = (await session.exec(select(LearningObjective).where(LearningObjective.topic_id == topic.id))).all()
        los_data = [{"code": lo.code, "description": lo.description, "formula_latex": lo.formula_latex} for lo in los]

        # 2. Build Diagnostic Prompt
        system_prompt = build_why_wrong_diagnostic_prompt(
            topic_title=topic.title,
            topic_description=topic.description,
            learning_objectives=los_data,
        )

        user_content = (
            f"### PROBLEM CONTEXT:\n{request_in.question_prompt}\n\n"
            f"### STUDENT SELECTION (INCORRECT):\n"
            f"Selected Option Key: {request_in.selected_option_key or 'N/A'}\n"
            f"Selected Text: {request_in.selected_answer_text}\n\n"
            f"### CORRECT ANSWER CONTEXT:\n{request_in.correct_answer_text or 'Derive standard correct solution'}\n\n"
            f"Perform a complete causal fallacy diagnosis, explaining why this option fails and what recognition rule to use."
        )

        # 3. Structured LLM Generation
        llm_out: WhyWrongDiagnosticOutput = await gateway.generate_structured(
            messages=[LLMMessage(role=MessageRole.USER, content=user_content)],
            response_model=WhyWrongDiagnosticOutput,
            system_prompt=system_prompt,
            tier=ModelTier.REASONING,
            temperature=0.2,
        )

        # 4. Atomic Database Persistence
        diagnostic = WhyWrongDiagnostic(
            student_id=student_id,
            question_id=request_in.question_id,
            topic_id=topic.id,
            selected_option_key=request_in.selected_option_key,
            selected_answer_text=request_in.selected_answer_text,
            fallacy_category=llm_out.fallacy_category,
            why_incorrect_explanation=llm_out.why_incorrect_explanation,
            mental_trap_description=llm_out.mental_trap_description,
            recognition_rule=llm_out.recognition_rule,
            repair_action_summary=llm_out.repair_action_summary,
        )
        session.add(diagnostic)
        await session.commit()
        await session.refresh(diagnostic)

        return WhyWrongDiagnosticResponse(
            id=diagnostic.id,
            topic_id=diagnostic.topic_id,
            question_id=diagnostic.question_id,
            selected_option_key=diagnostic.selected_option_key,
            selected_answer_text=diagnostic.selected_answer_text,
            fallacy_category=diagnostic.fallacy_category,
            why_incorrect_explanation=diagnostic.why_incorrect_explanation,
            mental_trap_description=diagnostic.mental_trap_description,
            recognition_rule=diagnostic.recognition_rule,
            repair_action_summary=diagnostic.repair_action_summary,
            correct_derivation_latex=llm_out.correct_derivation_latex,
            created_at=diagnostic.created_at,
        )

    @classmethod
    async def list_student_diagnostics(
        cls,
        session: AsyncSession,
        student_id: str,
        topic_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[WhyWrongDiagnosticResponse]:
        stmt = select(WhyWrongDiagnostic).where(WhyWrongDiagnostic.student_id == student_id)
        if topic_id:
            stmt = stmt.where(WhyWrongDiagnostic.topic_id == topic_id)
        stmt = stmt.order_by(desc(WhyWrongDiagnostic.created_at)).offset(offset).limit(limit)

        results = (await session.exec(stmt)).all()
        return [WhyWrongDiagnosticResponse.model_validate(r) for r in results]
