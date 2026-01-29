"""Organization service with business logic."""

from typing import List
from uuid import UUID

from app.modules.organizations.models import OrganizationRole
from app.modules.organizations.repository import (
    OrganizationRepository,
    UserOrganizationRepository
)
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    OrganizationListResponse,
    OrganizationStats
)
from app.shared.exceptions import NotFoundException, ForbiddenException, AlreadyExistsException
from app.shared.utils import generate_slug


class OrganizationService:
    """Service for organization operations."""
    
    def __init__(
        self,
        organization_repository: OrganizationRepository,
        user_org_repository: UserOrganizationRepository
    ):
        self.organization_repository = organization_repository
        self.user_org_repository = user_org_repository
    
    def create_organization(
        self,
        org_data: OrganizationCreate,
        owner_id: UUID
    ) -> OrganizationResponse:
        """
        Create new organization and assign creator as owner.
        
        Args:
            org_data: Organization creation data
            owner_id: User ID of the creator (will be owner)
        
        Returns:
            Created organization
        
        Raises:
            AlreadyExistsException: If tax_id already exists
        """
        # Validate tax_id uniqueness
        if self.organization_repository.tax_id_exists(org_data.tax_id):
            raise AlreadyExistsException("Organization", "tax_id", org_data.tax_id)
        
        # Generate slug if not provided
        org_dict = org_data.model_dump()
        if not org_dict.get("slug"):
            org_dict["slug"] = generate_slug(org_data.name)
        
        # Create organization
        organization = self.organization_repository.create(org_dict)
        
        # Create user-organization relationship with owner role
        self.user_org_repository.create_membership(
            user_id=owner_id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER
        )
        
        return OrganizationResponse.model_validate(organization)
    
    def get_organization(self, org_id: UUID, user_id: UUID) -> OrganizationResponse:
        """
        Get organization by ID.
        
        Args:
            org_id: Organization ID
            user_id: User ID (for permission check)
        
        Returns:
            Organization data
        
        Raises:
            NotFoundException: If organization not found
            ForbiddenException: If user doesn't have access
        """
        organization = self.organization_repository.get_by_uuid(org_id)
        
        if not organization:
            raise NotFoundException("Organization", org_id)
        
        # Check if user is member
        if not self.user_org_repository.is_member(user_id, org_id):
            raise ForbiddenException("You don't have access to this organization")
        
        return OrganizationResponse.model_validate(organization)
    
    def get_user_organizations(self, user_id: UUID) -> List[OrganizationListResponse]:
        """
        Get all organizations for a user with user role and stats.
        
        Args:
            user_id: User ID
        
        Returns:
            List of organizations with user role and statistics
        """
        # Get organizations with roles
        orgs_with_roles = self.organization_repository.get_user_organizations_with_roles(user_id)
        
        result = []
        for organization, role in orgs_with_roles:
            # Get statistics for this organization
            stats_dict = self.organization_repository.get_organization_stats(organization.id)
            
            # Create response object
            org_dict = {
                "id": organization.id,
                "name": organization.name,
                "slug": organization.slug,
                "tax_id": organization.tax_id,
                "timezone": organization.timezone,
                "currency_code": organization.currency_code,
                "logo_url": organization.logo_url,
                "is_active": organization.is_active,
                "user_role": role.value,  # Convert enum to string value
                "stats": OrganizationStats(**stats_dict),
                "created_at": organization.created_at,
                "updated_at": organization.updated_at
            }
            result.append(OrganizationListResponse(**org_dict))
        
        return result
    
    def update_organization(
        self,
        org_id: UUID,
        org_data: OrganizationUpdate,
        user_id: UUID
    ) -> OrganizationResponse:
        """
        Update organization.
        
        Args:
            org_id: Organization ID
            org_data: Update data
            user_id: User ID (for permission check)
        
        Returns:
            Updated organization
        
        Raises:
            NotFoundException: If organization not found
            ForbiddenException: If user doesn't have admin/owner role
        """
        # Check permissions (only admin/owner can update)
        role = self.user_org_repository.get_user_role(user_id, org_id)
        if role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            raise ForbiddenException("You don't have permission to update this organization")
        
        # Get organization
        organization = self.organization_repository.get_by_uuid(org_id)
        if not organization:
            raise NotFoundException("Organization", org_id)
        
        # Update organization
        update_dict = org_data.model_dump(exclude_unset=True)
        
        # Validate tax_id uniqueness if being updated
        if "tax_id" in update_dict and update_dict["tax_id"] != organization.tax_id:
            if self.organization_repository.tax_id_exists(update_dict["tax_id"]):
                raise AlreadyExistsException("Organization", "tax_id", update_dict["tax_id"])
        
        for key, value in update_dict.items():
            setattr(organization, key, value)
        
        self.organization_repository.db.commit()
        self.organization_repository.db.refresh(organization)
        
        return OrganizationResponse.model_validate(organization)
    
    def delete_organization(self, org_id: UUID, user_id: UUID) -> bool:
        """
        Delete organization (soft delete).
        
        Args:
            org_id: Organization ID
            user_id: User ID (for permission check)
        
        Returns:
            True if deleted
        
        Raises:
            NotFoundException: If organization not found
            ForbiddenException: If user is not owner
        """
        # Check permissions (only owner can delete)
        role = self.user_org_repository.get_user_role(user_id, org_id)
        if role != OrganizationRole.OWNER:
            raise ForbiddenException("Only organization owners can delete organizations")
        
        # Get organization
        organization = self.organization_repository.get_by_uuid(org_id)
        if not organization:
            raise NotFoundException("Organization", org_id)
        
        # Soft delete
        organization.is_active = False
        self.organization_repository.db.commit()
        
        return True