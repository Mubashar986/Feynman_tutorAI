from fastapi import APIRouter
from backend.app.api.v1.endpoints import health
from backend.app.auth import auth_router
from backend.app.learning_state import learning_state_router
from backend.app.curriculum import curriculum_router

api_router = APIRouter()

# Health & Diagnostics routes
api_router.include_router(health.router, prefix="", tags=["Health & Diagnostics"])

# Authentication & RBAC routes
api_router.include_router(auth_router, prefix="", tags=["Authentication & RBAC"])

# Learning State Machine & Audit Log routes
api_router.include_router(learning_state_router, prefix="", tags=["Learning State Machine"])

# Exam Templates & Curriculum routes
api_router.include_router(curriculum_router, prefix="", tags=["Exam Templates & Curriculum"])

