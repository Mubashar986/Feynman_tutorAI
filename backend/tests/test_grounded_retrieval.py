import io
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import UploadFile

from backend.app.rag.indexer import VectorIndexerService
from backend.app.rag.retrieval import GroundedRetrievalService
from backend.app.rag.service import DocumentService


# ==============================================================================
# 1. GroundedRetrievalService Unit & Integration Tests (FR-008, Constraint #5)
# ==============================================================================

@pytest.mark.asyncio
async def test_grounded_retrieval_topic_filtered_search(db_session: AsyncSession):
    # 1. Ingest Physics Document on Thermodynamics
    doc_content = rb"""# Thermal Physics
## First Law of Thermodynamics
The change in internal energy is equal to heat added minus work done:
$$\Delta U = Q - W$$

## Carnot Cycle & Entropy
A Carnot engine operates between two temperatures T_hot and T_cold with maximum theoretical efficiency:
$$\eta = 1 - \frac{T_C}{T_H}$$
"""

    topic_thermo_id = f"top_thermo_{uuid.uuid4().hex[:6]}"
    upload = UploadFile(
        filename="thermo_physics.md",
        file=io.BytesIO(doc_content),
    )

    doc = await DocumentService.process_uploaded_document(
        session=db_session,
        file=upload,
        title="University Physics Thermodynamics",
        topic_id=topic_thermo_id,
    )

    # 2. Index document chunks
    indexed_cnt = await VectorIndexerService.index_document(db_session, doc.id)
    assert indexed_cnt >= 1

    # 3. Search with matching topic_id
    citations = await GroundedRetrievalService.search_curriculum_sources(
        query="Carnot engine efficiency and temperatures",
        topic_id=topic_thermo_id,
        limit=5,
        score_threshold=0.0,
    )
    assert len(citations) >= 1
    assert citations[0].document_title == "University Physics Thermodynamics"
    assert "Thermal Physics" in citations[0].heading_breadcrumbs

    # 4. Search with non-matching topic_id (Scope Protection)
    mismatched_citations = await GroundedRetrievalService.search_curriculum_sources(
        query="Carnot engine efficiency",
        topic_id="topic_optics_unrelated",
        limit=5,
        score_threshold=0.0,
    )
    assert len(mismatched_citations) == 0


@pytest.mark.asyncio
async def test_grounded_context_token_budgeting_and_formatting(db_session: AsyncSession):
    doc_content = b"""# Calculus Notes
## Fundamental Theorem of Calculus
The definite integral of a function is computed using its antiderivative.

## Integration by Parts
Formula: integral of u dv equals u v minus integral of v du.
"""
    topic_calc_id = f"top_calc_{uuid.uuid4().hex[:6]}"
    upload = UploadFile(
        filename="calculus_integration.md",
        file=io.BytesIO(doc_content),
    )
    doc = await DocumentService.process_uploaded_document(
        session=db_session,
        file=upload,
        title="AP Calculus Integration",
        topic_id=topic_calc_id,
    )
    await VectorIndexerService.index_document(db_session, doc.id)

    # Retrieve grounded context with token budget
    response = await GroundedRetrievalService.retrieve_grounded_context(
        query="Fundamental Theorem of Calculus and antiderivative",
        topic_id=topic_calc_id,
        limit=3,
        score_threshold=0.0,
        max_context_tokens=500,
    )

    assert response.total_sources >= 1
    assert "--- BEGIN GROUNDED CURRICULUM SOURCES ---" in response.formatted_context
    assert "[Source 1: AP Calculus Integration" in response.formatted_context
    assert "--- END GROUNDED CURRICULUM SOURCES ---" in response.formatted_context
    assert len(response.citations) == response.total_sources
    assert response.estimated_tokens > 0


# ==============================================================================
# 2. FastAPI Retrieval Endpoint Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_retrieval_api_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Ingest & index test document
    chem_topic_id = f"top_chem_{uuid.uuid4().hex[:6]}"
    doc_content = b"# Chemistry 101\n## Periodic Table\n\nNoble gases are chemically inert."
    upload = UploadFile(
        filename="chem.md",
        file=io.BytesIO(doc_content),
    )
    doc = await DocumentService.process_uploaded_document(
        session=db_session,
        file=upload,
        title="General Chemistry",
        topic_id=chem_topic_id,
    )
    await VectorIndexerService.index_document(db_session, doc.id)
    await db_session.commit()

    # 2. Test POST /api/v1/documents/search with topic scope
    search_payload = {
        "query": "Noble gases chemically inert",
        "topic_id": chem_topic_id,
        "limit": 3,
        "score_threshold": 0.0,
    }
    resp_search = await async_client.post("/api/v1/documents/search", json=search_payload)
    assert resp_search.status_code == 200
    citations = resp_search.json()
    assert len(citations) >= 1
    assert citations[0]["document_title"] == "General Chemistry"

    # 3. Test POST /api/v1/documents/grounded-context with topic scope
    context_payload = {
        "query": "Noble gases properties",
        "topic_id": chem_topic_id,
        "limit": 2,
        "score_threshold": 0.0,
        "max_context_tokens": 1000,
    }
    resp_context = await async_client.post("/api/v1/documents/grounded-context", json=context_payload)
    assert resp_context.status_code == 200
    context_data = resp_context.json()
    assert "BEGIN GROUNDED CURRICULUM SOURCES" in context_data["formatted_context"]
    assert context_data["total_sources"] >= 1

