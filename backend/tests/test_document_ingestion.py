import io
import os
import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.core.storage.local import LocalStorageProvider
from backend.app.rag.chunker import SemanticRecursiveChunker
from backend.app.rag.models import DocumentStatus, DocumentType
from backend.app.rag.service import DocumentService


# ==============================================================================
# 1. LocalStorageProvider Unit Tests (ADR-009)
# ==============================================================================

@pytest.mark.asyncio
async def test_local_storage_provider_save_get_delete(tmp_path):
    storage = LocalStorageProvider(base_directory=str(tmp_path))
    content = b"Physics notes on classical mechanics."

    # 1. Save file
    storage_path = await storage.save_file(content, "mechanics.txt")
    assert os.path.exists(storage_path)

    # 2. Read file
    read_bytes = await storage.get_file_bytes(storage_path)
    assert read_bytes == content

    # 3. Delete file
    deleted = await storage.delete_file(storage_path)
    assert deleted is True
    assert not os.path.exists(storage_path)


@pytest.mark.asyncio
async def test_local_storage_path_traversal_guard(tmp_path):
    storage = LocalStorageProvider(base_directory=str(tmp_path))

    # Attempting to access outside directory must raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await storage.get_file_bytes("../../../etc/passwd")
    assert "Path traversal detected" in str(exc_info.value)


# ==============================================================================
# 2. SemanticRecursiveChunker Unit Tests (ADR-018)
# ==============================================================================

def test_chunker_preserves_heading_breadcrumbs():
    markdown_text = """# Cambridge Physics 9702
## Chapter 1: Kinematics
### Section 1.1: Projectile Motion

A projectile is an object upon which the only force acting is gravity.
The horizontal motion occurs at constant velocity.

### Section 1.2: Angular Trajectories

When an object is launched at an angle theta, its range is derived from kinematics equations.
"""
    chunker = SemanticRecursiveChunker(target_tokens=40, overlap_tokens=10)
    chunks = chunker.chunk_document_text(markdown_text)

    assert len(chunks) >= 2
    # Verify heading breadcrumbs
    first_chunk = chunks[0]
    assert "Cambridge Physics 9702" in first_chunk.heading_breadcrumbs
    assert "Chapter 1: Kinematics" in first_chunk.heading_breadcrumbs
    assert "Section 1.1: Projectile Motion" in first_chunk.heading_breadcrumbs
    assert "[Context:" in first_chunk.content


def test_chunker_preserves_latex_mathematical_formulas():
    physics_doc_with_math = r"""# Dynamics & Energy
## Kinetic Energy & Work

The work done on an object is equal to the change in kinetic energy:
$$W = \int_{x_1}^{x_2} F(x) \, dx = \frac{1}{2}mv_2^2 - \frac{1}{2}mv_1^2$$

Also consider the relativistic mass equation: $E = \gamma m_0 c^2$ where \(\gamma = \frac{1}{\sqrt{1 - v^2/c^2}}\).
"""
    chunker = SemanticRecursiveChunker(target_tokens=30, overlap_tokens=5)
    chunks = chunker.chunk_document_text(physics_doc_with_math)

    assert len(chunks) >= 1
    # Verify LaTeX formulas are intact
    full_text = " ".join([c.clean_content for c in chunks])
    assert r"$$W = \int_{x_1}^{x_2} F(x) \, dx = \frac{1}{2}mv_2^2 - \frac{1}{2}mv_1^2$$" in full_text
    assert r"$E = \gamma m_0 c^2$" in full_text



# ==============================================================================
# 3. DocumentService Ingestion Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_service_ingest_markdown_file(db_session: AsyncSession):
    content = b"# Calculus BC\n## Derivatives\n\nThe power rule states that d/dx(x^n) = n*x^(n-1)."
    from fastapi import UploadFile

    upload = UploadFile(
        filename=f"calculus_{uuid.uuid4().hex[:6]}.md",
        file=io.BytesIO(content),
    )

    doc = await DocumentService.process_uploaded_document(
        session=db_session,
        file=upload,
        title="AP Calculus Derivatives Guide",
    )

    assert doc.id is not None
    assert doc.status == DocumentStatus.CHUNKED
    assert doc.chunk_count >= 1
    assert doc.total_tokens > 0

    # Fetch chunks
    chunks = await DocumentService.get_document_chunks(db_session, doc.id)
    assert len(chunks) == doc.chunk_count
    assert "Calculus BC" in chunks[0].heading_breadcrumbs


@pytest.mark.asyncio
async def test_document_service_rejects_empty_file(db_session: AsyncSession):
    from fastapi import UploadFile

    empty_upload = UploadFile(
        filename="empty.txt",
        file=io.BytesIO(b""),
    )

    with pytest.raises(Exception) as exc_info:
        await DocumentService.process_uploaded_document(db_session, empty_upload)
    assert "empty" in str(exc_info.value).lower()


# ==============================================================================
# 4. FastAPI Endpoint Integration & Role Protection Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_document_upload_role_protection(async_client: AsyncClient):
    # 1. Register Student & Instructor
    student_email = f"doc.student.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": student_email, "password": "Password123!", "full_name": "Student RAG", "role": "student"},
    )
    login_stud = await async_client.post(
        "/api/v1/auth/login",
        json={"email": student_email, "password": "Password123!"},
    )
    student_token = login_stud.json()["access_token"]

    inst_email = f"doc.inst.{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": inst_email, "password": "Password123!", "full_name": "Instructor RAG", "role": "instructor"},
    )
    login_inst = await async_client.post(
        "/api/v1/auth/login",
        json={"email": inst_email, "password": "Password123!"},
    )
    inst_token = login_inst.json()["access_token"]

    file_payload = {"file": ("physics_notes.md", b"# Chapter 1\n\nVelocity is displacement over time.", "text/markdown")}

    # 2. Student attempts upload -> MUST BE 403 FORBIDDEN
    resp_student = await async_client.post(
        "/api/v1/documents/upload",
        files=file_payload,
        data={"title": "Unauthorized Student Upload"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp_student.status_code == 403

    # 3. Instructor uploads -> MUST BE 201 CREATED
    file_payload_inst = {"file": ("physics_notes.md", b"# Chapter 1\n\nVelocity is displacement over time.", "text/markdown")}
    resp_inst = await async_client.post(
        "/api/v1/documents/upload",
        files=file_payload_inst,
        data={"title": "Official Physics Notes"},
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert resp_inst.status_code == 201
    doc_data = resp_inst.json()
    assert doc_data["status"] == "chunked"
    doc_id = doc_data["id"]

    # 4. Public/Student can view document chunks
    chunks_resp = await async_client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunks_resp.status_code == 200
    chunks = chunks_resp.json()
    assert len(chunks) >= 1

    # 5. Instructor deletes document -> MUST BE 204 NO CONTENT
    del_resp = await async_client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {inst_token}"},
    )
    assert del_resp.status_code == 204
