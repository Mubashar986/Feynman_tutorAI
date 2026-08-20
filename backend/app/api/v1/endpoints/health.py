from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Response
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.health_service import HealthService

router = APIRouter(tags=["Health & Diagnostics"])


@router.get(
    "/healthz",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Returns immediate 200 OK to confirm the web process is alive and accepting connections.",
)
async def liveness_check() -> Dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Validates database connectivity, latency, and core system health.",
)
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    db_health = await HealthService.check_database(db)
    system_info = HealthService.get_system_info()

    is_healthy = db_health["status"] == "connected"
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "database": db_health,
        "system": system_info,
    }
