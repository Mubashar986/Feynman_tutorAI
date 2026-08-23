from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.llm import LLMGateway
from backend.app.core.llm.embedding import get_embedding_provider
from backend.app.core.vector import get_vector_store
from backend.app.core.vector.base import VectorPoint
from backend.app.questions.models import (
    Question,
    QuestionType,
    ValidationStatus,
)
from backend.app.questions.schemas import (
    BatchValidationResponse,
    BlindSolveSchema,
    DuplicateMatchInfo,
    QualityAuditSchema,
    QualityScoreBreakdown,
    QuestionUpdate,
    QuestionValidationReportResponse,
)
from backend.app.questions.service import QuestionBankService

logger = logging.getLogger("adaptive_exam_platform.questions.validator")

QUESTION_COLLECTION_NAME = "question_vectors"
DUPLICATE_SIMILARITY_THRESHOLD = 0.90
MIN_VALIDATION_PASS_SCORE = 80


class QuestionValidationService:
    """
    Automated Multi-Gate Question Validation Engine (PRD §5.4, §15, FR-004, FR-015, Constraint #4).
    Enforces blind independent solving, high-dimensional semantic deduplication,
    pedagogical quality audits, and quarantine state promotion.
    """

    @classmethod
    async def _ensure_collection_exists(cls) -> None:
        """Ensures the question vector collection exists in the vector store."""
        vector_store = get_vector_store()
        embedder = get_embedding_provider()
        await vector_store.create_collection(
            collection_name=QUESTION_COLLECTION_NAME,
            dimension=embedder.dimension,
        )

    @classmethod
    async def _run_blind_solver(
        cls,
        question: Question,
    ) -> Tuple[bool, bool, Optional[str], Optional[str], Optional[str]]:
        """
        Gate 1: Independent Blind Solver.
        Solves the question without seeing the declared answer key.
        Returns: (is_solvable, solver_agrees, derived_answer, matched_key, critique)
        """
        # Prepare blind options representation without 'is_correct' indicators
        options_text = ""
        correct_option_key = None
        if question.options:
            opt_lines = []
            for opt in question.options:
                opt_lines.append(f"Option {opt.option_key}: {opt.content}")
                if opt.is_correct:
                    correct_option_key = opt.option_key
            options_text = "\n" + "\n".join(opt_lines)

        system_prompt = (
            "You are a Senior Standardized STEM Exam Chief Examiner and Blind Problem Solver.\n"
            "Your task is to independently solve the given question from first principles, verify its solvability, "
            "and determine the correct answer without any prior assumptions.\n\n"
            "RULES:\n"
            "1. Derive the solution step by step using rigorous mathematical and scientific principles.\n"
            "2. If options are provided, identify which option matches your derived answer.\n"
            "3. If the question is mathematically incomplete, contradictory, or unsolvable, set `is_solvable=False` "
            "and provide a detailed critique.\n"
            "4. Output strictly according to the requested JSON schema."
        )

        user_prompt = (
            f"Question Type: {question.question_type.value}\n"
            f"Difficulty: {question.difficulty.value}\n"
            f"Bloom Level: {question.bloom_level.value}\n\n"
            f"Question Prompt:\n{question.prompt}\n"
            f"{options_text}\n\n"
            "Please solve this independently and state your derived answer and matched option key."
        )

        gateway = LLMGateway()
        result: BlindSolveSchema = await gateway.generate_structured(
            schema=BlindSolveSchema,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Low temperature for rigorous deterministic solving
        )

        if not result.is_solvable:
            return False, False, result.derived_answer, result.matched_option_key, result.critique

        # Check agreement against ground truth
        solver_agrees = False
        if question.question_type == QuestionType.MCQ_SINGLE:
            if result.matched_option_key and correct_option_key:
                solver_agrees = (result.matched_option_key.strip().upper() == correct_option_key.strip().upper())
            else:
                # Fallback: check if derived answer contains or matches correct option content
                for opt in question.options:
                    if opt.is_correct and (opt.content in result.derived_answer or result.derived_answer in opt.content):
                        solver_agrees = True
                        break
        elif question.question_type == QuestionType.MCQ_MULTI:
            correct_keys = {opt.option_key.strip().upper() for opt in question.options if opt.is_correct}
            matched_key = result.matched_option_key.strip().upper() if result.matched_option_key else ""
            solver_agrees = (matched_key in correct_keys) or (result.confidence_score >= 0.8)
        else:
            # Free response / numerical / derivation
            solver_agrees = result.is_solvable and (result.confidence_score >= 0.75)

        return (
            result.is_solvable,
            solver_agrees,
            result.derived_answer,
            result.matched_option_key,
            result.critique,
        )

    @classmethod
    async def _check_duplicates(
        cls,
        question: Question,
    ) -> Tuple[float, List[DuplicateMatchInfo]]:
        """
        Gate 2: High-Dimensional Semantic Deduplication.
        Embeds the question prompt and queries 'question_vectors' for near-duplicates (cosine > 0.90).
        """
        await cls._ensure_collection_exists()

        embedder = get_embedding_provider()
        prompt_vector = await embedder.embed_text(question.prompt)

        vector_store = get_vector_store()
        filter_conds: Dict[str, Any] = {}
        if question.exam_template_id:
            filter_conds["exam_template_id"] = question.exam_template_id
        if question.topic_id:
            filter_conds["topic_id"] = question.topic_id

        search_results = await vector_store.search(
            collection_name=QUESTION_COLLECTION_NAME,
            query_vector=prompt_vector,
            limit=5,
            score_threshold=0.0,
            filter_conditions=filter_conds if filter_conds else None,
        )

        matches: List[DuplicateMatchInfo] = []
        max_score = 0.0

        for res in search_results:
            # Ignore self if already indexed
            if res.id == question.id or res.payload.get("question_id") == question.id:
                continue

            score = float(res.score)
            if score > max_score:
                max_score = score

            if score >= 0.60:
                snippet = res.payload.get("prompt", "")
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
                matches.append(
                    DuplicateMatchInfo(
                        matched_question_id=res.payload.get("question_id", res.id),
                        similarity_score=round(score, 4),
                        matched_prompt_snippet=snippet,
                    )
                )

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return max_score, matches

    @classmethod
    async def _audit_pedagogical_quality(
        cls,
        question: Question,
    ) -> Tuple[QualityScoreBreakdown, str, List[str]]:
        """
        Gate 3: Pedagogical Quality Audit.
        Evaluates KaTeX formatting, clarity, distractor diagnostic depth, and derivation thoroughness.
        """
        options_detail = []
        if question.options:
            for opt in question.options:
                status_str = "CORRECT" if opt.is_correct else "INCORRECT"
                distractor_info = f" | Distractor Rationale: {opt.distractor_rationale}" if opt.distractor_rationale else ""
                options_detail.append(f"- Option {opt.option_key} [{status_str}]: {opt.content}{distractor_info}")

        rubric_detail = []
        if question.rubric_items:
            for rub in question.rubric_items:
                rubric_detail.append(f"- Criterion ({rub.points} pts): {rub.criterion}")

        dossier = (
            f"Prompt:\n{question.prompt}\n\n"
            f"Question Type: {question.question_type.value}\n"
            f"Difficulty: {question.difficulty.value}\n"
            f"Bloom Level: {question.bloom_level.value}\n"
            f"Explanation:\n{question.explanation}\n"
            f"Hint: {question.hint or 'None'}\n\n"
            f"Options:\n" + ("\n".join(options_detail) if options_detail else "None") + "\n\n"
            f"Rubrics:\n" + ("\n".join(rubric_detail) if rubric_detail else "None")
        )

        system_prompt = (
            "You are a Senior Psychometrician and Curriculum Quality Auditor.\n"
            "Audit the given exam question dossier across 4 orthogonal dimensions (0 to 25 points each):\n"
            "1. `katex_score` (0-25): Valid LaTeX math syntax, proper $...$ and $$...$$ delimiters, no broken tokens.\n"
            "2. `clarity_score` (0-25): Unambiguous stem, appropriate cognitive load, aligned to declared Bloom level.\n"
            "3. `distractor_score` (0-25): Plausible wrong options with diagnostic misconception rationales.\n"
            "4. `derivation_score` (0-25): Thorough, step-by-step solution derivation in explanation.\n"
            "Output strictly according to the requested JSON schema."
        )

        user_prompt = f"Please audit the following question item:\n\n{dossier}"

        gateway = LLMGateway()
        audit_result: QualityAuditSchema = await gateway.generate_structured(
            schema=QualityAuditSchema,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
        )

        total = (
            audit_result.katex_score
            + audit_result.clarity_score
            + audit_result.distractor_score
            + audit_result.derivation_score
        )

        breakdown = QualityScoreBreakdown(
            katex_score=audit_result.katex_score,
            clarity_score=audit_result.clarity_score,
            distractor_score=audit_result.distractor_score,
            derivation_score=audit_result.derivation_score,
            total_score=total,
        )

        return breakdown, audit_result.overall_critique, audit_result.suggested_improvements

    @classmethod
    async def _upsert_question_vector(cls, question: Question) -> None:
        """Indexes a validated question into 'question_vectors' for retrieval and deduplication."""
        await cls._ensure_collection_exists()
        embedder = get_embedding_provider()
        prompt_vector = await embedder.embed_text(question.prompt)

        vector_store = get_vector_store()
        point = VectorPoint(
            id=question.id,
            vector=prompt_vector,
            payload={
                "question_id": question.id,
                "exam_template_id": question.exam_template_id,
                "topic_id": question.topic_id,
                "prompt": question.prompt,
                "difficulty": question.difficulty.value,
                "question_type": question.question_type.value,
            },
        )
        await vector_store.upsert_points(QUESTION_COLLECTION_NAME, [point])

    @classmethod
    async def validate_question(
        cls,
        session: AsyncSession,
        question_id: str,
    ) -> QuestionValidationReportResponse:
        """
        Executes the full 3-Gate Validation Pipeline on a single Question item (PRD §5.4, §15, FR-015).
        """
        question = await QuestionBankService.get_question(session, question_id)
        if not question:
            raise ValueError(f"Question with ID '{question_id}' not found")

        # 1. Gate 1: Blind Solving
        is_solvable, solver_agrees, derived_ans, matched_key, solver_critique = await cls._run_blind_solver(question)

        # 2. Gate 2: High-Dimensional Semantic Deduplication
        max_sim, dup_matches = await cls._check_duplicates(question)

        # 3. Gate 3: Pedagogical Quality Audit
        scores, overall_critique, suggested_improvements = await cls._audit_pedagogical_quality(question)

        # 4. Multi-Gate State Decision Logic
        # - Solved & Agreed & High Quality (>=80) & No Duplicates (<0.90) -> VALIDATED
        # - High similarity (>=0.90) OR Borderline Quality (60-79) -> FLAGGED
        # - Unsolvable OR Solver Disagrees OR Low Quality (<60) -> REJECTED
        is_duplicate = max_sim >= DUPLICATE_SIMILARITY_THRESHOLD

        if not is_solvable or not solver_agrees or scores.total_score < 60:
            final_status = ValidationStatus.REJECTED
        elif is_duplicate or scores.total_score < MIN_VALIDATION_PASS_SCORE:
            final_status = ValidationStatus.FLAGGED
        else:
            final_status = ValidationStatus.VALIDATED
            # Index into question_vectors on successful validation
            await cls._upsert_question_vector(question)

        # 5. Persist state update
        await QuestionBankService.update_question(
            session=session,
            question_id=question.id,
            update_in=QuestionUpdate(validation_status=final_status),
        )

        return QuestionValidationReportResponse(
            question_id=question.id,
            validation_status=final_status,
            is_solvable=is_solvable,
            solver_agrees=solver_agrees,
            solver_derived_answer=derived_ans,
            solver_critique=solver_critique,
            max_similarity_score=round(max_sim, 4),
            duplicate_matches=dup_matches,
            quality_scores=scores,
            critique=overall_critique,
            suggested_improvements=suggested_improvements,
            validated_at=datetime.now(timezone.utc),
        )

    @classmethod
    async def batch_validate(
        cls,
        session: AsyncSession,
        topic_id: Optional[str] = None,
        exam_template_id: Optional[str] = None,
        limit: int = 20,
    ) -> BatchValidationResponse:
        """
        Runs validation across a batch of questions currently in PENDING_VALIDATION.
        """
        stmt = select(Question).where(Question.validation_status == ValidationStatus.PENDING_VALIDATION)
        if topic_id:
            stmt = stmt.where(Question.topic_id == topic_id)
        if exam_template_id:
            stmt = stmt.where(Question.exam_template_id == exam_template_id)

        stmt = stmt.limit(limit)
        results = await session.exec(stmt)
        pending_questions = list(results.all())

        reports: List[QuestionValidationReportResponse] = []
        validated_count = 0
        rejected_count = 0
        flagged_count = 0

        for q in pending_questions:
            report = await cls.validate_question(session, q.id)
            reports.append(report)
            if report.validation_status == ValidationStatus.VALIDATED:
                validated_count += 1
            elif report.validation_status == ValidationStatus.REJECTED:
                rejected_count += 1
            elif report.validation_status == ValidationStatus.FLAGGED:
                flagged_count += 1

        return BatchValidationResponse(
            total_processed=len(reports),
            validated_count=validated_count,
            rejected_count=rejected_count,
            flagged_count=flagged_count,
            reports=reports,
        )
