import time
from typing import Dict, Any
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.config import settings


class HealthService:
    @staticmethod
    async def check_database(db: AsyncSession) -> Dict[str, Any]:
        """Executes a non-blocking heartbeat query and measures response latency."""
        start_time = time.perf_counter()
        try:
            result = await db.exec(text("SELECT 1"))
            val = result.first()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            is_connected = val is not None and (val == 1 or val[0] == 1)
            return {
                "status": "connected" if is_connected else "degraded",
                "latency_ms": latency_ms,
                "error": None,
            }
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "status": "disconnected",
                "latency_ms": latency_ms,
                "error": str(e),
            }

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Returns application metadata."""
        return {
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "api_version": settings.API_V1_STR,
        }
