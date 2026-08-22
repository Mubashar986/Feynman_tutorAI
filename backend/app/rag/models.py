from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CHUNKED = "chunked"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentType(str, Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"


class Document(SQLModel, table=True):
    """
    Metadata record for uploaded curriculum source documents (textbooks, notes, past papers) (PRD §5.3, FR-005).
    """
    __tablename__ = "documents"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    title: str = Field(index=True, nullable=False)
    original_filename: str = Field(nullable=False)
    file_type: DocumentType = Field(default=DocumentType.TEXT, nullable=False)
    file_size_bytes: int = Field(default=0, nullable=False)
    sha256_hash: str = Field(index=True, nullable=False)
    storage_path: str = Field(nullable=False)
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, nullable=False)
    error_message: Optional[str] = Field(default=None, nullable=True)

    exam_template_id: Optional[str] = Field(
        default=None,
        foreign_key="exam_templates.id",
        index=True,
        nullable=True,
    )
    topic_id: Optional[str] = Field(
        default=None,
        foreign_key="topics.id",
        index=True,
        nullable=True,
    )
    uploaded_by_user_id: Optional[str] = Field(
        default=None,
        foreign_key="users.id",
        index=True,
        nullable=True,
    )

    chunk_count: int = Field(default=0, nullable=False)
    total_tokens: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class DocumentChunk(SQLModel, table=True):
    """
    Atomic text chunk produced by the SemanticRecursiveChunker (ADR-018, FR-008).
    Linked to document, topic, page number, and heading hierarchy breadcrumbs.
    """
    __tablename__ = "document_chunks"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    document_id: str = Field(
        foreign_key="documents.id",
        index=True,
        nullable=False,
    )
    topic_id: Optional[str] = Field(
        default=None,
        foreign_key="topics.id",
        index=True,
        nullable=True,
    )
    chunk_index: int = Field(default=0, nullable=False)
    page_number: Optional[int] = Field(default=1, nullable=True)
    content: str = Field(nullable=False)  # Enriched content (includes breadcrumb header)
    clean_content: str = Field(nullable=False)  # Unmodified chunk text
    token_count: int = Field(default=0, nullable=False)
    heading_breadcrumbs: str = Field(default="[]", nullable=False)  # JSON-encoded list[str]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
