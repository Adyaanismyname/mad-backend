from fastapi import APIRouter
from api.endpoints import userEndpoints, workoutEndpoints, feedbackEndpoints

router = APIRouter()

router.include_router(userEndpoints.router, prefix="/users", tags=["users"])
router.include_router(workoutEndpoints.router, prefix="/workouts", tags=["workouts"])
router.include_router(feedbackEndpoints.router, prefix="/feedback", tags=["feedback"])



