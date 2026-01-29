"""Service for Team business logic."""

from typing import List, Optional
from uuid import UUID

from app.modules.teams.models import Team, TeamMember
from app.modules.teams.repository import (
    TeamRepository,
    TeamMemberRepository
)
from app.modules.teams.schemas import (
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    TeamDetailResponse,
    TeamMemberCreate,
    TeamMemberResponse
)
from app.modules.departments.repository import DepartmentRepository
from app.modules.organizations.models import OrganizationRole
from app.modules.organizations.repository import UserOrganizationRepository
from app.shared.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException
)


class TeamService:
    """Service for team operations."""
    
    def __init__(
        self,
        team_repository: TeamRepository,
        team_member_repository: TeamMemberRepository,
        department_repository: DepartmentRepository,
        user_org_repository: UserOrganizationRepository
    ):
        self.team_repository = team_repository
        self.team_member_repository = team_member_repository
        self.department_repository = department_repository
        self.user_org_repository = user_org_repository
    
    def _check_permissions(self, user_id: UUID, org_id: UUID):
        """Check if user has required permissions."""
        role = self.user_org_repository.get_user_role(user_id, org_id)
        if not role or role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MANAGER]:
            raise ForbiddenException("You don't have permission to perform this action")
    
    def create_team(
        self,
        dept_id: UUID,
        team_data: TeamCreate,
        user_id: UUID
    ) -> TeamResponse:
        """Create a new team."""
        department = self.department_repository.get_by_uuid(dept_id)
        if not department:
            raise NotFoundException("Department", dept_id)
        
        self._check_permissions(user_id, department.organization_id)
        
        # Validate team lead if provided
        if team_data.team_lead_id:
            if not self.user_org_repository.is_member(
                team_data.team_lead_id, department.organization_id
            ):
                raise ValidationException("Team lead must be a member of the organization")
        
        # Create team
        team_dict = team_data.model_dump()
        team_dict["department_id"] = dept_id
        team = self.team_repository.create(team_dict)
        
        return TeamResponse.model_validate(team)
    
    def get_teams(
        self,
        dept_id: UUID,
        user_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[TeamResponse]:
        """Get all teams for a department."""
        department = self.department_repository.get_by_uuid(dept_id)
        if not department:
            raise NotFoundException("Department", dept_id)
        
        if not self.user_org_repository.is_member(user_id, department.organization_id):
            raise ForbiddenException("You don't have access to this department")
        
        teams = self.team_repository.get_by_department(dept_id, is_active)
        return [TeamResponse.model_validate(team) for team in teams]
    
    def get_team(self, team_id: UUID, user_id: UUID) -> TeamDetailResponse:
        """Get team by ID with details."""
        team = self.team_repository.get_by_uuid(team_id)
        if not team:
            raise NotFoundException("Team", team_id)
        
        department = self.department_repository.get_by_uuid(team.department_id)
        if not self.user_org_repository.is_member(user_id, department.organization_id):
            raise ForbiddenException("You don't have access to this team")
        
        # Get members
        members = self.team_member_repository.get_by_team(team_id)
        member_list = [
            TeamMemberResponse(
                id=member.id,
                team_id=member.team_id,
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at,
                user={
                    "id": str(member.user.id),
                    "email": member.user.email,
                    "first_name": member.user.first_name,
                    "last_name": member.user.last_name,
                    "full_name": member.user.full_name,
                    "avatar_url": member.user.avatar_url
                } if member.user else None
            )
            for member in members
        ]
        
        response = TeamDetailResponse.model_validate(team)
        response.members = member_list
        response.member_count = len(member_list)
        
        if team.team_lead:
            response.team_lead = {
                "id": str(team.team_lead.id),
                "email": team.team_lead.email,
                "first_name": team.team_lead.first_name,
                "last_name": team.team_lead.last_name,
                "full_name": team.team_lead.full_name
            }
        
        return response
    
    def update_team(
        self,
        team_id: UUID,
        team_data: TeamUpdate,
        user_id: UUID
    ) -> TeamResponse:
        """Update team."""
        team = self.team_repository.get_by_uuid(team_id)
        if not team:
            raise NotFoundException("Team", team_id)
        
        department = self.department_repository.get_by_uuid(team.department_id)
        self._check_permissions(user_id, department.organization_id)
        
        # Validate team lead if being updated
        if team_data.team_lead_id is not None:
            if team_data.team_lead_id:
                if not self.user_org_repository.is_member(
                    team_data.team_lead_id, department.organization_id
                ):
                    raise ValidationException("Team lead must be a member of the organization")
        
        # Update team
        update_dict = team_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(team, key, value)
        
        self.team_repository.db.commit()
        self.team_repository.db.refresh(team)
        
        return TeamResponse.model_validate(team)
    
    def delete_team(self, team_id: UUID, user_id: UUID) -> bool:
        """Delete team (soft delete)."""
        team = self.team_repository.get_by_uuid(team_id)
        if not team:
            raise NotFoundException("Team", team_id)
        
        department = self.department_repository.get_by_uuid(team.department_id)
        self._check_permissions(user_id, department.organization_id)
        
        # Soft delete
        team.is_active = False
        self.team_repository.db.commit()
        
        return True
    
    def add_team_member(
        self,
        team_id: UUID,
        member_data: TeamMemberCreate,
        user_id: UUID
    ) -> TeamMemberResponse:
        """Add member to team."""
        team = self.team_repository.get_by_uuid(team_id)
        if not team:
            raise NotFoundException("Team", team_id)
        
        department = self.department_repository.get_by_uuid(team.department_id)
        self._check_permissions(user_id, department.organization_id)
        
        # Validate user is member of organization
        if not self.user_org_repository.is_member(
            member_data.user_id, department.organization_id
        ):
            raise ValidationException("User must be a member of the organization")
        
        # Check if already a member
        if self.team_member_repository.is_member(team_id, member_data.user_id):
            raise ValidationException("User is already a member of this team")
        
        # Create team member
        member_dict = member_data.model_dump()
        member_dict["team_id"] = team_id
        member = self.team_member_repository.create(member_dict)
        
        # Refresh to get user relationship
        self.team_member_repository.db.refresh(member)
        if member.user:
            return TeamMemberResponse(
                id=member.id,
                team_id=member.team_id,
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at,
                user={
                    "id": str(member.user.id),
                    "email": member.user.email,
                    "first_name": member.user.first_name,
                    "last_name": member.user.last_name,
                    "full_name": member.user.full_name,
                    "avatar_url": member.user.avatar_url
                }
            )
        
        return TeamMemberResponse.model_validate(member)
    
    def remove_team_member(
        self,
        team_id: UUID,
        member_user_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove member from team."""
        team = self.team_repository.get_by_uuid(team_id)
        if not team:
            raise NotFoundException("Team", team_id)
        
        department = self.department_repository.get_by_uuid(team.department_id)
        self._check_permissions(user_id, department.organization_id)
        
        # Get team member
        member = self.team_member_repository.get_by_team_and_user(team_id, member_user_id)
        if not member:
            raise NotFoundException("Team member", member_user_id)
        
        # Delete member
        self.team_member_repository.db.delete(member)
        self.team_member_repository.db.commit()
        
        return True
    
    def get_team_members(
        self,
        team_id: UUID,
        user_id: UUID
    ) -> List[TeamMemberResponse]:
        """Get all members of a team."""
        team = self.team_repository.get_by_uuid(team_id)
        if not team:
            raise NotFoundException("Team", team_id)
        
        department = self.department_repository.get_by_uuid(team.department_id)
        if not self.user_org_repository.is_member(user_id, department.organization_id):
            raise ForbiddenException("You don't have access to this team")
        
        members = self.team_member_repository.get_by_team(team_id)
        return [
            TeamMemberResponse(
                id=member.id,
                team_id=member.team_id,
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at,
                user={
                    "id": str(member.user.id),
                    "email": member.user.email,
                    "first_name": member.user.first_name,
                    "last_name": member.user.last_name,
                    "full_name": member.user.full_name,
                    "avatar_url": member.user.avatar_url
                } if member.user else None
            )
            for member in members
        ]
