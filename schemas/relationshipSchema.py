from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class RelationshipCreate(BaseModel):
    """
    Request model for creating a coach-client relationship.
    
    Can be initiated by either:
    - Coach inviting a client (provide client_user_id)
    - Client requesting a coach (provide coach_user_id)
    
    Endpoint: POST /relationships
    """
    coach_user_id: Optional[UUID] = None
    client_user_id: Optional[UUID] = None
    
    @field_validator('coach_user_id', 'client_user_id')
    @classmethod
    def validate_one_id_provided(cls, v, info):
        """Ensure exactly one ID is provided."""
        data = info.data
        coach_id = data.get('coach_user_id') if 'coach_user_id' in data else v if info.field_name == 'coach_user_id' else None
        client_id = data.get('client_user_id') if 'client_user_id' in data else v if info.field_name == 'client_user_id' else None
        
        # Only validate after both fields have been processed
        if info.field_name == 'client_user_id':
            if not coach_id and not client_id:
                raise ValueError('Either coach_user_id or client_user_id must be provided')
            if coach_id and client_id:
                raise ValueError('Only one of coach_user_id or client_user_id should be provided')
        
        return v


class RelationshipUpdate(BaseModel):
    """
    Request model for updating a relationship status.
    
    Used to accept, reject, pause, reactivate, or terminate relationships.
    
    Endpoint: PUT /relationships/{relationship_id}
    """
    status: str  # "pending", "active", "paused", "terminated"
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Ensure status is valid."""
        valid_statuses = ['pending', 'active', 'paused', 'terminated']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v.lower()


class RelationshipResponse(BaseModel):
    """
    Response model for coach-client relationship data.
    
    Returns relationship information including user details.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    coach_user_id: UUID
    client_user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class RelationshipWithUserDetails(BaseModel):
    """
    Enhanced response model including user information.
    
    Provides coach and client names/emails for frontend display.
    """
    id: UUID
    coach_user_id: UUID
    coach_email: str
    coach_name: str
    client_user_id: UUID
    client_email: str
    client_name: str
    status: str
    created_at: datetime
    updated_at: datetime
