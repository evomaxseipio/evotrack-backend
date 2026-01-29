"""Dependencies for teams module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.teams.repository import (
    TeamRepository,
    TeamMemberRepository
)
from app.modules.teams.service import TeamService
from app.modules.departments.repository import DepartmentRepository
from app.modules.organizations.repository import UserOrganizationRepository


def get_team_repository(db: Session = Depends(get_db)) -> TeamRepository:
    """Get team repository instance."""
    return TeamRepository(db)


def get_team_member_repository(db: Session = Depends(get_db)) -> TeamMemberRepository:
    """Get team member repository instance."""
    return TeamMemberRepository(db)


def get_department_repository(db: Session = Depends(get_db)) -> DepartmentRepository:
    """Get department repository instance."""
    return DepartmentRepository(db)


def get_user_organization_repository(db: Session = Depends(get_db)) -> UserOrganizationRepository:
    """Get user-organization repository instance."""
    return UserOrganizationRepository(db)


def get_team_service(
    team_repository: TeamRepository = Depends(get_team_repository),
    team_member_repository: TeamMemberRepository = Depends(get_team_member_repository),
    department_repository: DepartmentRepository = Depends(get_department_repository),
    user_org_repository: UserOrganizationRepository = Depends(get_user_organization_repository)
) -> TeamService:
    """Get team service instance."""
    return TeamService(
        team_repository,
        team_member_repository,
        department_repository,
        user_org_repository
    )
