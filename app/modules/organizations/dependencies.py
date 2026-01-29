"""Dependencies for organizations module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.organizations.repository import (
    OrganizationRepository,
    UserOrganizationRepository
)
from app.modules.organizations.service import OrganizationService
from app.modules.organizations.invitation_service import InvitationService
from app.modules.users.repository import UserRepository


def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    """Get organization repository instance."""
    return OrganizationRepository(db)


def get_user_organization_repository(db: Session = Depends(get_db)) -> UserOrganizationRepository:
    """Get user-organization repository instance."""
    return UserOrganizationRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


def get_organization_service(
    org_repository: OrganizationRepository = Depends(get_organization_repository),
    user_org_repository: UserOrganizationRepository = Depends(get_user_organization_repository)
) -> OrganizationService:
    """Get organization service instance."""
    return OrganizationService(org_repository, user_org_repository)


def get_invitation_service(
    db: Session = Depends(get_db),
    org_repository: OrganizationRepository = Depends(get_organization_repository),
    user_org_repository: UserOrganizationRepository = Depends(get_user_organization_repository),
    user_repository: UserRepository = Depends(get_user_repository)
) -> InvitationService:
    """Get invitation service instance."""
    return InvitationService(db, org_repository, user_org_repository, user_repository)