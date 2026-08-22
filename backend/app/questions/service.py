from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.questions.models import (
    DifficultyLevel,
    Question,
    QuestionOption,
    QuestionRubricItem,
    QuestionType,
    ValidationStatus,
)
from backend.app.questions.schemas import QuestionCreate, QuestionUpdate


class QuestionBankService:
    """
    CRUD and query orchestration service for Question Items, Options, and Rubrics (PRD §5.4, §15, FR-004, FR-015).
    """

    @classmethod
    async def create_question(
        cls,
        session: AsyncSession,
        question_in: QuestionCreate,
        author_id: Optional[str] = None,
    ) -> Question:
        """
        Atomically creates a Question, its Options, and Rubric items in a single transaction.
        """
        # 1. Create main Question record
        question = Question(
            exam_template_id=question_in.exam_template_id,
            topic_id=question_in.topic_id,
            learning_objective_id=question_in.learning_objective_id,
            question_type=question_in.question_type,
            difficulty=question_in.difficulty,
            bloom_level=question_in.bloom_level,
            validation_status=question_in.validation_status,
            prompt=question_in.prompt,
            hint=question_in.hint,
            explanation=question_in.explanation,
            estimated_time_seconds=question_in.estimated_time_seconds,
            points=question_in.points,
            is_generated_by_ai=question_in.is_generated_by_ai,
            created_by_user_id=author_id,
        )
        session.add(question)
        await session.flush()

        # 2. Add Options
        for opt_in in question_in.options:
            opt = QuestionOption(
                question_id=question.id,
                option_key=opt_in.option_key,
                content=opt_in.content,
                is_correct=opt_in.is_correct,
                distractor_rationale=opt_in.distractor_rationale,
                order=opt_in.order,
            )
            session.add(opt)

        # 3. Add Rubric Items
        for rub_in in question_in.rubric_items:
            rub = QuestionRubricItem(
                question_id=question.id,
                criterion=rub_in.criterion,
                points=rub_in.points,
                order=rub_in.order,
            )
            session.add(rub)

        await session.flush()
        await session.refresh(question)
        return question

    @classmethod
    async def get_question(
        cls,
        session: AsyncSession,
        question_id: str,
    ) -> Optional[Question]:
        """
        Retrieves a question with options and rubrics eagerly loaded.
        """
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options), selectinload(Question.rubric_items))
        )
        res = await session.exec(stmt)
        return res.first()

    @classmethod
    async def list_questions(
        cls,
        session: AsyncSession,
        exam_template_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        question_type: Optional[QuestionType] = None,
        difficulty: Optional[DifficultyLevel] = None,
        validation_status: Optional[ValidationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Question], int]:
        """
        Lists questions matching filters with eager-loaded child collections and total count.
        """
        stmt = select(Question).options(selectinload(Question.options), selectinload(Question.rubric_items))

        if exam_template_id:
            stmt = stmt.where(Question.exam_template_id == exam_template_id)
        if topic_id:
            stmt = stmt.where(Question.topic_id == topic_id)
        if question_type:
            stmt = stmt.where(Question.question_type == question_type)
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)
        if validation_status:
            stmt = stmt.where(Question.validation_status == validation_status)

        # Total count query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_res = await session.exec(count_stmt)
        total = count_res.one()

        # Paginated query
        stmt = stmt.order_by(Question.created_at.desc()).offset(offset).limit(limit)
        results = await session.exec(stmt)
        return list(results.all()), total

    @classmethod
    async def update_question(
        cls,
        session: AsyncSession,
        question_id: str,
        update_in: QuestionUpdate,
    ) -> Optional[Question]:
        """
        Updates an existing question record.
        """
        question = await cls.get_question(session, question_id)
        if not question:
            return None

        update_dict = update_in.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(question, key, val)

        question.updated_at = datetime.now(timezone.utc)
        session.add(question)
        await session.flush()
        await session.refresh(question)
        return question

    @classmethod
    async def delete_question(
        cls,
        session: AsyncSession,
        question_id: str,
    ) -> bool:
        """
        Permanently deletes a question and cascades to its options and rubrics.
        """
        question = await cls.get_question(session, question_id)
        if not question:
            return False

        await session.delete(question)
        await session.flush()
        return True
