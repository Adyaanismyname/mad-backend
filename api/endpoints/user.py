from fastapi import APIRouter , status , Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from db.session import get_db
from schemas.user import UserCreate, UserResponse
from models.user import User



router = APIRouter()


@router.get("/getAllUsers", response_model=dict)
def get_all_users(db: Session = Depends(get_db)):
    try:
        users = db.query(User).all()
        # Convert SQLAlchemy models to Pydantic models
        user_list = [UserResponse.model_validate(user).model_dump() for user in users]
        return {"data": user_list, "message": "Users retrieved successfully"}
    except OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. The database might be sleeping (Render free tier). Please try again in 30-60 seconds."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

