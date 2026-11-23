from fastapi import APIRouter

from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.assessments import router as assessments_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.knowledge import router as knowledge_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(assessments_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(knowledge_router)
api_v1_router.include_router(admin_router)

__all__ = ["api_v1_router"]
