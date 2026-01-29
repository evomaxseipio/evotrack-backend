"""Repository for Organization database operations."""

from typing import List, Optional, Tuple, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.modules.organizations.models import Organization, UserOrganization, OrganizationRole
from app.shared.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization model."""
    
    def __init__(self, db: Session):
        super().__init__(Organization, db)
    
    def get_by_uuid(self, org_id: UUID) -> Optional[Organization]:
        """Get organization by UUID."""
        return self.db.query(Organization).filter(Organization.id == org_id).first()
    
    def tax_id_exists(self, tax_id: str) -> bool:
        """
        Check if tax_id already exists.
        
        Args:
            tax_id: Tax identification number to check
        
        Returns:
            True if tax_id exists, False otherwise
        """
        return self.db.query(Organization).filter(Organization.tax_id == tax_id.strip()).count() > 0
    
    def get_user_organizations(self, user_id: UUID) -> List[Organization]:
        """Get all organizations for a user."""
        return (
            self.db.query(Organization)
            .join(UserOrganization)
            .filter(UserOrganization.user_id == user_id)
            .filter(UserOrganization.is_active == True)
            .filter(Organization.is_active == True)
            .all()
        )
    
    def get_user_organizations_with_roles(self, user_id: UUID) -> List[Tuple[Organization, OrganizationRole]]:
        """
        Get all organizations for a user with their roles.
        
        Args:
            user_id: User UUID
        
        Returns:
            List of tuples (Organization, OrganizationRole) ordered by membership creation date
        """
        results = (
            self.db.query(Organization, UserOrganization.role)
            .join(UserOrganization, Organization.id == UserOrganization.organization_id)
            .filter(UserOrganization.user_id == user_id)
            .filter(UserOrganization.is_active == True)
            .filter(Organization.is_active == True)
            .order_by(UserOrganization.created_at.asc())
            .all()
        )
        return [(org, role) for org, role in results]
    
    def get_active_organizations(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all active organizations."""
        return (
            self.db.query(Organization)
            .filter(Organization.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_organization_stats(self, org_id: UUID) -> Dict[str, int]:
        """
        Get statistics for an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Dictionary with users_count, departments_count, and projects_count
        """
        # Import here to avoid circular imports
        from app.modules.departments.models import Department
        
        # Count active users in organization
        users_count = (
            self.db.query(func.count(UserOrganization.id))
            .filter(UserOrganization.organization_id == org_id)
            .filter(UserOrganization.is_active == True)
            .scalar() or 0
        )
        
        # Count active departments in organization
        departments_count = (
            self.db.query(func.count(Department.id))
            .filter(Department.organization_id == org_id)
            .filter(Department.is_active == True)
            .scalar() or 0
        )
        
        # Projects count - for now return 0, can be updated when projects module is implemented
        # Try to import Project model if it exists
        projects_count = 0
        try:
            from app.modules.projects.models import Project
            # Check if Project has organization_id attribute
            if hasattr(Project, 'organization_id'):
                query = self.db.query(func.count(Project.id)).filter(Project.organization_id == org_id)
                # Add is_active filter if it exists
                if hasattr(Project, 'is_active'):
                    query = query.filter(Project.is_active == True)
                projects_count = query.scalar() or 0
        except (ImportError, AttributeError):
            # Projects module not implemented yet or model structure differs
            pass
        
        return {
            "users_count": users_count,
            "departments_count": departments_count,
            "projects_count": projects_count
        }


class UserOrganizationRepository(BaseRepository[UserOrganization]):
    """Repository for UserOrganization model."""
    
    def __init__(self, db: Session):
        super().__init__(UserOrganization, db)
    
    def create_membership(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: OrganizationRole
    ) -> UserOrganization:
        """Create user-organization membership."""
        membership = UserOrganization(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            is_active=True
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership
    
    def get_user_role(self, user_id: UUID, organization_id: UUID) -> Optional[OrganizationRole]:
        """Get user's role in organization."""
        membership = (
            self.db.query(UserOrganization)
            .filter(UserOrganization.user_id == user_id)
            .filter(UserOrganization.organization_id == organization_id)
            .filter(UserOrganization.is_active == True)
            .first()
        )
        return membership.role if membership else None
    
    def is_member(self, user_id: UUID, organization_id: UUID) -> bool:
        """Check if user is member of organization."""
        return (
            self.db.query(UserOrganization)
            .filter(UserOrganization.user_id == user_id)
            .filter(UserOrganization.organization_id == organization_id)
            .filter(UserOrganization.is_active == True)
            .count() > 0
        )