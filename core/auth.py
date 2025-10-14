from jose import jwt , JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends , HTTPException , status
from core.config import settings
from fastapi.security import OAuth2PasswordBearer


# get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token with expiration time.
    
    Args:
        data (dict): The payload data to encode in the token
        
    Returns:
        str: The encoded JWT token as a string
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def verify_user_token(token: str = Depends(oauth2_scheme)):
    """
    Verify and decode a JWT token to extract user information.
    
    Args:
        token (str): The JWT token from the Authorization header
        
    Returns:
        dict: The decoded token payload containing user information
        
    Raises:
        HTTPException: 401 Unauthorized if token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


async def verify_admin_token(payload: dict = Depends(verify_user_token)):
    """
    Verify that the authenticated user has admin privileges.
    
    Args:
        payload (dict): The decoded JWT payload from verify_user_token
        
    Returns:
        dict: The same payload if user has admin privileges
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't have admin privileges
    """
    if not payload.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges to access this resource"
        )
    return payload
  