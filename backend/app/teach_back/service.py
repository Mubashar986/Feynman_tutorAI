import json
import logging
from typing import Any, Dict, List, Optional
from sqlmodel import col, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.llm import LLMGateway, LLMMessage, MessageRole, ModelTier
from backend.app.curriculum.models import LearningObjective, Topic, TopicPrerequisite
from backend.app.rag.retrieval import GroundedRetrievalService
from backend.app.teach_back.models import (
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
    RubricCriterionScore,
    TeachBackEvaluateRequest,
    TeachBackEvaluationResponse,
    TeachBackLLMEvaluationOutput,
    TeachBackSessionListResponse,
    TeachBackSessionResponse,
    TopicRubricResponse,
)

logger = logging.getLogger("adaptive_exam_platform.teach_back.service")


class TeachBackService:
    """
    Teach-Back Mode & Rubric Evaluator Orchestrator (PRD Cap 17, §14.4, FR-017).
    Enforces student isolation, grounded syllabus rubrics, and Pydantic V2 structured output validation.
    """

    @classmethod
    async def evaluate_explanation(
        cls,
        session: AsyncSession,
        student_id: str,
        request_in: TeachBackEvaluateRequest,
        llm_gateway: Optional[LLMGateway] = None,
    ) -> TeachBackEvaluationResponse:
        """
        Evaluates a student's Teach-Back explanation against curriculum rubrics using LLMGateway.
        """
        gateway = llm_gateway or LLMGateway()

        # 1. Fetch Target Topic
        topic_stmt = select(Topic).where(Topic.id == request_in.topic_id)
        topic_result = await session.exec(topic_stmt)
        topic = topic_result.first()
        if not topic:
            raise ValueError(f"Topic with ID '{request_in.topic_id}' not found.")

        # 2. Fetch Topic Learning Objectives
        lo_stmt = select(LearningObjective).where(LearningObjective.topic_id == topic.id)
        lo_res = await session.exec(lo_stmt)
        objectives = lo_res.all()
        objectives_data = [
            {
                "id": lo.id,
                "code": lo.code,
                "description": lo.description,
                "formula_latex": lo.formula_latex,
                "bloom_level": lo.bloom_level.value if hasattr(lo.bloom_level, "value") else str(lo.bloom_level),
            }
            for lo in objectives
        ]

        # 3. Fetch Prerequisite Topics
        prereq_link_stmt = select(TopicPrerequisite).where(TopicPrerequisite.topic_id == topic.id)
        prereq_link_res = await session.exec(prereq_link_stmt)
        prereq_links = prereq_link_res.all()
        prereq_topic_ids = [link.prerequisite_topic_id for link in prereq_links]

        prerequisites_data = []
        if prereq_topic_ids:
            prereq_topics_stmt = select(Topic).where(col(Topic.id).in_(prereq_topic_ids))
            prereq_topics_res = await session.exec(prereq_topics_stmt)
            prerequisites_data = [
                {
                    "id": pt.id,
                    "title": pt.title,
                    "description": pt.description,
                }
                for pt in prereq_topics_res.all()
            ]

        # 4. Optional Grounded Retrieval (RAG)
        grounded_chunks = []
        try:
            citations = await GroundedRetrievalService.search_curriculum_sources(
                query=f"{topic.title}: {request_in.explanation[:200]}",
                exam_template_id=request_in.exam_template_id,
                topic_id=topic.id,
                limit=2,
            )
            grounded_chunks = [
                {
                    "source_title": c.source_title,
                    "content": c.snippet,
                }
                for c in citations
            ]
        except Exception as rag_err:
            logger.debug(f"RAG retrieval skipped or empty for Teach-Back: {rag_err}")

        # 5. Build Dynamic Rubric Prompt
        system_prompt = build_rubric_system_prompt(
            topic_title=topic.title,
            topic_description=topic.description,
            learning_objectives=objectives_data,
            prerequisites=prerequisites_data,
            audience_level=request_in.audience_level,
            grounded_chunks=grounded_chunks,
        )

        user_content = (
            f"### STUDENT CONCEPT EXPLANATION SUBMISSION:\n"
            f"**Concept Under Explanation:** {request_in.concept_title or topic.title}\n"
            f"**Target Audience:** {request_in.audience_level.value}\n\n"
            f"**Explanation Body:**\n{request_in.explanation}\n"
        )

        # 6. Execute Multi-Provider Structured LLM Evaluation
        llm_eval: TeachBackLLMEvaluationOutput = await gateway.generate_structured(
            messages=[LLMMessage(role=MessageRole.USER, content=user_content)],
            response_model=TeachBackLLMEvaluationOutput,
            system_prompt=system_prompt,
            tier=ModelTier.REASONING,
            temperature=0.2,
        )

        # 7. Calculate Composite Score & Classify Mastery
        overall_score = calculate_overall_score(llm_eval.criteria_scores)
        assessment_level = determine_mastery_level(overall_score)

        # 8. Atomic Database Persistence (ACID Transaction)
        tb_session = TeachBackSession(
            student_id=student_id,
            exam_template_id=request_in.exam_template_id,
            topic_id=topic.id,
            concept_title=request_in.concept_title or topic.title,
            audience_level=request_in.audience_level,
        )
        session.add(tb_session)
        await session.flush()  # obtain tb_session.id

        tb_evaluation = TeachBackEvaluation(
            session_id=tb_session.id,
            student_id=student_id,
            student_explanation=request_in.explanation,
            overall_score=overall_score,
            assessment_level=assessment_level,
            criteria_scores_json=json.dumps([c.model_dump() for c in llm_eval.criteria_scores]),
            strengths_json=json.dumps(llm_eval.strengths),
            misconceptions_json=json.dumps(llm_eval.misconceptions),
            missing_elements_json=json.dumps(llm_eval.missing_elements),
            prerequisite_gaps_json=json.dumps([p.model_dump() for p in llm_eval.prerequisite_gaps]),
            pedagogical_feedback=llm_eval.pedagogical_feedback,
            model_correction_latex=llm_eval.model_correction_latex,
        )
        session.add(tb_evaluation)
        await session.commit()
        await session.refresh(tb_session)
        await session.refresh(tb_evaluation)

        logger.info(
            f"Completed Teach-Back evaluation for student {student_id[:8]} on topic {topic.id[:8]}. "
            f"Score: {overall_score} ({assessment_level.value})"
        )

        return TeachBackEvaluationResponse.from_db_models(tb_session, tb_evaluation)

    @classmethod
    async def get_topic_rubric(
        cls,
        session: AsyncSession,
        topic_id: str,
    ) -> TopicRubricResponse:
        """
        Retrieves the curriculum rubric expectations, learning objectives, and prerequisites for a topic.
        """
        topic_stmt = select(Topic).where(Topic.id == topic_id)
        topic_res = await session.exec(topic_stmt)
        topic = topic_res.first()
        if not topic:
            raise ValueError(f"Topic with ID '{topic_id}' not found.")

        # Learning objectives
        lo_stmt = select(LearningObjective).where(LearningObjective.topic_id == topic.id)
        lo_res = await session.exec(lo_stmt)
        objectives = [
            {
                "id": lo.id,
                "code": lo.code,
                "description": lo.description,
                "formula_latex": lo.formula_latex,
            }
            for lo in lo_res.all()
        ]

        # Prerequisites
        prereq_stmt = select(TopicPrerequisite).where(TopicPrerequisite.topic_id == topic.id)
        prereq_links = (await session.exec(prereq_stmt)).all()
        prereq_ids = [l.prerequisite_topic_id for l in prereq_links]

        prereqs = []
        if prereq_ids:
            pts = (await session.exec(select(Topic).where(col(Topic.id).in_(prereq_ids)))).all()
            prereqs = [{"id": pt.id, "title": pt.title, "description": pt.description} for pt in pts]

        return TopicRubricResponse(
            topic_id=topic.id,
            topic_title=topic.title,
            description=topic.description,
            learning_objectives=objectives,
            prerequisites=prereqs,
            rubric_dimensions=DEFAULT_RUBRIC_DIMENSIONS,
        )

    @classmethod
    async def list_student_sessions(
        cls,
        session: AsyncSession,
        student_id: str,
        exam_template_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TeachBackSessionListResponse:
        """
        Lists past Teach-Back sessions for the authenticated student.
        """
        stmt = select(TeachBackSession).where(TeachBackSession.student_id == student_id)
        if exam_template_id:
            stmt = stmt.where(TeachBackSession.exam_template_id == exam_template_id)

        stmt = stmt.order_by(desc(TeachBackSession.created_at)).offset(offset).limit(limit)
        results = (await session.exec(stmt)).all()

        session_responses: List[TeachBackSessionResponse] = []
        for s in results:
            # Fetch latest evaluation
            eval_stmt = (
                select(TeachBackEvaluation)
                .where(TeachBackEvaluation.session_id == s.id)
                .order_by(desc(TeachBackEvaluation.created_at))
                .limit(1)
            )
            eval_record = (await session.exec(eval_stmt)).first()

            session_responses.append(
                TeachBackSessionResponse(
                    id=s.id,
                    student_id=s.student_id,
                    exam_template_id=s.exam_template_id,
                    topic_id=s.topic_id,
                    concept_title=s.concept_title,
                    audience_level=s.audience_level,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    latest_score=eval_record.overall_score if eval_record else None,
                    latest_assessment_level=eval_record.assessment_level if eval_record else None,
                )
            )

        # Count total
        count_stmt = select(TeachBackSession).where(TeachBackSession.student_id == student_id)
        if exam_template_id:
            count_stmt = count_stmt.where(TeachBackSession.exam_template_id == exam_template_id)
        all_sessions = (await session.exec(count_stmt)).all()

        return TeachBackSessionListResponse(
            sessions=session_responses,
            total=len(all_sessions),
        )

    @classmethod
    async def get_session_evaluation(
        cls,
        session: AsyncSession,
        student_id: str,
        session_id: str,
    ) -> TeachBackEvaluationResponse:
        """
        Fetches full evaluation details for a session, enforcing student isolation.
        """
        s_stmt = select(TeachBackSession).where(
            TeachBackSession.id == session_id,
            TeachBackSession.student_id == student_id,
        )
        tb_session = (await session.exec(s_stmt)).first()
        if not tb_session:
            raise ValueError(f"Teach-Back session '{session_id}' not found.")

        eval_stmt = (
            select(TeachBackEvaluation)
            .where(TeachBackEvaluation.session_id == session_id)
            .order_by(desc(TeachBackEvaluation.created_at))
            .limit(1)
        )
        eval_record = (await session.exec(eval_stmt)).first()
        if not eval_record:
            raise ValueError(f"Evaluation report for session '{session_id}' not found.")

        return TeachBackEvaluationResponse.from_db_models(tb_session, eval_record)
