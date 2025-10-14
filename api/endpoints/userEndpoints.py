from fastapi import APIRouter , status , Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from db.session import get_db
from schemas.userSchema import UserCreate, UserResponse
from core.auth import verify_admin_token
from models.user import User



router = APIRouter()


@router.get("/getAllUsers", response_model=dict)
async def get_all_users(admin : dict = Depends(verify_admin_token),db: Session = Depends(get_db)):
    try:
        users = await db.query(User).all()
        # Convert SQLAlchemy models to Pydantic models
        user_list = [UserResponse.model_validate(user).model_dump() for user in users]
        return {"data": user_list, "message": "Users retrieved successfully"}
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

