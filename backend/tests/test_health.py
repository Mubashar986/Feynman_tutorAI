import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.services.health_service import HealthService


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Verify root GET / returns project metadata and documentation links."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "version" in data
    assert data["api_v1"] == "/api/v1"


@pytest.mark.asyncio
async def test_root_liveness(async_client: AsyncClient):
    """Verify /healthz returns immediate 200 OK."""
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_v1_liveness(async_client: AsyncClient):
    """Verify /api/v1/healthz returns immediate 200 OK."""
    response = await async_client.get("/api/v1/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_v1_readiness(async_client: AsyncClient):
    """Verify /api/v1/health validates database connectivity and latency."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"
    assert isinstance(data["database"]["latency_ms"], (int, float))
    assert data["system"]["project_name"] == "AI-Powered Adaptive Exam Learning Platform"


@pytest.mark.asyncio
async def test_health_service_direct(db_session: AsyncSession):
    """Unit test HealthService.check_database directly against in-memory async session."""
    health_result = await HealthService.check_database(db_session)
    assert health_result["status"] == "connected"
    assert health_result["latency_ms"] >= 0
    assert health_result["error"] is None
