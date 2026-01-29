"""Team API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.auth.dependencies import CurrentUser
from app.modules.teams.dependencies import get_team_service
from app.modules.teams.service import TeamService
from app.modules.teams.schemas import (
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    TeamDetailResponse,
    TeamMemberCreate,
    TeamMemberResponse
)
from app.shared.responses import MessageResponse

router = APIRouter()


# Team Endpoints
@router.post(
    "/departments/{dept_id}/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create team",
    description="Create a new team in a department"
)
def create_team(
    dept_id: UUID,
    team_data: TeamCreate,
    current_user: CurrentUser,
    team_service: TeamService = Depends(get_team_service)
) -> TeamResponse:
    """
    Create a new team.
    
    **Requires admin, owner, or manager role.**
    
    **Request Body:**
    - **name**: Team name (required)
    - **description**: Team description (optional)
    - **team_lead_id**: Team lead user ID (optional)
    
    **Returns:**
    - Created team
    
    **Errors:**
    - **403**: Insufficient permissions
    - **404**: Department not found
    - **400**: Invalid team lead
    """
    return team_service.create_team(dept_id, team_data, current_user.id)


@router.get(
    "/departments/{dept_id}/teams",
    response_model=List[TeamResponse],
    summary="List teams",
    description="Get all teams for a department"
)
def list_teams(
    dept_id: UUID,
    current_user: CurrentUser,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    team_service: TeamService = Depends(get_team_service)
) -> List[TeamResponse]:
    """
    List all teams for a department.
    
    **Requires organization membership.**
    
    **Query Parameters:**
    - **is_active**: Filter by active status (optional)
    
    **Returns:**
    - List of teams
    
    **Errors:**
    - **404**: Department not found
    - **403**: Not a member of organization
    """
    return team_service.get_teams(dept_id, current_user.id, is_active)


@router.get(
    "/teams/{team_id}",
    response_model=TeamDetailResponse,
    summary="Get team",
    description="Get team details with members"
)
def get_team(
    team_id: UUID,
    current_user: CurrentUser,
    team_service: TeamService = Depends(get_team_service)
) -> TeamDetailResponse:
    """
    Get team by ID with full details.
    
    **Requires organization membership.**
    
    **Returns:**
    - Team details
    - List of team members
    - Team lead info
    
    **Errors:**
    - **404**: Team not found
    - **403**: Not a member of organization
    """
    return team_service.get_team(team_id, current_user.id)


@router.put(
    "/teams/{team_id}",
    response_model=TeamResponse,
    summary="Update team",
    description="Update team details"
)
def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: CurrentUser,
    team_service: TeamService = Depends(get_team_service)
) -> TeamResponse:
    """
    Update team.
    
    **Requires admin, owner, or manager role.**
    
    **Request Body:**
    - All fields optional
    
    **Returns:**
    - Updated team
    
    **Errors:**
    - **404**: Team not found
    - **403**: Insufficient permissions
    """
    return team_service.update_team(team_id, team_data, current_user.id)


@router.delete(
    "/teams/{team_id}",
    response_model=MessageResponse,
    summary="Delete team",
    description="Delete team (soft delete)"
)
def delete_team(
    team_id: UUID,
    current_user: CurrentUser,
    team_service: TeamService = Depends(get_team_service)
) -> MessageResponse:
    """
    Delete team (soft delete).
    
    **Requires admin, owner, or manager role.**
    
    **Returns:**
    - Success message
    
    **Errors:**
    - **404**: Team not found
    - **403**: Insufficient permissions
    """
    team_service.delete_team(team_id, current_user.id)
    return MessageResponse(
        success=True,
        message="Team deleted successfully"
    )


@router.post(
    "/teams/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add team member",
    description="Add a member to a team"
)
def add_team_member(
    team_id: UUID,
    member_data: TeamMemberCreate,
    current_user: CurrentUser,
    team_service: TeamService = Depends(get_team_service)
) -> TeamMemberResponse:
    """
    Add member to team.
    
    **Requires admin, owner, or manager role.**
    
    **Request Body:**
    - **user_id**: User ID to add to team (required)
    - **role**: Role within the team (optional)
    
    **Returns:**
    - Created team member
    
    **Errors:**
    - **403**: Insufficient permissions
    - **404**: Team not found
    - **400**: User not member of organization or already a member
    """
    return team_service.add_team_member(team_id, member_data, current_user.id)


@router.delete(
    "/teams/{team_id}/members/{user_id}",
    response_model=MessageResponse,
    summary="Remove team member",
    description="Remove a member from a team"
)
def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    team_service: TeamService = Depends(get_team_service)
) -> MessageResponse:
    """
    Remove member from team.
    
    **Requires admin, owner, or manager role.**
    
    **Returns:**
    - Success message
    
    **Errors:**
    - **403**: Insufficient permissions
    - **404**: Team or member not found
    """
    team_service.remove_team_member(team_id, user_id, current_user.id)
    return MessageResponse(
        success=True,
        message="Team member removed successfully"
    )


@router.get(
    "/teams/{team_id}/members",
    response_model=List[TeamMemberResponse],
    summary="Get team members",
    description="Get all members of a team"
)
def get_team_members(
    team_id: UUID,
    current_user: CurrentUser,
    team_service: TeamService = Depends(get_team_service)
) -> List[TeamMemberResponse]:
    """
    Get all members of a team.
    
    **Requires organization membership.**
    
    **Returns:**
    - List of team members with user details
    
    **Errors:**
    - **404**: Team not found
    - **403**: Not a member of organization
    """
    return team_service.get_team_members(team_id, current_user.id)
