from pydantic import BaseModel, EmailStr, ConfigDict

class UserLogin(BaseModel):
    """
    User login request model.
    
    Used for authenticating users with email and password.
    Endpoint: POST /users/login
    """
    email: EmailStr
    password: str
    

class UserTokenData(BaseModel):
    """
    JWT token payload data model.
    
    Contains user information extracted from decoded JWT tokens.
    Used internally for authentication and authorization.
    """
    username: str | None = None
    user_id: int | None = None
    is_admin: bool | None = None


class UserFetch(BaseModel):
    """
    User fetch request model for admin-only getUser endpoint.
    
    Contains the user ID to retrieve specific user metadata.
    Endpoint: GET /users/getUser/{user_id} (Admin only)
    
    Used by administrators to fetch detailed user information by ID.
    """
    id: int


class UserResponse(BaseModel):
    """
    User data response model.
    
    Returns public user information (excludes sensitive data like password).
    Used in API responses for user-related endpoints.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class SignupRequest(BaseModel):
    """
    Request model for signing up a new user.
    """
    email: EmailStr
    password: str
    full_name: str | None = None


class VerifyOTP(BaseModel):
    """
    Model for verifying an OTP/token sent to user's email.
    """
    email: EmailStr
    token: str

