from typing import List, Optional
from backend.app.core.llm.embedding import get_embedding_provider
from backend.app.core.vector import get_vector_store
from backend.app.rag.indexer import CURRICULUM_COLLECTION_NAME
from backend.app.rag.schemas import (
    GroundedContextResponse,
    RetrievedSourceCitation,
)


class GroundedRetrievalService:
    """
    Pedagogical grounded retrieval service enforcing topic scoping,
    relevance thresholding, and source provenance formatting (PRD §5.3, §14.3, FR-008, Constraint #5).
    """

    @classmethod
    async def search_curriculum_sources(
        cls,
        query: str,
        exam_template_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.60,
    ) -> List[RetrievedSourceCitation]:
        """
        Executes semantic vector search against curriculum_chunks with topic/exam payload filtering.
        """
        if not query or not query.strip():
            return []

        # 1. Embed query
        embedder = get_embedding_provider()
        query_vector = await embedder.embed_text(query.strip())

        # 2. Build payload filter conditions
        filter_conditions = {}
        if exam_template_id:
            filter_conditions["exam_template_id"] = exam_template_id
        if topic_id:
            filter_conditions["topic_id"] = topic_id

        # 3. Search vector store
        vector_store = get_vector_store()
        effective_threshold = None if score_threshold is not None and score_threshold <= 0.0 else score_threshold
        search_results = await vector_store.search(
            collection_name=CURRICULUM_COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            score_threshold=effective_threshold,
            filter_conditions=filter_conditions if filter_conditions else None,
        )


        # 4. Map to structured citations
        citations: List[RetrievedSourceCitation] = []
        for res in search_results:
            clean_content = res.payload.get("clean_content", "")
            snippet = clean_content[:250] + "..." if len(clean_content) > 250 else clean_content
            breadcrumbs = res.payload.get("heading_breadcrumbs", [])

            citation = RetrievedSourceCitation(
                chunk_id=res.id,
                document_id=res.payload.get("document_id", ""),
                document_title=res.payload.get("document_title", "Curriculum Document"),
                exam_template_id=res.payload.get("exam_template_id"),
                topic_id=res.payload.get("topic_id"),
                page_number=res.payload.get("page_number", 1),
                heading_breadcrumbs=breadcrumbs,
                similarity_score=round(float(res.score), 4),
                snippet=snippet,
                clean_content=clean_content,
            )
            citations.append(citation)

        return citations

    @classmethod
    def _format_context_block(cls, citations: List[RetrievedSourceCitation]) -> str:
        """
        Formats retrieved sources into a standardized, anti-hallucination prompt context block.
        """
        if not citations:
            return ""

        context_lines = ["--- BEGIN GROUNDED CURRICULUM SOURCES ---"]
        for idx, cit in enumerate(citations, start=1):
            path_str = " > ".join(cit.heading_breadcrumbs) if cit.heading_breadcrumbs else "General Content"
            header = f"[Source {idx}: {cit.document_title} | {path_str} | Page {cit.page_number}]"
            context_lines.append(f"{header}\n{cit.clean_content}\n")

        context_lines.append("--- END GROUNDED CURRICULUM SOURCES ---")
        return "\n".join(context_lines)

    @classmethod
    async def retrieve_grounded_context(
        cls,
        query: str,
        exam_template_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.60,
        max_context_tokens: int = 2048,
    ) -> GroundedContextResponse:
        """
        Retrieves relevant curriculum sources, applies greedy token budgeting,
        and formats an LLM-ready prompt block alongside structured citation metadata.
        """
        all_citations = await cls.search_curriculum_sources(
            query=query,
            exam_template_id=exam_template_id,
            topic_id=topic_id,
            limit=limit,
            score_threshold=score_threshold,
        )

        # Greedy token budgeting
        admitted_citations: List[RetrievedSourceCitation] = []
        current_token_count = 0

        for cit in all_citations:
            # Estimate tokens (~4 chars per token)
            chunk_tokens = max(1, len(cit.clean_content) // 4)
            if current_token_count + chunk_tokens <= max_context_tokens:
                admitted_citations.append(cit)
                current_token_count += chunk_tokens
            else:
                # Stop if budget is reached
                break

        formatted_context = cls._format_context_block(admitted_citations)
        total_estimated_tokens = max(0, len(formatted_context) // 4)

        return GroundedContextResponse(
            query=query,
            formatted_context=formatted_context,
            citations=admitted_citations,
            total_sources=len(admitted_citations),
            estimated_tokens=total_estimated_tokens,
        )
