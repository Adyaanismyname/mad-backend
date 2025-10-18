from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy import select
from db.session import get_db
from schemas.userSchema import UserLogin, UserResponse, UserTokenData, UserFetch
from core.auth import verify_admin_token, create_access_token
from models.user import User
from schemas.core import StandardResponse



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
async def get_user(user_id: int, admin: dict = Depends(verify_admin_token), db: AsyncSession = Depends(get_db)):
    """
    Get specific user metadata by ID (Admin only).
    
    Returns: {"data": {user_data}, "message": "User retrieved successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (user not found), 503 (db error), 500 (server error)
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
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



@router.post("/login" , response_model=StandardResponse)
async def login_user(user_credentials : UserLogin, db : AsyncSession = Depends(get_db)):
    """
    Login a user and return a JWT token.
    
    Args:
        user_credentials (UserLogin): The user's login credentials
        db (AsyncSession): The database session (injected)
    Returns:
        StandardResponse: The response containing the JWT token and message
    Errors:
        401 Unauthorized: If credentials are invalid        
        500 Internal Server Error: If an unexpected error occurs
    """
    try:
        result = await db.execute(select(User).where(User.username == user_credentials.username))
        user = result.scalar_one_or_none()
        if not user or not user.verify_password(user_credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )  
        # Create JWT token
        token_data = UserTokenData(username=user.username, user_id=user.id)
        access_token = create_access_token(data=token_data.model_dump())

        return StandardResponse(data={"access_token": access_token}, message="Login successful")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


