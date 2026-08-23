from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.llm import LLMGateway, LLMMessage, MessageRole
from backend.app.errors.models import RepairStatus
from backend.app.errors.service import ErrorBankService
from backend.app.mastery.service import MasteryEngineService
from backend.app.questions.service import QuestionBankService
from backend.app.rag.retrieval import GroundedRetrievalService
from backend.app.tutor.models import (
    HintLevel,
    TutorMessage,
    TutorRole,
    TutorSession,
)
from backend.app.tutor.schemas import (
    SocraticPromptRequest,
    SocraticResponse,
    TutorMessageResponse,
    TutorSessionCreate,
    TutorSessionDetailResponse,
)

logger = logging.getLogger("adaptive_exam_platform.tutor.service")


class SocraticTutorService:
    """
    Socratic AI Tutor Orchestrator with RAG & Pedagogical Guardrails (PRD §14.3, §14.5, FR-008, Cap 4).
    Enforces student state isolation and strict non-leakage pedagogical scaffolding.
    """

    SYSTEM_PROMPT_TEMPLATE = """You are an elite, encouraging, and rigorous Socratic AI Academic Tutor for Cambridge A-Level and University-track students.

### PEDAGOGICAL INVARIANTS (STRICT - MUST NEVER VIOLATE):
1. **NEVER REVEAL THE FINAL ANSWER OR MCQ OPTION LETTER DIRECTLY.**
   - Do NOT say "The answer is 8 m/s^2" or "Option B is correct".
   - Guide the student step-by-step using thought-provoking questions.
2. **SCAFFOLDING LEVEL: {hint_level_name} (Tier {hint_tier})**
   - {hint_level_instruction}
3. **MATHEMATICAL & SCIENTIFIC NOTATION (KaTeX):**
   - Format ALL variables, quantities, and equations using standard KaTeX: inline `$v = u + at$` or block `$$\\int f(x) dx$$`.
4. **STUDENT LEARNING PROFILE & MASTERY:**
   - Topic Mastery: {mastery_probability:.1%} ({mastery_status})
   - {misconception_guidance}
5. **GROUNDED SOURCE CITATIONS:**
   - Base your scientific facts ONLY on the provided grounded curriculum chunks.
   - Attribute textbook concepts naturally without dumping entire raw text blocks.

--- BEGIN GROUNDED CURRICULUM SOURCES ---
{grounded_sources}
--- END GROUNDED CURRICULUM SOURCES ---
{question_context}
"""

    @classmethod
    def _format_hint_instructions(cls, hint_level: HintLevel) -> tuple[str, int, str]:
        if hint_level == HintLevel.CONCEPTUAL:
            return (
                "CONCEPTUAL HINT",
                1,
                "Prompt the student to recall the fundamental physical law, definition, or theorem. Ask what principle connects the given variables.",
            )
        elif hint_level == HintLevel.STRATEGIC:
            return (
                "STRATEGIC HINT",
                2,
                "Suggest the mathematical direction or strategy to approach the problem. Outline the logical path without performing the algebra.",
            )
        elif hint_level == HintLevel.STEP:
            return (
                "STEP HINT",
                3,
                "Guide the immediate next algebraic step. Show the symbolic equation setup with variables identified, and ask the student to substitute values.",
            )
        else:
            return (
                "COMPREHENSIVE EXPLANATION",
                4,
                "Provide a complete, step-by-step pedagogical derivation explaining the physics principles thoroughly.",
            )

    @classmethod
    async def create_session(
        cls,
        session: AsyncSession,
        student_id: str,
        session_in: TutorSessionCreate,
    ) -> TutorSession:
        """
        Initializes a new Socratic conversational session.
        """
        title = session_in.title or f"Socratic Session: Topic {session_in.topic_id[:8]}"
        tutor_session = TutorSession(
            student_id=student_id,
            exam_template_id=session_in.exam_template_id,
            topic_id=session_in.topic_id,
            question_id=session_in.question_id,
            title=title,
            is_active=True,
        )
        session.add(tutor_session)
        await session.flush()
        await session.refresh(tutor_session)
        return tutor_session

    @classmethod
    async def list_sessions(
        cls,
        session: AsyncSession,
        student_id: str,
        topic_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[TutorSession]:
        """
        Retrieves active and past tutor sessions for the authenticated student.
        """
        stmt = (
            select(TutorSession)
            .where(TutorSession.student_id == student_id)
        )
        if topic_id:
            stmt = stmt.where(TutorSession.topic_id == topic_id)
        stmt = stmt.order_by(TutorSession.updated_at.desc()).limit(limit)
        res = await session.exec(stmt)
        return list(res.all())

    @classmethod
    async def get_session_history(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
    ) -> Optional[TutorSessionDetailResponse]:
        """
        Fetches the complete dialogue turn history for a session.
        """
        stmt = select(TutorSession).where(
            TutorSession.id == session_id,
            TutorSession.student_id == student_id,
        )
        res = await session.exec(stmt)
        tutor_sess = res.first()
        if not tutor_sess:
            return None

        msg_stmt = (
            select(TutorMessage)
            .where(TutorMessage.session_id == session_id)
            .order_by(TutorMessage.created_at.asc())
        )
        msg_res = await session.exec(msg_stmt)
        messages = [TutorMessageResponse.from_orm_model(m) for m in msg_res.all()]

        return TutorSessionDetailResponse(
            id=tutor_sess.id,
            student_id=tutor_sess.student_id,
            exam_template_id=tutor_sess.exam_template_id,
            topic_id=tutor_sess.topic_id,
            question_id=tutor_sess.question_id,
            title=tutor_sess.title,
            is_active=tutor_sess.is_active,
            created_at=tutor_sess.created_at,
            updated_at=tutor_sess.updated_at,
            messages=messages,
        )

    @classmethod
    async def send_message(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
        message_in: SocraticPromptRequest,
        mock_llm_response: Optional[str] = None,
    ) -> SocraticResponse:
        """
        Orchestrates multi-turn conversation turn:
        1. Validates session ownership.
        2. Retrieves Grounded RAG chunks.
        3. Injects live mastery probability & active misconceptions.
        4. Invokes LLMGateway with Socratic system prompt.
        5. Persists dialogue turns to database.
        """
        # 1. Validate Session
        stmt = select(TutorSession).where(
            TutorSession.id == session_id,
            TutorSession.student_id == student_id,
        )
        res = await session.exec(stmt)
        tutor_sess = res.first()
        if not tutor_sess:
            raise ValueError(f"Tutor session '{session_id}' not found for current student")

        # 2. Retrieve Grounded Curriculum Chunks (Task 3.3 RAG)
        rag_query = f"{message_in.message}"
        rag_result = await GroundedRetrievalService.retrieve_grounded_context(
            query=rag_query,
            exam_template_id=tutor_sess.exam_template_id,
            topic_id=tutor_sess.topic_id,
            limit=3,
        )
        grounded_sources = rag_result.formatted_context if rag_result.formatted_context else "No specific textbook chunk retrieved."
        citations_data = [c.model_dump() for c in rag_result.citations]

        # 3. Retrieve Student Mastery State (Task 5.1)
        mastery = await MasteryEngineService.get_topic_mastery(
            session=session,
            student_id=student_id,
            topic_id=tutor_sess.topic_id,
        )
        mastery_prob = mastery.mastery_probability if mastery else 0.10
        mastery_status = mastery.status.value if mastery else "novice"

        # 4. Retrieve Active Misconceptions (Task 5.2)
        errors_resp = await ErrorBankService.list_student_errors(
            session=session,
            student_id=student_id,
            topic_id=tutor_sess.topic_id,
            repair_status=RepairStatus.ACTIVE,
            limit=2,
        )
        misconception_guidance = "No active misconceptions recorded for this topic."
        if errors_resp.errors:
            misc_items = [f"- {e.distractor_rationale or e.error_category.value}" for e in errors_resp.errors]
            misconception_guidance = "ACTIVE MISCONCEPTIONS TO ADDRESS SOCRATICALLY:\n" + "\n".join(misc_items)

        # 5. Question Context (if attached)
        question_context = ""
        if tutor_sess.question_id:
            question = await QuestionBankService.get_question(session, tutor_sess.question_id)
            if question:
                question_context = f"\n--- CURRENT QUESTION CONTEXT ---\nPrompt: {question.prompt}\nExplanation: {question.explanation}\n"

        # 6. Build Multi-Turn Conversation History (Sliding Window: last 6 turns)
        history_stmt = (
            select(TutorMessage)
            .where(TutorMessage.session_id == session_id)
            .order_by(TutorMessage.created_at.desc())
            .limit(6)
        )
        history_res = await session.exec(history_stmt)
        recent_messages = list(reversed(list(history_res.all())))

        llm_messages: List[LLMMessage] = []
        hint_name, hint_tier, hint_inst = cls._format_hint_instructions(message_in.hint_level)

        system_prompt = cls.SYSTEM_PROMPT_TEMPLATE.format(
            hint_level_name=hint_name,
            hint_tier=hint_tier,
            hint_level_instruction=hint_inst,
            mastery_probability=mastery_prob,
            mastery_status=mastery_status,
            misconception_guidance=misconception_guidance,
            grounded_sources=grounded_sources,
            question_context=question_context,
        )
        llm_messages.append(LLMMessage(role="system", content=system_prompt))

        for m in recent_messages:
            role_str = "user" if m.role == TutorRole.USER else "assistant"
            llm_messages.append(LLMMessage(role=role_str, content=m.content))

        llm_messages.append(LLMMessage(role="user", content=message_in.message))

        # 7. Generate Response via LLMGateway
        if mock_llm_response:
            assistant_content = mock_llm_response
        else:
            try:
                gateway = LLMGateway()
                llm_resp = await gateway.generate_text(
                    messages=llm_messages,
                    temperature=0.3,
                    max_tokens=600,
                )
                assistant_content = llm_resp.content
            except Exception as e:
                logger.warning(f"LLM generation failed in Socratic Tutor: {e}")
                assistant_content = (
                    "Let's break down this problem systematically! "
                    "First, identify what variables are given and what fundamental equation relates them. "
                    "What formula do you think applies here?"
                )

        # 8. Persist User & Assistant Messages
        user_msg = TutorMessage(
            session_id=session_id,
            role=TutorRole.USER,
            content=message_in.message,
            hint_level=message_in.hint_level,
        )
        session.add(user_msg)

        assistant_msg = TutorMessage(
            session_id=session_id,
            role=TutorRole.ASSISTANT,
            content=assistant_content,
            hint_level=message_in.hint_level,
            citations_json=json.dumps(citations_data),
        )
        session.add(assistant_msg)

        tutor_sess.updated_at = datetime.now(timezone.utc)
        session.add(tutor_sess)
        await session.flush()
        await session.refresh(assistant_msg)

        msg_response = TutorMessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            hint_level=assistant_msg.hint_level,
            citations=citations_data,
            created_at=assistant_msg.created_at,
        )

        return SocraticResponse(
            session_id=session_id,
            topic_id=tutor_sess.topic_id,
            message=msg_response,
            citations=citations_data,
        )
