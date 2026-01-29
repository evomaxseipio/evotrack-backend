"""Dependencies for user module."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.organizations.dependencies import get_user_organization_repository
from app.modules.organizations.repository import UserOrganizationRepository
from app.modules.users.service import UserService


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    user_org_repository: UserOrganizationRepository = Depends(get_user_organization_repository)
) -> UserService:
    """Get user service instance."""
    return UserService(user_repository, user_org_repository)


def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    Get current authenticated user.
    
    This dependency extracts user ID from JWT and fetches full user object.
    """
    return user_service.get_user(user_id)


# Type aliases for cleaner code
CurrentUser = Annotated[User, Depends(get_current_user)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
