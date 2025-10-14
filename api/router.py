from fastapi import APIRouter
from api.endpoints import userEndpoints

router = APIRouter()

router.include_router(userEndpoints.router, prefix="/users", tags=["users"])



