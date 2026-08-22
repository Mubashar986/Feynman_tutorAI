import logging
from typing import List, Optional, Tuple
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.llm import LLMGateway
from backend.app.questions.models import (
    BloomTaxonomy,
    DifficultyLevel,
    QuestionType,
    ValidationStatus,
)
from backend.app.questions.schemas import (
    GeneratedQuestionBatchResponse,
    GeneratedQuestionBatchSchema,
    QuestionCreate,
    QuestionDetailResponse,
    QuestionGenerateRequest,
    QuestionOptionCreate,
    QuestionRubricItemCreate,
)
from backend.app.questions.service import QuestionBankService
from backend.app.rag.retrieval import GroundedRetrievalService

logger = logging.getLogger("adaptive_exam_platform.questions.generator")


class QuestionGeneratorService:
    """
    RAG-grounded automated item and distractor generation service (PRD §5.4, §15, FR-004, FR-010).
    Enforces Bloom taxonomy steering, diagnostic distractor rationales, and validation quarantine.
    """

    @classmethod
    def _build_prompts(
        cls,
        request: QuestionGenerateRequest,
        grounded_context: str,
    ) -> Tuple[str, str]:
        """
        Builds pedagogical system and user prompts with domain constraints and KaTeX rules.
        """
        system_prompt = (
            "You are a Senior Standardized STEM Exam Author and Psychometrician.\n"
            "Your task is to generate rigorous, curriculum-aligned exam questions with step-by-step derivations "
            "and diagnostic distractor rationales for incorrect options.\n\n"
            "RULES:\n"
            "1. Ground all questions strictly in the provided syllabus and textbook material if available.\n"
            "2. Mathematical and scientific formulas MUST use standard KaTeX syntax ($...$ for inline, $$...$$ for display).\n"
            "3. For every multiple-choice option where `is_correct=False`, you MUST provide a detailed `distractor_rationale` "
            "explaining the specific cognitive misconception or computational error that leads to that wrong answer.\n"
            "4. For single-choice MCQ (`mcq_single`), provide exactly 4 options (A, B, C, D) with EXACTLY ONE `is_correct=True`.\n"
            "5. Provide an exhaustive, step-by-step derivation in `explanation`.\n"
            "6. Output must strictly conform to the requested JSON schema."
        )

        user_prompt_lines = [
            f"Please generate {request.count} question(s) with the following specifications:",
            f"- Question Type: {request.question_type.value}",
            f"- Difficulty Level: {request.difficulty.value}",
            f"- Bloom's Taxonomy Cognitive Level: {request.bloom_level.value}",
        ]

        if request.custom_prompt_guidance:
            user_prompt_lines.append(f"- Custom Author Instructions: {request.custom_prompt_guidance}")

        if grounded_context:
            user_prompt_lines.append("\n" + grounded_context)
        else:
            user_prompt_lines.append("\n(No specific textbook chunks found for this topic. Generate from core syllabus fundamentals.)")

        user_prompt = "\n".join(user_prompt_lines)
        return system_prompt, user_prompt

    @classmethod
    async def generate_questions(
        cls,
        session: AsyncSession,
        request: QuestionGenerateRequest,
        author_id: Optional[str] = None,
    ) -> GeneratedQuestionBatchResponse:
        """
        Executes the grounded dynamic item generation pipeline and persists drafts in PENDING_VALIDATION.
        """
        # 1. Grounded Context Retrieval (PRD Constraint #5)
        grounded_resp = await GroundedRetrievalService.retrieve_grounded_context(
            query=f"Key definitions formulas theorems for topic {request.topic_id}",
            exam_template_id=request.exam_template_id,
            topic_id=request.topic_id,
            limit=3,
            score_threshold=0.0,
        )


        # 2. Build Prompts
        system_prompt, user_prompt = cls._build_prompts(request, grounded_resp.formatted_context)

        # 3. LLM Gateway Structured Generation (ADR-006, FR-010, Constraint #10)
        gateway = LLMGateway()
        batch_output: GeneratedQuestionBatchSchema = await gateway.generate_structured(
            schema=GeneratedQuestionBatchSchema,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.4,
        )

        # 4. Atomic Relational Staging in PENDING_VALIDATION (Constraint #4)
        persisted_questions: List[QuestionDetailResponse] = []

        for q_raw in batch_output.questions:
            # Construct QuestionCreate DTO
            q_create = QuestionCreate(
                exam_template_id=request.exam_template_id,
                topic_id=request.topic_id,
                learning_objective_id=request.learning_objective_id,
                question_type=request.question_type,
                difficulty=request.difficulty,
                bloom_level=request.bloom_level,
                validation_status=ValidationStatus.PENDING_VALIDATION,
                prompt=q_raw.prompt,
                hint=q_raw.hint,
                explanation=q_raw.explanation,
                estimated_time_seconds=q_raw.estimated_time_seconds,
                points=q_raw.points,
                is_generated_by_ai=True,
                options=[
                    QuestionOptionCreate(
                        option_key=opt.option_key,
                        content=opt.content,
                        is_correct=opt.is_correct,
                        distractor_rationale=opt.distractor_rationale,
                        order=opt.order,
                    )
                    for opt in q_raw.options
                ],
                rubric_items=[
                    QuestionRubricItemCreate(
                        criterion=rub.criterion,
                        points=rub.points,
                        order=rub.order,
                    )
                    for rub in q_raw.rubric_items
                ],
            )

            # Persist to relational database via QuestionBankService
            persisted = await QuestionBankService.create_question(
                session=session,
                question_in=q_create,
                author_id=author_id,
            )
            persisted_questions.append(QuestionDetailResponse.model_validate(persisted))

        return GeneratedQuestionBatchResponse(
            generated_count=len(persisted_questions),
            questions=persisted_questions,
            grounded_sources_used=grounded_resp.total_sources,
        )
