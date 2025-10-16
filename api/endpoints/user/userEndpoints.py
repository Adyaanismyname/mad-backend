from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from db.session import get_db
from schemas.userSchema import UserLogin, UserTokenData
from core.auth import create_access_token
from models.user import User
from schemas.core import StandardResponse

router = APIRouter()


@router.post("/login", response_model=StandardResponse)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login a user and return a JWT token.
    
    Args:
        user_credentials (UserLogin): The user's login credentials
        db (Session): The database session (injected)
    Returns:
        StandardResponse: The response containing the JWT token and message
    Errors:
        401 Unauthorized: If credentials are invalid        
        500 Internal Server Error: If an unexpected error occurs
    """
    try:
        user = await db.query(User).filter(User.username == user_credentials.username).first()
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