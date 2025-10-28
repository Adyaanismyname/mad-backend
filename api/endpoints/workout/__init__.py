from fastapi import APIRouter
from .assignment import router as assignment_router
from .create import router as create_router
from .query import router as query_router
from .excercise_management import router as exercise_management_router
from .delete import router as delete_router
from .update import router as update_router
# Create main feedback router
router = APIRouter()

# Include all sub-routers
router.include_router(assignment_router, tags=["Assignment"])
router.include_router(create_router, tags=["Create"])
router.include_router(query_router, tags=["Query"])
router.include_router(exercise_management_router, tags=["Exercise Management"])
router.include_router(delete_router, tags=["Delete"])
router.include_router(update_router, tags=["Update"])


__all__ = ["router"]