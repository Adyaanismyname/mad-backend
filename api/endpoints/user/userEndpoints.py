from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy import select
from db.session import get_db
from schemas.userSchema import UserLogin, UserTokenData, SignupRequest, VerifyOTP
from core.auth import create_access_token
from models.user import User
from schemas.core import StandardResponse
from models.email_verification_token import EmailVerificationToken
from fastapi import BackgroundTasks
from core.mailer import send_verification_email
from datetime import datetime, timedelta
import random
import string
import uuid

router = APIRouter()


@router.post("/login", response_model=StandardResponse)
async def login_user(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
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
        # Use SQLAlchemy 2.0 style query
        result = await db.execute(select(User).filter(User.email == user_credentials.email))
        user = result.scalar_one_or_none()
        
        if not user or not user.verify_password(user_credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )  
        # Create JWT token - convert UUID to string
        token_data = {
            "username": None,
            "user_id": str(user.id),
            "is_admin": False
        }
        access_token = create_access_token(data=token_data)

        return StandardResponse(data={"access_token": access_token}, message="Login successful")
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

        # Generate OTP (6-digit)
        otp = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        token_record = EmailVerificationToken(user_id=user.id, token=otp, expires_at=expires_at)
        db.add(token_record)
        await db.commit()

        # Send email in background
        background_tasks.add_task(send_verification_email, user.email, otp, 10)

        return StandardResponse(data={}, message="Verification OTP sent to email")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/verify-otp", response_model=StandardResponse)
async def verify_otp(payload: VerifyOTP, db: AsyncSession = Depends(get_db)):
    """
    Verify an OTP sent to the user's email and return a JWT token.
    """
    try:
        # Find token record and join user using SQLAlchemy 2.0 style
        result = await db.execute(
            select(EmailVerificationToken)
            .join(User)
            .filter(
                EmailVerificationToken.token == payload.token,
                User.email == payload.email,
                EmailVerificationToken.is_used == False
            )
        )
        token_row = result.scalar_one_or_none()

        if not token_row:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or used token")

        if token_row.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

        # Mark token used
        token_row.is_used = True
        await db.commit()

        user = token_row.user
        # Create JWT token - convert UUID to string
        token_data = {
            "username": None,
            "user_id": str(user.id),
            "is_admin": False
        }
        access_token = create_access_token(data=token_data)

        return StandardResponse(data={"access_token": access_token}, message="Verification successful")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))