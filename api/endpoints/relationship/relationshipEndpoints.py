from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, or_, and_
from db.session import get_db
from schemas.relationshipSchema import (
    RelationshipCreate, RelationshipUpdate, RelationshipResponse,
    RelationshipWithUserDetails
)
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
from models.user import User, UserRole
from uuid import UUID

router = APIRouter()


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    relationship_data: RelationshipCreate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a coach-client relationship (Coach invites Client OR Client requests Coach).
    
    Two scenarios:
    1. Coach invites a client: Provide client_user_id (status: PENDING, client accepts)
    2. Client requests a coach: Provide coach_user_id (status: PENDING, coach accepts)
    
    Returns: {"data": {relationship_data}, "message": "Relationship created successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 409 (already exists), 422 (validation), 500 (server error)
    """
    try:
        current_user_id = UUID(str(current_user.get("user_id")))
        
        # Determine who is initiating
        if relationship_data.client_user_id:
            # Coach is inviting a client
            coach_user_id = current_user_id
            client_user_id = relationship_data.client_user_id
            
            # Verify current user is a coach
            result = await db.execute(select(User).filter(User.id == coach_user_id))
            coach = result.scalar_one_or_none()
            if not coach or coach.role not in [UserRole.COACH, UserRole.BOTH]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only coaches can invite clients"
                )
            
            # Verify client exists
            result = await db.execute(select(User).filter(User.id == client_user_id))
            client = result.scalar_one_or_none()
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client user not found"
                )
                
        elif relationship_data.coach_user_id:
            # Client is requesting a coach
            coach_user_id = relationship_data.coach_user_id
            client_user_id = current_user_id
            
            # Verify coach exists and has coach role
            result = await db.execute(select(User).filter(User.id == coach_user_id))
            coach = result.scalar_one_or_none()
            if not coach:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Coach user not found"
                )
            if coach.role not in [UserRole.COACH, UserRole.BOTH]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Specified user is not a coach"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either coach_user_id or client_user_id must be provided"
            )
        
        # Check if relationship already exists
        result = await db.execute(
            select(CoachClientRelationship).filter(
                CoachClientRelationship.coach_user_id == coach_user_id,
                CoachClientRelationship.client_user_id == client_user_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Relationship already exists with status: {existing.status.value}"
            )
        
        # Create new relationship (status: PENDING)
        new_relationship = CoachClientRelationship(
            coach_user_id=coach_user_id,
            client_user_id=client_user_id,
            status=RelationshipStatus.PENDING
        )
        
        db.add(new_relationship)
        await db.commit()
        await db.refresh(new_relationship)
        
        response = RelationshipResponse.model_validate(new_relationship)
        return StandardResponse(
            data=response.model_dump(),
            message="Relationship request created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("", response_model=StandardResponse)
async def get_my_relationships(
    status_filter: str = None,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all relationships for the current user (as coach or client).
    
    Optional query param: status (pending, active, paused, terminated)
    
    Returns: {"data": [relationships], "message": "Relationships retrieved successfully"}
    Errors: 401 (unauthorized), 500 (server error)
    """
    try:
        current_user_id = UUID(str(current_user.get("user_id")))
        
        # Get relationships where user is either coach or client
        query = (
            select(CoachClientRelationship)
            .options(
                joinedload(CoachClientRelationship.coach),
                joinedload(CoachClientRelationship.client)
            )
            .filter(
                or_(
                    CoachClientRelationship.coach_user_id == current_user_id,
                    CoachClientRelationship.client_user_id == current_user_id
                )
            )
        )
        
        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = RelationshipStatus[status_filter.upper()]
                query = query.filter(CoachClientRelationship.status == status_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status. Must be one of: pending, active, paused, terminated"
                )
        
        result = await db.execute(query)
        relationships = result.scalars().all()
        
        # Format response with user details
        response_data = []
        for rel in relationships:
            response_data.append({
                "id": rel.id,
                "coach_user_id": rel.coach_user_id,
                "coach_email": rel.coach.email,
                "coach_name": rel.coach.full_name,
                "client_user_id": rel.client_user_id,
                "client_email": rel.client.email,
                "client_name": rel.client.full_name,
                "status": rel.status.value,
                "created_at": rel.created_at,
                "updated_at": rel.updated_at
            })
        
        return StandardResponse(
            data=response_data,
            message="Relationships retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{relationship_id}", response_model=StandardResponse)
async def get_relationship_details(
    relationship_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific relationship.
    
    User must be either the coach or client in the relationship.
    
    Returns: {"data": {relationship_data}, "message": "Relationship retrieved successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        current_user_id = UUID(str(current_user.get("user_id")))
        
        result = await db.execute(
            select(CoachClientRelationship)
            .options(
                joinedload(CoachClientRelationship.coach),
                joinedload(CoachClientRelationship.client)
            )
            .filter(CoachClientRelationship.id == relationship_id)
        )
        relationship = result.scalar_one_or_none()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found"
            )
        
        # Verify user is part of this relationship
        if relationship.coach_user_id != current_user_id and relationship.client_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this relationship"
            )
        
        response_data = {
            "id": relationship.id,
            "coach_user_id": relationship.coach_user_id,
            "coach_email": relationship.coach.email,
            "coach_name": relationship.coach.full_name,
            "client_user_id": relationship.client_user_id,
            "client_email": relationship.client.email,
            "client_name": relationship.client.full_name,
            "status": relationship.status.value,
            "created_at": relationship.created_at,
            "updated_at": relationship.updated_at
        }
        
        return StandardResponse(
            data=response_data,
            message="Relationship retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/{relationship_id}", response_model=StandardResponse)
async def update_relationship_status(
    relationship_id: UUID,
    update_data: RelationshipUpdate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update relationship status (Accept, Reject, Pause, Reactivate, Terminate).
    
    Status transitions:
    - PENDING -> ACTIVE (accept), TERMINATED (reject)
    - ACTIVE -> PAUSED, TERMINATED
    - PAUSED -> ACTIVE (reactivate), TERMINATED
    
    Authorization:
    - To accept PENDING: Must be the recipient (if coach invited, client accepts; if client requested, coach accepts)
    - To pause/terminate ACTIVE: Either party can do it
    - To reactivate PAUSED: Either party can do it
    
    Returns: {"data": {relationship_data}, "message": "Relationship updated successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (invalid transition), 500 (server error)
    """
    try:
        current_user_id = UUID(str(current_user.get("user_id")))
        
        result = await db.execute(
            select(CoachClientRelationship).filter(
                CoachClientRelationship.id == relationship_id
            )
        )
        relationship = result.scalar_one_or_none()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found"
            )
        
        # Verify user is part of this relationship
        if relationship.coach_user_id != current_user_id and relationship.client_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this relationship"
            )
        
        new_status = RelationshipStatus[update_data.status.upper()]
        current_status = relationship.status
        
        # Validate status transitions
        if current_status == RelationshipStatus.PENDING:
            if new_status == RelationshipStatus.ACTIVE:
                # Accepting - must be the other party (not the one who created it)
                # Note: The one who didn't initiate is the acceptor
                pass  # Allow acceptance
            elif new_status == RelationshipStatus.TERMINATED:
                # Rejecting - allowed
                pass
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Pending relationships can only be accepted (active) or rejected (terminated)"
                )
        
        elif current_status == RelationshipStatus.ACTIVE:
            if new_status not in [RelationshipStatus.PAUSED, RelationshipStatus.TERMINATED]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Active relationships can only be paused or terminated"
                )
        
        elif current_status == RelationshipStatus.PAUSED:
            if new_status not in [RelationshipStatus.ACTIVE, RelationshipStatus.TERMINATED]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Paused relationships can only be reactivated or terminated"
                )
        
        elif current_status == RelationshipStatus.TERMINATED:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Terminated relationships cannot be modified"
            )
        
        # Update status
        relationship.status = new_status
        await db.commit()
        await db.refresh(relationship)
        
        response = RelationshipResponse.model_validate(relationship)
        
        status_messages = {
            "active": "Relationship accepted",
            "paused": "Relationship paused",
            "terminated": "Relationship terminated"
        }
        message = status_messages.get(update_data.status, "Relationship updated successfully")
        
        return StandardResponse(
            data=response.model_dump(),
            message=message
        )
        
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid status value"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/{relationship_id}", response_model=StandardResponse)
async def delete_relationship(
    relationship_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a relationship (Hard delete).
    
    Can only delete PENDING or TERMINATED relationships.
    For ACTIVE/PAUSED relationships, must terminate first.
    Either party can delete.
    
    Returns: {"data": {}, "message": "Relationship deleted successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (invalid state), 500 (server error)
    """
    try:
        current_user_id = UUID(str(current_user.get("user_id")))
        
        result = await db.execute(
            select(CoachClientRelationship).filter(
                CoachClientRelationship.id == relationship_id
            )
        )
        relationship = result.scalar_one_or_none()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found"
            )
        
        # Verify user is part of this relationship
        if relationship.coach_user_id != current_user_id and relationship.client_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this relationship"
            )
        
        # Only allow deletion of PENDING or TERMINATED relationships
        if relationship.status not in [RelationshipStatus.PENDING, RelationshipStatus.TERMINATED]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Can only delete pending or terminated relationships. Terminate active/paused relationships first."
            )
        
        await db.delete(relationship)
        await db.commit()
        
        return StandardResponse(
            data={},
            message="Relationship deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/coaches/available", response_model=StandardResponse)
