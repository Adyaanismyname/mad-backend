from fastapi import APIRouter
from api.endpoints.workout import router as workout_router
from api.endpoints.relationship import router as relationship_router
from api.endpoints.admin import userEndpoints as admin_user_endpoints
from api.endpoints.user import userEndpoints as user_endpoints

router = APIRouter()

# Regular user endpoints  
router.include_router(user_endpoints.router, prefix="/users", tags=["users"])
router.include_router(workout_router, prefix="/workouts", tags=["workouts"])
router.include_router(relationship_router, prefix="/relationships", tags=["relationships"])
# Admin endpoints
router.include_router(admin_user_endpoints.router, prefix="/admin/users", tags=["admin-users"])



