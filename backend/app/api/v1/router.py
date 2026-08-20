from fastapi import APIRouter
from backend.app.api.v1.endpoints import health

api_router = APIRouter()

# Health & Diagnostics routes
api_router.include_router(health.router, prefix="", tags=["Health & Diagnostics"])
