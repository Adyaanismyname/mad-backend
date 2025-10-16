from fastapi import APIRouter
from api.endpoints.admin import userEndpoints as admin_user_endpoints
from api.endpoints.user import userEndpoints as user_endpoints

router = APIRouter()

# Admin endpoints
router.include_router(admin_user_endpoints.router, prefix="/admin/users", tags=["admin-users"])

# Regular user endpoints  
router.include_router(user_endpoints.router, prefix="/users", tags=["users"])



