from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.database import get_db
from backend.app.auth.dependencies import get_current_user, require_role
from backend.app.auth.models import User, UserRole
from backend.app.rag.schemas import (
    DocumentChunkResponse,
    DocumentResponse,
)
from backend.app.rag.service import DocumentService

router = APIRouter(prefix="/documents", tags=["Vector RAG & Resource Ingestion"])


@router.get(
    "",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all uploaded source documents",
)
async def list_documents(
    exam_template_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
) -> List[DocumentResponse]:
    """
    Returns a list of all processed curriculum source documents, optionally filtered by exam or topic.
    """
    return await DocumentService.list_documents(
        session=session,
        exam_template_id=exam_template_id,
        topic_id=topic_id,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document metadata by ID",
)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Retrieves document ingestion status, token counts, and chunk statistics.
    """
    doc = await DocumentService.get_document(session, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )
    return DocumentResponse.model_validate(doc)


@router.get(
    "/{document_id}/chunks",
    response_model=List[DocumentChunkResponse],
    status_code=status.HTTP_200_OK,
    summary="Get semantic chunks and heading breadcrumbs for a document",
)
async def get_document_chunks(
    document_id: str,
    session: AsyncSession = Depends(get_db),
) -> List[DocumentChunkResponse]:
    """
    Returns the segmented text chunks, heading breadcrumbs, and token metrics generated from the document.
    """
    return await DocumentService.get_document_chunks(session, document_id)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and chunk a source document (Instructor/Admin only)",
)
async def upload_document(
    file: UploadFile = File(...),
    exam_template_id: Optional[str] = Form(None),
    topic_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Uploads a textbook, syllabus guide, or notes file (PDF, Markdown, TXT), validates security,
    segments it into semantic chunks with LaTeX protection, and saves to relational storage.
    """
    document = await DocumentService.process_uploaded_document(
        session=session,
        file=file,
        exam_template_id=exam_template_id,
        topic_id=topic_id,
        uploaded_by_user_id=current_user.id,
        title=title,
    )
    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a source document and its chunks (Instructor/Admin only)",
    dependencies=[Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently deletes a document, removes its raw file from storage, and cascades deletions to all chunks.
    """
    deleted = await DocumentService.delete_document(session, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found",
        )


@router.post(
    "/{document_id}/index",
    status_code=status.HTTP_200_OK,
    summary="Generate embeddings and index document into Qdrant (Instructor/Admin only)",
    dependencies=[Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
async def index_document(
    document_id: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Generates dense embeddings for all document chunks and upserts them into the Qdrant vector index.
    """
    from backend.app.rag.indexer import VectorIndexerService
    chunks_indexed = await VectorIndexerService.index_document(session, document_id)
    return {
        "document_id": document_id,
        "status": "indexed",
        "chunks_indexed": chunks_indexed,
    }


@router.post(
    "/exam-templates/{exam_template_id}/index-all",
    status_code=status.HTTP_200_OK,
    summary="Batch index all documents for an exam template (Instructor/Admin only)",
    dependencies=[Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN]))],
)
async def index_all_exam_documents(
    exam_template_id: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Batch indexes all curriculum documents associated with a specific exam template.
    """
    from backend.app.rag.indexer import VectorIndexerService
    return await VectorIndexerService.index_exam_template(session, exam_template_id)

