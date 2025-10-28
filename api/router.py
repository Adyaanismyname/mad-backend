from fastapi import APIRouter
from api.endpoints import userEndpoints
from api.endpoints.feedback import router as feedback_router
from api.endpoints.workout import router as workout_router
from api.endpoints.admin import userEndpoints as admin_user_endpoints
from api.endpoints.user import userEndpoints as user_endpoints

router = APIRouter()

router.include_router(userEndpoints.router, prefix="/users", tags=["users"])
router.include_router(workout_router, prefix="/workouts", tags=["workouts"])
router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
# Admin endpoints
router.include_router(admin_user_endpoints.router, prefix="/admin/users", tags=["admin-users"])

# Regular user endpoints  
router.include_router(user_endpoints.router, prefix="/users", tags=["users"])



