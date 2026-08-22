import io
import math
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import UploadFile

from backend.app.core.llm.embedding import MockDeterministicEmbeddingProvider
from backend.app.core.vector import (
    VectorPoint,
    get_vector_store,
)
from backend.app.rag.indexer import VectorIndexerService, CURRICULUM_COLLECTION_NAME
from backend.app.rag.models import DocumentStatus
from backend.app.rag.service import DocumentService


# ==============================================================================
# 1. Embedding Provider Unit Tests (ADR-007)
# ==============================================================================

@pytest.mark.asyncio
async def test_mock_deterministic_embedding_provider_properties():
    embedder = MockDeterministicEmbeddingProvider(dimension=768)

    assert embedder.dimension == 768

    text_a = "Kinematics is the branch of classical mechanics describing motion."
    text_b = "Kinematics is the branch of classical mechanics describing motion."
    text_c = "Organic chemistry deals with carbon compounds and reactions."

    vec_a = await embedder.embed_text(text_a)
    vec_b = await embedder.embed_text(text_b)
    vec_c = await embedder.embed_text(text_c)

    # 1. Dimension check
    assert len(vec_a) == 768

    # 2. Unit normalization check: ||v|| == 1.0
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    assert math.isclose(norm_a, 1.0, rel_tol=1e-5)

    # 3. Determinism check: identical text yields identical vectors
    assert vec_a == vec_b

    # 4. Different text yields distinct vector
    assert vec_a != vec_c


# ==============================================================================
# 2. Vector Store & Payload Filtering Tests (ADR-003)
# ==============================================================================

@pytest.mark.asyncio
async def test_vector_store_upsert_and_payload_filter():
    vector_store = get_vector_store()
    collection_name = f"test_coll_{uuid.uuid4().hex[:6]}"

    await vector_store.create_collection(collection_name, dimension=4)

    # Insert 2 points with different topic_ids
    p1 = VectorPoint(
        id="chunk_1",
        vector=[1.0, 0.0, 0.0, 0.0],
        payload={"topic_id": "topic_physics", "title": "Newton's Laws"},
    )
    p2 = VectorPoint(
        id="chunk_2",
        vector=[0.0, 1.0, 0.0, 0.0],
        payload={"topic_id": "topic_calculus", "title": "Derivatives"},
    )

    await vector_store.upsert_points(collection_name, [p1, p2])

    # Search with query close to p1
    results = await vector_store.search(
        collection_name=collection_name,
        query_vector=[0.9, 0.1, 0.0, 0.0],
        limit=5,
    )
    assert len(results) == 2
    assert results[0].id == "chunk_1"

    # Search with topic_id filter for calculus
    filtered = await vector_store.search(
        collection_name=collection_name,
        query_vector=[1.0, 0.0, 0.0, 0.0],
        limit=5,
        filter_conditions={"topic_id": "topic_calculus"},
    )
    assert len(filtered) == 1
    assert filtered[0].id == "chunk_2"


# ==============================================================================
# 3. VectorIndexerService Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_vector_indexer_lifecycle(db_session: AsyncSession):
    # 1. Ingest a document
    content = b"# Electromagnetic Theory\n## Maxwell Equations\n\nGauss law states that electric flux is proportional to charge."
    upload = UploadFile(
        filename=f"em_theory_{uuid.uuid4().hex[:6]}.md",
        file=io.BytesIO(content),
    )

    doc = await DocumentService.process_uploaded_document(
        session=db_session,
        file=upload,
        title="Electromagnetism Notes",
    )
    assert doc.status == DocumentStatus.CHUNKED

    # 2. Index the document into Qdrant
    indexed_count = await VectorIndexerService.index_document(db_session, doc.id)
    assert indexed_count >= 1
    assert doc.status == DocumentStatus.INDEXED

    # 3. Query vector store directly
    vector_store = get_vector_store()
    results = await vector_store.search(
        collection_name=CURRICULUM_COLLECTION_NAME,
        query_vector=[0.5] * 768,
        limit=5,
        filter_conditions={"document_id": doc.id},
    )
    assert len(results) >= 1
    assert results[0].payload["document_title"] == "Electromagnetism Notes"

    # 4. Delete document and verify vectors are removed
    await DocumentService.delete_document(db_session, doc.id)
    remaining = await vector_store.search(
        collection_name=CURRICULUM_COLLECTION_NAME,
        query_vector=[0.5] * 768,
        limit=5,
        filter_conditions={"document_id": doc.id},
    )
    assert len(remaining) == 0


# ==============================================================================
# 4. FastAPI Indexing Endpoint & Role Protection Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_indexing_endpoints_role_protection(async_client: AsyncClient):
    # 1. Register Instructor & Student
    inst_email = f"index.inst.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": inst_email, "password": "Password123!", "full_name": "Instructor Indexer", "role": "instructor"},
    )
    login_inst = await async_client.post(
        "/api/v1/auth/login",
        json={"email": inst_email, "password": "Password123!"},
    )
    inst_token = login_inst.json()["access_token"]

    student_email = f"index.stud.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": student_email, "password": "Password123!", "full_name": "Student Indexer", "role": "student"},
    )
    login_stud = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_email, "password": "Password123!"},
    )
    student_token = login_stud.json()["access_token"]

    # 2. Instructor uploads a document
    file_payload = {"file": ("algebra_ch1.md", b"# Algebra 101\n\nLinear equations in one variable.", "text/markdown")}
    upload_resp = await async_client.post(
        "/api/v1/documents/upload",
        files=file_payload,
        data={"title": "Algebra Basics"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    # 3. Student tries to trigger index -> MUST BE 403 FORBIDDEN
    resp_student_index = await async_client.post(
        f"/api/v1/documents/{doc_id}/index",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp_student_index.status_code == 403

    # 4. Instructor triggers index -> MUST BE 200 OK
    resp_inst_index = await async_client.post(
        f"/api/v1/documents/{doc_id}/index",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_inst_index.status_code == 200
    assert resp_inst_index.json()["status"] == "indexed"
    assert resp_inst_index.json()["chunks_indexed"] >= 1
