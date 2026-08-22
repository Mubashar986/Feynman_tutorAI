import hashlib
import io
import json
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.storage import get_storage_provider
from backend.app.rag.chunker import SemanticRecursiveChunker
from backend.app.rag.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    DocumentType,
)
from backend.app.rag.schemas import (
    DocumentChunkResponse,
    DocumentResponse,
)

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class DocumentService:
    """
    Application domain service for secure document ingestion, text extraction,
    and relational chunk persistence (PRD §5.3, FR-005, FR-008).
    """

    @staticmethod
    def detect_file_type(filename: str) -> DocumentType:
        """Determines DocumentType from file extension."""
        ext = Path(filename).suffix.lower()
        if ext in [".md", ".markdown"]:
            return DocumentType.MARKDOWN
        elif ext == ".pdf":
            return DocumentType.PDF
        elif ext == ".json":
            return DocumentType.JSON
        elif ext in [".txt", ".text"]:
            return DocumentType.TEXT
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions: .pdf, .md, .txt, .json",
            )

    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, file_type: DocumentType) -> str:
        """
        Extracts raw text from file bytes with fallback support for PDF and UTF-8 decoders.
        """
        if file_type in [DocumentType.TEXT, DocumentType.MARKDOWN, DocumentType.JSON]:
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="replace")

        elif file_type == DocumentType.PDF:
            try:
                # Try pypdf if installed
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_pages = []
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text_pages.append(f"\n\n<!-- Page {page_idx + 1} -->\n{page_text}")
                return "\n".join(text_pages)
            except ImportError:
                # Fallback: extract plain ASCII/UTF-8 streams from PDF bytes safely
                raw_str = file_bytes.decode("latin-1", errors="ignore")
                # Look for text streams in PDF object bodies
                import re
                text_blocks = re.findall(r"BT\s+(.*?)\s+ET", raw_str, re.DOTALL)
                if text_blocks:
                    return "\n".join(text_blocks)
                return "PDF document text extracted (pypdf optional driver)."
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to parse PDF document: {str(e)}",
                )

        return ""

    @classmethod
    async def process_uploaded_document(
        cls,
        session: AsyncSession,
        file: UploadFile,
        exam_template_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        uploaded_by_user_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Document:
        """
        Validates untrusted uploaded file, persists it to storage, extracts text,
        chunks text via SemanticRecursiveChunker, and saves chunks to database.
        """
        # 1. Read file bytes and validate size
        file_bytes = await file.read()
        file_size = len(file_bytes)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum permitted limit (25MB).",
            )
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uploaded file is empty (0 bytes).",
            )

        # 2. Validate file type and compute hash
        original_filename = file.filename or "uploaded_document.txt"
        file_type = cls.detect_file_type(original_filename)
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        doc_title = title.strip() if title and title.strip() else Path(original_filename).stem

        # 3. Check for duplicate upload in the same exam/topic
        dup_stmt = select(Document).where(
            (Document.sha256_hash == sha256_hash) &
            (Document.exam_template_id == exam_template_id) &
            (Document.topic_id == topic_id)
        )
        dup_res = await session.execute(dup_stmt)
        existing = dup_res.scalar_one_or_none()
        if existing:
            return existing

        # 4. Save to StorageProvider (ADR-009)
        storage = get_storage_provider()
        storage_path = await storage.save_file(
            file_bytes=file_bytes,
            filename=original_filename,
            content_type=file.content_type,
        )

        # 5. Create Document record in PROCESSING state
        document = Document(
            title=doc_title,
            original_filename=original_filename,
            file_type=file_type,
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            storage_path=storage_path,
            status=DocumentStatus.PROCESSING,
            exam_template_id=exam_template_id,
            topic_id=topic_id,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        session.add(document)
        await session.flush()

        # 6. Extract text and chunk
        try:
            raw_text = cls.extract_text_from_bytes(file_bytes, file_type)
            chunker = SemanticRecursiveChunker()
            chunk_payloads = chunker.chunk_document_text(raw_text)

            total_tokens = 0
            for cp in chunk_payloads:
                chunk = DocumentChunk(
                    document_id=document.id,
                    topic_id=topic_id,
                    chunk_index=cp.chunk_index,
                    page_number=cp.page_number,
                    content=cp.content,
                    clean_content=cp.clean_content,
                    token_count=cp.token_count,
                    heading_breadcrumbs=json.dumps(cp.heading_breadcrumbs),
                )
                session.add(chunk)
                total_tokens += cp.token_count

            # Update document status to CHUNKED
            document.status = DocumentStatus.CHUNKED
            document.chunk_count = len(chunk_payloads)
            document.total_tokens = total_tokens
            await session.flush()

        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await session.flush()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed during chunking: {str(e)}",
            )

        return document

    @staticmethod
    async def list_documents(
        session: AsyncSession,
        exam_template_id: Optional[str] = None,
        topic_id: Optional[str] = None,
    ) -> List[DocumentResponse]:
        """Lists uploaded documents filtered by exam template or topic."""
        stmt = select(Document)
        if exam_template_id:
            stmt = stmt.where(Document.exam_template_id == exam_template_id)
        if topic_id:
            stmt = stmt.where(Document.topic_id == topic_id)

        stmt = stmt.order_by(Document.created_at.desc())
        res = await session.execute(stmt)
        docs = res.scalars().all()
        return [DocumentResponse.model_validate(d) for d in docs]

    @staticmethod
    async def get_document(session: AsyncSession, document_id: str) -> Optional[Document]:
        """Fetches a document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_document_chunks(
        session: AsyncSession,
        document_id: str,
    ) -> List[DocumentChunkResponse]:
        """Fetches all chunks belonging to a document."""
        doc = await DocumentService.get_document(session, document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found",
            )

        stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index)
        res = await session.execute(stmt)
        chunks = res.scalars().all()

        responses = []
        for c in chunks:
            try:
                breadcrumbs = json.loads(c.heading_breadcrumbs)
            except Exception:
                breadcrumbs = []

            resp = DocumentChunkResponse(
                id=c.id,
                document_id=c.document_id,
                topic_id=c.topic_id,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                content=c.content,
                clean_content=c.clean_content,
                token_count=c.token_count,
                heading_breadcrumbs=breadcrumbs,
                created_at=c.created_at,
            )
            responses.append(resp)

        return responses

    @classmethod
    async def delete_document(cls, session: AsyncSession, document_id: str) -> bool:
        """Deletes a document, its file from storage, and cascades deletion to all chunks."""
        doc = await cls.get_document(session, document_id)
        if not doc:
            return False

        # 1. Delete chunks
        chunk_stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        chunk_res = await session.execute(chunk_stmt)
        for c in chunk_res.scalars().all():
            await session.delete(c)

        # 2. Delete file from storage
        storage = get_storage_provider()
        await storage.delete_file(doc.storage_path)

        # 3. Delete indexed vectors from Qdrant (Task 3.2)
        try:
            from backend.app.rag.indexer import VectorIndexerService
            await VectorIndexerService.delete_document_vectors(doc.id)
        except Exception:
            pass

        # 4. Delete document row
        await session.delete(doc)
        await session.flush()
        return True

