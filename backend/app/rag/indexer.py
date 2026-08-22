import json
from typing import Any, Dict, List
from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.llm.embedding import get_embedding_provider
from backend.app.core.vector import VectorPoint, get_vector_store
from backend.app.rag.models import Document, DocumentChunk, DocumentStatus

CURRICULUM_COLLECTION_NAME = "curriculum_chunks"


class VectorIndexerService:
    """
    Application domain service for batch embedding generation and Qdrant vector indexing (PRD §5.3, FR-008, ADR-003).
    """

    @classmethod
    async def index_document(cls, session: AsyncSession, document_id: str) -> int:
        """
        Embeds all chunks for a document, builds rich payload metadata,
        upserts into Qdrant, and transitions document status to INDEXED.
        """
        # 1. Fetch document and chunks
        stmt_doc = select(Document).where(Document.id == document_id)
        res_doc = await session.execute(stmt_doc)
        doc = res_doc.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found",
            )

        stmt_chunks = select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index)
        res_chunks = await session.execute(stmt_chunks)
        chunks = res_chunks.scalars().all()

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document '{document_id}' has 0 chunks to index.",
            )

        # 2. Generate embeddings
        embedder = get_embedding_provider()
        texts_to_embed = [c.content for c in chunks]
        embeddings = await embedder.embed_texts(texts_to_embed)

        # 3. Assemble VectorPoints with rich metadata payloads
        points: List[VectorPoint] = []
        for chunk, embedding in zip(chunks, embeddings):
            try:
                breadcrumbs = json.loads(chunk.heading_breadcrumbs)
            except Exception:
                breadcrumbs = []

            payload = {
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "exam_template_id": doc.exam_template_id,
                "topic_id": chunk.topic_id or doc.topic_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "token_count": chunk.token_count,
                "heading_breadcrumbs": breadcrumbs,
                "clean_content": chunk.clean_content,
                "content": chunk.content,
            }

            points.append(
                VectorPoint(
                    id=chunk.id,
                    vector=embedding,
                    payload=payload,
                )
            )

        # 4. Upsert into VectorStore (Qdrant)
        vector_store = get_vector_store()
        await vector_store.create_collection(
            collection_name=CURRICULUM_COLLECTION_NAME,
            dimension=embedder.dimension,
        )
        await vector_store.upsert_points(
            collection_name=CURRICULUM_COLLECTION_NAME,
            points=points,
        )

        # 5. Update relational state to INDEXED
        doc.status = DocumentStatus.INDEXED
        await session.flush()

        return len(points)

    @classmethod
    async def index_exam_template(
        cls,
        session: AsyncSession,
        exam_template_id: str,
    ) -> Dict[str, Any]:
        """
        Batch indexes all documents belonging to a specific exam template.
        """
        stmt = select(Document).where(Document.exam_template_id == exam_template_id)
        res = await session.execute(stmt)
        docs = res.scalars().all()

        total_chunks = 0
        indexed_docs = 0

        for doc in docs:
            chunks_indexed = await cls.index_document(session, doc.id)
            total_chunks += chunks_indexed
            indexed_docs += 1

        return {
            "exam_template_id": exam_template_id,
            "documents_indexed": indexed_docs,
            "total_chunks_indexed": total_chunks,
        }

    @classmethod
    async def delete_document_vectors(cls, document_id: str) -> bool:
        """
        Removes all indexed vector points associated with a deleted document.
        """
        vector_store = get_vector_store()
        return await vector_store.delete_by_payload(
            collection_name=CURRICULUM_COLLECTION_NAME,
            field_name="document_id",
            field_value=document_id,
        )
