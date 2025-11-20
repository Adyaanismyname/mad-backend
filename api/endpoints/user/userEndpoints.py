from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy import select
from db.session import get_db
from schemas.userSchema import UserLogin, UserTokenData, SignupRequest, VerifyOTP, UserResponse
from core.auth import create_access_token, verify_admin_token, verify_user_token
from models.user import User
from schemas.core import StandardResponse
from datetime import datetime, timedelta, timezone
from uuid import UUID
from api.endpoints.helper_methods import generate_and_send_otp

router = APIRouter()


@router.post("/login", response_model=StandardResponse)
async def login_user(
    user_credentials: UserLogin, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Login a user and return a JWT token or send OTP if not activated.
    
    Args:
        user_credentials (UserLogin): The user's login credentials
        background_tasks (BackgroundTasks): FastAPI background tasks
        db (AsyncSession): The database session (injected)
    Returns:
        StandardResponse: JWT token if activated, or message about OTP sent
    Errors:
        401 Unauthorized: If credentials are invalid
        403 Forbidden: If account is not activated (OTP will be sent)
        500 Internal Server Error: If an unexpected error occurs
    """
    try:
        # Use SQLAlchemy 2.0 style query
        result = await db.execute(select(User).filter(User.email == user_credentials.email))
        user = result.scalar_one_or_none()
        
        if not user or not user.verify_password(user_credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )  
            
        # Check if user is activated
        if not user.is_activated:
            # Send OTP for activation
            await generate_and_send_otp(user, db, background_tasks)
            return StandardResponse(
                data={"requires_activation": True}, 
                message="Account not activated. Verification OTP sent to email"
            )
            
        # Create JWT token - convert UUID to string
        token_data = {
            "username": None,
            "user_id": str(user.id),
            "is_admin": False
        }
        access_token = create_access_token(data=token_data)

        # Return user data along with token
        user_data = UserResponse.model_validate(user).model_dump()
        return StandardResponse(
            data={
                "access_token": access_token,
                "user": user_data
            }, 
            message="Login successful"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.post("/signup", response_model=StandardResponse)
async def signup_user(payload: SignupRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Signup a new user and send an OTP to their email for verification.
    """
    try:
        # Check if user exists
        result = await db.execute(select(User).filter(User.email == payload.email))
        exists = result.scalar_one_or_none()
        
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Create user
        user = User()
        user.email = payload.email
        user.full_name = payload.full_name or ""
        user.set_password(payload.password)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Generate and send OTP
        await generate_and_send_otp(user, db, background_tasks)

        return StandardResponse(data={}, message="Verification OTP sent to email")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/verify-otp", response_model=StandardResponse)
async def verify_otp(payload: VerifyOTP, db: AsyncSession = Depends(get_db)):
    """
    Verify an OTP sent to the user's email, activate account, and return a JWT token.
    """
    try:
        # Find user by email
        result = await db.execute(select(User).filter(User.email == payload.email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

        # Check if OTP exists
        if not user.otp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No OTP found for this user")

        # Check if OTP matches
        if user.otp != payload.token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        # Check if OTP is expired (10 minutes)
        if not user.otp_created_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP timestamp not found")
        
        otp_age = datetime.now(timezone.utc) - user.otp_created_at
        if otp_age > timedelta(minutes=10):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")

        # Activate user and clear the OTP after successful verification
        user.is_activated = True
        user.otp = None
        user.otp_created_at = None
        await db.commit()

        # Create JWT token - convert UUID to string
        token_data = {
            "username": None,
            "user_id": str(user.id),
            "is_admin": False
        }
        access_token = create_access_token(data=token_data)

        # Return user data along with token
        user_data = UserResponse.model_validate(user).model_dump()
        return StandardResponse(
            data={
                "access_token": access_token,
                "user": user_data
            }, 
            message="Account activated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/profile", response_model=StandardResponse)
async def get_my_profile(user_payload: dict = Depends(verify_user_token), db: AsyncSession = Depends(get_db)):
    """
    Get the authenticated user's profile information.
    
    Returns: {"data": {user_data}, "message": "Profile retrieved successfully"}
    Requires: Valid JWT token in Authorization header
    Errors: 401 (unauthorized), 404 (user not found), 503 (db error), 500 (server error)
    """
    try:
        user_id = UUID(user_payload.get("user_id"))
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = UserResponse.model_validate(user).model_dump()
        return StandardResponse(data=user_data, message="Profile retrieved successfully")
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
