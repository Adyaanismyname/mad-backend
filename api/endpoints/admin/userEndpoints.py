from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy import select
from db.session import get_db
from schemas.userSchema import UserResponse, UserFetch
from core.auth import verify_admin_token
from models.user import User
from schemas.core import StandardResponse
from uuid import UUID

router = APIRouter()


@router.get("/getAllUsers", response_model=StandardResponse)
async def get_all_users(admin: dict = Depends(verify_admin_token), db: AsyncSession = Depends(get_db)):
    """
    Get all users from the database (Admin only).
    
    Returns: {"data": [user_list], "message": "Users retrieved successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 503 (db error), 500 (server error)
    """
    try:
        result = await db.execute(select(User))
        users = result.scalars().all()
        # Convert SQLAlchemy models to Pydantic models
        user_list = [UserResponse.model_validate(user).model_dump() for user in users]
        return StandardResponse(data=user_list, message="Users retrieved successfully")
    except OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/getUser/{user_id}", response_model=StandardResponse)
async def get_user(user_id: UUID, admin: dict = Depends(verify_admin_token), db: AsyncSession = Depends(get_db)):
    """
    Get specific user metadata by ID (Admin only).
    
    Returns: {"data": {user_data}, "message": "User retrieved successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (user not found), 503 (db error), 500 (server error)
    """
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        user_data = UserResponse.model_validate(user).model_dump()
        return StandardResponse(data=user_data, message="User retrieved successfully")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )