from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.dependencies import require_role
from backend.app.auth.models import User, UserRole
from backend.app.core.database import get_db
from backend.app.questions.models import (
    DifficultyLevel,
    QuestionType,
    ValidationStatus,
)
from backend.app.questions.schemas import (
    GeneratedQuestionBatchResponse,
    QuestionCreate,
    QuestionDetailResponse,
    QuestionGenerateRequest,
    QuestionListResponse,
    QuestionUpdate,
)
from backend.app.questions.service import QuestionBankService


router = APIRouter(prefix="/questions", tags=["Question Bank & Item Lab"])


@router.get(
    "",
    response_model=QuestionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List question items with curriculum and psychometric filters",
)
async def list_questions(
    exam_template_id: Optional[str] = Query(None, description="Filter by exam template ID"),
    topic_id: Optional[str] = Query(None, description="Filter by topic ID"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by question format"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty level"),
    validation_status: Optional[ValidationStatus] = Query(None, description="Filter by validation status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> QuestionListResponse:
    """
    Returns a paginated list of question items with child options and rubric details.
    """
    questions, total = await QuestionBankService.list_questions(
        session=session,
        exam_template_id=exam_template_id,
        topic_id=topic_id,
        question_type=question_type,
        difficulty=difficulty,
        validation_status=validation_status,
        limit=limit,
        offset=offset,
    )
    return QuestionListResponse(
        total=total,
        questions=[QuestionDetailResponse.model_validate(q) for q in questions],
    )


@router.get(
    "/{question_id}",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get question detail with options and rubric items",
)
async def get_question(
    question_id: str,
    session: AsyncSession = Depends(get_db),
) -> QuestionDetailResponse:
    """
    Retrieves full question metadata, choices with distractor rationales, and analytical scoring rubric.
    """
    question = await QuestionBankService.get_question(session, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found",
        )
    return QuestionDetailResponse.model_validate(question)


@router.post(
    "",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new question item with options and rubric (Instructor/Admin only)",
)
async def create_question(
    question_in: QuestionCreate,
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
    session: AsyncSession = Depends(get_db),
) -> QuestionDetailResponse:
    """
    Creates a new multi-type question item in the question bank.
    """
    question = await QuestionBankService.create_question(
        session=session,
        question_in=question_in,
        author_id=current_user.id,
    )
    return QuestionDetailResponse.model_validate(question)


@router.put(
    "/{question_id}",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update question metadata or validation status (Instructor/Admin only)",
    dependencies=[Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
async def update_question(
    question_id: str,
    update_in: QuestionUpdate,
    session: AsyncSession = Depends(get_db),
) -> QuestionDetailResponse:
    """
    Updates prompt, difficulty, Bloom level, or validation status of a question.
    """
    question = await QuestionBankService.update_question(
        session=session,
        question_id=question_id,
        update_in=update_in,
    )
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found",
        )
    return QuestionDetailResponse.model_validate(question)


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question item and cascade delete its options (Instructor/Admin only)",
    dependencies=[Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
async def delete_question(
    question_id: str,
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently deletes a question from the question bank.
    """
    deleted = await QuestionBankService.delete_question(session, question_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found",
        )


# ==============================================================================
# Dynamic Item Generation Endpoint (Task 4.2)
# ==============================================================================

@router.post(
    "/generate",
    response_model=GeneratedQuestionBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate curriculum-grounded questions with distractors using LLM (Instructor/Admin only)",
)
async def generate_questions(
    request: QuestionGenerateRequest,
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
    session: AsyncSession = Depends(get_db),
) -> GeneratedQuestionBatchResponse:
    """
    Synthesizes curriculum-grounded STEM questions using the LLM Gateway,
    steered by Bloom's Taxonomy, with diagnostic distractor rationales and KaTeX formatting.
    All generated items are automatically staged in PENDING_VALIDATION.
    """
    from backend.app.questions.generator import QuestionGeneratorService
    return await QuestionGeneratorService.generate_questions(
        session=session,
        request=request,
        author_id=current_user.id,
    )

