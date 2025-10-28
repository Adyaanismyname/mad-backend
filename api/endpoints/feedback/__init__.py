from fastapi import APIRouter
from .media_upload import router as media_upload_router
from .media_query import router as media_query_router
from .media_management import router as media_management_router
from .feedback_create import router as feedback_create_router
from .feedback_query import router as feedback_query_router
from .feedback_management import router as feedback_management_router

# Create main feedback router
router = APIRouter()

# Include all sub-routers
router.include_router(media_upload_router, tags=["Media Upload"])
router.include_router(media_query_router, tags=["Media Query"])
router.include_router(media_management_router, tags=["Media Management"])
router.include_router(feedback_create_router, tags=["Feedback Create"])
router.include_router(feedback_query_router, tags=["Feedback Query"])
router.include_router(feedback_management_router, tags=["Feedback Management"])

__all__ = ["router"]