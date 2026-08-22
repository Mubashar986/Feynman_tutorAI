from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.rag.models import DocumentStatus, DocumentType


# ==============================================================================
# 1. Document Chunk Schemas
# ==============================================================================

class DocumentChunkBase(BaseModel):
    chunk_index: int
    page_number: Optional[int] = 1
    content: str
    clean_content: str
    token_count: int
    heading_breadcrumbs: List[str] = []


class DocumentChunkResponse(DocumentChunkBase):
    id: str
    document_id: str
    topic_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkListResponse(BaseModel):
    document_id: str
    document_title: str
    total_chunks: int
    chunks: List[DocumentChunkResponse] = []


# ==============================================================================
# 2. Document Metadata Schemas
# ==============================================================================

class DocumentBase(BaseModel):
    title: str
    original_filename: str
    file_type: DocumentType = DocumentType.TEXT
    file_size_bytes: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    exam_template_id: Optional[str] = None
    topic_id: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: str
    sha256_hash: str
    chunk_count: int = 0
    total_tokens: int = 0
    uploaded_by_user_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse] = []


# ==============================================================================
# 3. Grounded Retrieval & Source Provenance Schemas (Task 3.3)
# ==============================================================================

class RetrievalQueryRequest(BaseModel):
    query: str = Field(..., description="The student's question or concept search text")
    exam_template_id: Optional[str] = Field(None, description="Optional exam template scope filter")
    topic_id: Optional[str] = Field(None, description="Optional curriculum topic scope filter")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of source chunks to retrieve")
    score_threshold: float = Field(default=0.60, ge=0.0, le=1.0, description="Minimum cosine similarity cutoff")
    max_context_tokens: int = Field(default=2048, ge=128, le=8192, description="Maximum total token budget for context assembly")


class RetrievedSourceCitation(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    exam_template_id: Optional[str] = None
    topic_id: Optional[str] = None
    page_number: Optional[int] = 1
    heading_breadcrumbs: List[str] = []
    similarity_score: float
    snippet: str
    clean_content: str


class GroundedContextResponse(BaseModel):
    query: str
    formatted_context: str
    citations: List[RetrievedSourceCitation] = []
    total_sources: int = 0
    estimated_tokens: int = 0

