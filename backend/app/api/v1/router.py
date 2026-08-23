from fastapi import APIRouter
from backend.app.api.v1.endpoints import health
from backend.app.auth import auth_router
from backend.app.learning_state import learning_state_router
from backend.app.curriculum import curriculum_router
from backend.app.rag import documents_router
from backend.app.questions import questions_router
from backend.app.mastery import mastery_router

api_router = APIRouter()

# Health & Diagnostics routes
api_router.include_router(health.router, prefix="", tags=["Health & Diagnostics"])

# Authentication & RBAC routes
api_router.include_router(auth_router, prefix="", tags=["Authentication & RBAC"])

# Learning State Machine & Audit Log routes
api_router.include_router(learning_state_router, prefix="", tags=["Learning State Machine"])

# Exam Templates & Curriculum routes
api_router.include_router(curriculum_router, prefix="", tags=["Exam Templates & Curriculum"])

# Vector RAG & Resource Ingestion routes
api_router.include_router(documents_router, prefix="", tags=["Vector RAG & Resource Ingestion"])

# Question Bank & Item Lab routes
api_router.include_router(questions_router, prefix="", tags=["Question Bank & Item Lab"])

# Student Mastery & Difficulty Calibration routes
api_router.include_router(mastery_router, prefix="", tags=["Student Mastery & Difficulty Calibration"])



