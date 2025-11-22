from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer
from uuid import UUID
from models.user import UserRole

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
    user_id: UUID | None = None
    email: str | None = None
    full_name: str | None = None
    role: str | None = None  # "coach", "client", or "both"
    is_activated: bool | None = None
    
    @field_serializer('user_id')
    def serialize_user_id(self, user_id: UUID | None, _info):
        """Convert UUID to string for JSON serialization."""
        return str(user_id) if user_id else None


class UserFetch(BaseModel):
    """
    User fetch request model for admin-only getUser endpoint.
    
    Contains the user ID to retrieve specific user metadata.
    Endpoint: GET /users/getUser/{user_id} (Admin only)
    
    Used by administrators to fetch detailed user information by ID.
    """
    id: UUID


class UserResponse(BaseModel):
    """
    User data response model.
    
    Returns public user information (excludes sensitive data like password).
    Used in API responses for user-related endpoints.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole


class SignupRequest(BaseModel):
    """
    Request model for signing up a new user.
    """
    email: EmailStr
    password: str
    full_name: str | None = None
    role: UserRole = UserRole.CLIENT


class VerifyOTP(BaseModel):
    """
    Model for verifying an OTP/token sent to user's email.
    """
    email: EmailStr
    token: str

