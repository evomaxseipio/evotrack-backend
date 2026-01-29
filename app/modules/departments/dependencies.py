"""Dependencies for departments module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.departments.repository import DepartmentRepository
from app.modules.departments.service import DepartmentService
from app.modules.teams.repository import TeamRepository
from app.modules.organizations.repository import UserOrganizationRepository
from app.modules.users.repository import UserRepository


def get_department_repository(db: Session = Depends(get_db)) -> DepartmentRepository:
    """Get department repository instance."""
    return DepartmentRepository(db)


def get_team_repository(db: Session = Depends(get_db)) -> TeamRepository:
    """Get team repository instance."""
    return TeamRepository(db)


def get_user_organization_repository(db: Session = Depends(get_db)) -> UserOrganizationRepository:
    """Get user-organization repository instance."""
    return UserOrganizationRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


def get_department_service(
    dept_repository: DepartmentRepository = Depends(get_department_repository),
    team_repository: TeamRepository = Depends(get_team_repository),
    user_org_repository: UserOrganizationRepository = Depends(get_user_organization_repository),
    user_repository: UserRepository = Depends(get_user_repository)
) -> DepartmentService:
    """Get department service instance."""
    return DepartmentService(
        dept_repository,
        team_repository,
        user_org_repository,
        user_repository
    )