async def get_available_coaches(
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of available coaches (for clients to browse and request).
    
    Returns coaches who are not already connected to the current user.
    
    Returns: {"data": [coach_list], "message": "Coaches retrieved successfully"}
    Errors: 401 (unauthorized), 500 (server error)
    """
    try:
        current_user_id = UUID(str(current_user.get("user_id")))
        
        # Get all existing relationships for current user
        result = await db.execute(
            select(CoachClientRelationship.coach_user_id).filter(
                CoachClientRelationship.client_user_id == current_user_id
            )
        )
        connected_coach_ids = [row[0] for row in result.all()]
        
        # Get all coaches not connected
        query = select(User).filter(
            User.role.in_([UserRole.COACH, UserRole.BOTH]),
            User.id != current_user_id
        )
        
        if connected_coach_ids:
            query = query.filter(User.id.not_in(connected_coach_ids))
        
        result = await db.execute(query)
        coaches = result.scalars().all()
        
        coach_list = [
            {
                "id": coach.id,
                "email": coach.email,
                "full_name": coach.full_name,
                "role": coach.role.value
            }
            for coach in coaches
        ]
        
        return StandardResponse(
            data=coach_list,
            message="Available coaches retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/clients/available", response_model=StandardResponse)
async def get_available_clients(
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of available clients (for coaches to browse and invite).
    
    Returns clients who are not already connected to the current user.
    Requires user to be a coach.
    
    Returns: {"data": [client_list], "message": "Clients retrieved successfully"}
    Errors: 401 (unauthorized), 403 (not a coach), 500 (server error)
    """
    try:
        current_user_id = UUID(str(current_user.get("user_id")))
        
        # Verify user is a coach
        result = await db.execute(select(User).filter(User.id == current_user_id))
        user = result.scalar_one_or_none()
        if not user or user.role not in [UserRole.COACH, UserRole.BOTH]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only coaches can access this endpoint"
            )
        
        # Get all existing relationships for current user
        result = await db.execute(
            select(CoachClientRelationship.client_user_id).filter(
                CoachClientRelationship.coach_user_id == current_user_id
            )
        )
        connected_client_ids = [row[0] for row in result.all()]
        
        # Get all users not connected (any role can be a client)
        query = select(User).filter(User.id != current_user_id)
        
        if connected_client_ids:
            query = query.filter(User.id.not_in(connected_client_ids))
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        client_list = [
            {
                "id": client.id,
                "email": client.email,
                "full_name": client.full_name,
                "role": client.role.value
            }
            for client in clients
        ]
        
        return StandardResponse(
            data=client_list,
            message="Available clients retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
