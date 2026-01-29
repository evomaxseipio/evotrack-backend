"""Invitation service for organization membership."""

from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.email import EmailService
from app.modules.organizations.models import (
    Invitation,
    InvitationStatus,
    OrganizationRole,
    UserOrganization
)
from app.modules.organizations.repository import (
    OrganizationRepository,
    UserOrganizationRepository
)
from app.modules.organizations.invitation_schemas import (
    InvitationCreate,
    InvitationResponse,
    MemberResponse,
    UpdateMemberRole,
    BulkInvitationCreate,
    BulkInvitationResponse,
    BulkInvitationError
)
from app.modules.users.repository import UserRepository
from app.shared.exceptions import (
    NotFoundException,
    ForbiddenException,
    AlreadyExistsException,
    ValidationException
)


class InvitationService:
    """Service for managing organization invitations."""
    
    def __init__(
        self,
        db: Session,
        org_repository: OrganizationRepository,
        user_org_repository: UserOrganizationRepository,
        user_repository: UserRepository
    ):
        self.db = db
        self.org_repository = org_repository
        self.user_org_repository = user_org_repository
        self.user_repository = user_repository
        self.email_service = EmailService()
    
    async def create_invitation(
        self,
        org_id: UUID,
        invitation_data: InvitationCreate,
        inviter_id: UUID
    ) -> InvitationResponse:
        """
        Create organization invitation.
        
        Args:
            org_id: Organization ID
            invitation_data: Invitation details
            inviter_id: User creating the invitation
        
        Returns:
            Created invitation
        
        Raises:
            NotFoundException: Organization not found
            ForbiddenException: Insufficient permissions
            AlreadyExistsException: User already member
            ValidationException: Invalid role
        """
        # Check organization exists
        organization = self.org_repository.get_by_uuid(org_id)
        if not organization:
            raise NotFoundException("Organization", org_id)
        
        # Check inviter has permission (owner/admin)
        inviter_role = self.user_org_repository.get_user_role(inviter_id, org_id)
        if inviter_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            raise ForbiddenException("Only owners and admins can invite members")
        
        # Validate role
        try:
            role = OrganizationRole(invitation_data.role.lower())
        except ValueError:
            raise ValidationException(f"Invalid role: {invitation_data.role}")
        
        # Check if user already exists
        existing_user = self.user_repository.get_by_email(invitation_data.email)
        if existing_user:
            # Check if already member
            if self.user_org_repository.is_member(existing_user.id, org_id):
                raise AlreadyExistsException("User", "email", invitation_data.email)
        
        # Check for existing pending invitation
        existing_invitation = (
            self.db.query(Invitation)
            .filter(Invitation.organization_id == org_id)
            .filter(Invitation.email == invitation_data.email.lower())
            .filter(Invitation.status == InvitationStatus.PENDING.value)
            .first()
        )
        
        if existing_invitation:
            raise AlreadyExistsException("Invitation", "email", invitation_data.email)
        
        # Create invitation
        invitation = Invitation(
            organization_id=org_id,
            email=invitation_data.email.lower(),
            role=role,
            invited_by=inviter_id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            status=InvitationStatus.PENDING
        )
        
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        
        # Get inviter details
        inviter = self.user_repository.get_by_uuid(inviter_id)
        
        # Send invitation email
        await self.email_service.send_invitation_email(
            to_email=invitation.email,
            organization_name=organization.name,
            inviter_name=inviter.full_name,
            invitation_token=str(invitation.token),
            role=role.value
        )
        
        return InvitationResponse.model_validate(invitation)
    
    async def accept_invitation(self, token: UUID, user_id: UUID) -> bool:
        """
        Accept organization invitation.
        
        Args:
            token: Invitation token
            user_id: User accepting the invitation
        
        Returns:
            True if accepted
        
        Raises:
            NotFoundException: Invitation not found
            ValidationException: Invalid invitation
        """
        # Get invitation
        invitation = (
            self.db.query(Invitation)
            .filter(Invitation.token == token)
            .filter(Invitation.status == InvitationStatus.PENDING.value)
            .first()
        )
        
        if not invitation:
            raise NotFoundException("Invitation", token)
        
        # Check expiration
        if invitation.is_expired():
            invitation.status = InvitationStatus.EXPIRED
            self.db.commit()
            raise ValidationException("Invitation has expired")
        
        # Get user
        user = self.user_repository.get_by_uuid(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        
        # Verify email matches
        if user.email.lower() != invitation.email.lower():
            raise ValidationException("Invitation is for a different email address")
        
        # Check if already member
        if self.user_org_repository.is_member(user_id, invitation.organization_id):
            raise ValidationException("You are already a member of this organization")
        
        # Create membership
        self.user_org_repository.create_membership(
            user_id=user_id,
            organization_id=invitation.organization_id,
            role=invitation.role
        )
        
        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        self.db.commit()
        
        return True
    
    def list_members(self, org_id: UUID, user_id: UUID) -> List[MemberResponse]:
        """
        List organization members.
        
        Args:
            org_id: Organization ID
            user_id: Requesting user ID
        
        Returns:
            List of members
        
        Raises:
            ForbiddenException: Not a member
        """
        # Check user is member
        if not self.user_org_repository.is_member(user_id, org_id):
            raise ForbiddenException("You don't have access to this organization")
        
        # Get all members
        memberships = (
            self.db.query(UserOrganization)
            .filter(UserOrganization.organization_id == org_id)
            .filter(UserOrganization.is_active == True)
            .all()
        )
        
        members = []
        for membership in memberships:
            user = self.user_repository.get_by_uuid(membership.user_id)
            if user:
                members.append(MemberResponse(
                    user_id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=membership.role.value,
                    is_active=membership.is_active,
                    joined_at=membership.created_at
                ))
        
        return members
    
    def update_member_role(
        self,
        org_id: UUID,
        member_user_id: UUID,
        role_data: UpdateMemberRole,
        requesting_user_id: UUID
    ) -> MemberResponse:
        """
        Update member role.
        
        Args:
            org_id: Organization ID
            member_user_id: Member to update
            role_data: New role
            requesting_user_id: User making the request
        
        Returns:
            Updated member
        
        Raises:
            ForbiddenException: Insufficient permissions
            ValidationException: Invalid role or cannot modify owner
        """
        # Check requester has permission (owner/admin)
        requester_role = self.user_org_repository.get_user_role(requesting_user_id, org_id)
        if requester_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            raise ForbiddenException("Only owners and admins can update member roles")
        
        # Get member's current role
        member_role = self.user_org_repository.get_user_role(member_user_id, org_id)
        if not member_role:
            raise NotFoundException("Member", member_user_id)
        
        # Cannot modify owner role
        if member_role == OrganizationRole.OWNER:
            raise ValidationException("Cannot modify organization owner role")
        
        # Validate new role
        try:
            new_role = OrganizationRole(role_data.role.lower())
        except ValueError:
            raise ValidationException(f"Invalid role: {role_data.role}")
        
        # Cannot assign owner role
        if new_role == OrganizationRole.OWNER:
            raise ValidationException("Cannot assign owner role")
        
        # Update role
        membership = (
            self.db.query(UserOrganization)
            .filter(UserOrganization.user_id == member_user_id)
            .filter(UserOrganization.organization_id == org_id)
            .first()
        )
        
        membership.role = new_role
        self.db.commit()
        
        # Get updated member info
        user = self.user_repository.get_by_uuid(member_user_id)
        return MemberResponse(
            user_id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=new_role.value,
            is_active=membership.is_active,
            joined_at=membership.created_at
        )
    
    async def remove_member(
        self,
        org_id: UUID,
        member_user_id: UUID,
        requesting_user_id: UUID
    ) -> bool:
        """
        Remove member from organization.
        
        Args:
            org_id: Organization ID
            member_user_id: Member to remove
            requesting_user_id: User making the request
        
        Returns:
            True if removed
        
        Raises:
            ForbiddenException: Insufficient permissions
            ValidationException: Cannot remove owner
        """
        # Check requester has permission (owner/admin)
        requester_role = self.user_org_repository.get_user_role(requesting_user_id, org_id)
        if requester_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            raise ForbiddenException("Only owners and admins can remove members")
        
        # Get member's role
        member_role = self.user_org_repository.get_user_role(member_user_id, org_id)
        if not member_role:
            raise NotFoundException("Member", member_user_id)
        
        # Cannot remove owner
        if member_role == OrganizationRole.OWNER:
            raise ValidationException("Cannot remove organization owner")
        
        # Cannot remove self
        if member_user_id == requesting_user_id:
            raise ValidationException("Cannot remove yourself from organization")
        
        # Deactivate membership
        membership = (
            self.db.query(UserOrganization)
            .filter(UserOrganization.user_id == member_user_id)
            .filter(UserOrganization.organization_id == org_id)
            .first()
        )
        
        membership.is_active = False
        self.db.commit()
        
        # Send notification email
        user = self.user_repository.get_by_uuid(member_user_id)
        organization = self.org_repository.get_by_uuid(org_id)
        requester = self.user_repository.get_by_uuid(requesting_user_id)
        
        await self.email_service.send_member_removed_email(
            to_email=user.email,
            organization_name=organization.name,
            removed_by=requester.full_name
        )
        
        return True
    
    async def create_bulk_invitations(
        self,
        org_id: UUID,
        bulk_data: BulkInvitationCreate,
        inviter_id: UUID
    ) -> BulkInvitationResponse:
        """
        Create multiple organization invitations in bulk.
        
        Args:
            org_id: Organization ID
            bulk_data: Bulk invitation data with list of invitations
            inviter_id: User creating the invitations
        
        Returns:
            Bulk invitation response with created invitations and errors
        
        Raises:
            NotFoundException: Organization not found
            ForbiddenException: Insufficient permissions
            ValidationException: Invalid request (e.g., too many invitations)
        """
        # Check organization exists
        organization = self.org_repository.get_by_uuid(org_id)
        if not organization:
            raise NotFoundException("Organization", org_id)
        
        # Check inviter has permission (owner/admin)
        inviter_role = self.user_org_repository.get_user_role(inviter_id, org_id)
        if inviter_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            raise ForbiddenException("Only owners and admins can invite members")
        
        # Validate maximum invitations
        if len(bulk_data.invitations) > 50:
            raise ValidationException("Maximum 50 invitations allowed per request")
        
        # Get inviter details (needed for email sending)
        inviter = self.user_repository.get_by_uuid(inviter_id)
        if not inviter:
            raise NotFoundException("User", inviter_id)
        
        created_invitations = []
        errors = []
        
        # Track emails to detect duplicates in request
        seen_emails = set()
        
        # First pass: validate all invitations
        valid_invitations = []
        for idx, invitation_item in enumerate(bulk_data.invitations):
            email_lower = invitation_item.email.lower()
            error = None
            
            # Check for duplicate in request
            if email_lower in seen_emails:
                error = "Duplicate email in request"
            else:
                seen_emails.add(email_lower)
                
                # Validate role
                try:
                    role = OrganizationRole(invitation_item.role.lower())
                except ValueError:
                    error = f"Invalid role: {invitation_item.role}"
                
                # Check if user already exists and is member
                if not error:
                    existing_user = self.user_repository.get_by_email(invitation_item.email)
                    if existing_user:
                        if self.user_org_repository.is_member(existing_user.id, org_id):
                            error = "User is already a member of this organization"
                
                # Check for existing pending invitation
                if not error:
                    existing_invitation = (
                        self.db.query(Invitation)
                        .filter(Invitation.organization_id == org_id)
                        .filter(Invitation.email == email_lower)
                        .filter(Invitation.status == InvitationStatus.PENDING.value)
                        .first()
                    )
                    if existing_invitation:
                        error = "Pending invitation already exists for this email"
            
            if error:
                errors.append(BulkInvitationError(
                    email=invitation_item.email,
                    error=error
                ))
            else:
                valid_invitations.append((invitation_item, role))
        
        # Second pass: create all valid invitations in a single transaction
        if valid_invitations:
            try:
                for invitation_item, role in valid_invitations:
                    invitation = Invitation(
                        organization_id=org_id,
                        email=invitation_item.email.lower(),
                        role=role,
                        invited_by=inviter_id,
                        expires_at=datetime.utcnow() + timedelta(days=7),
                        status=InvitationStatus.PENDING
                    )
                    self.db.add(invitation)
                    created_invitations.append(invitation)
                
                # Commit all invitations in one transaction
                self.db.commit()
                
                # Refresh all invitations to get IDs and tokens
                for invitation in created_invitations:
                    self.db.refresh(invitation)
                
            except Exception as e:
                # Rollback on any error
                self.db.rollback()
                # Convert all valid invitations to errors
                for invitation_item, _ in valid_invitations:
                    errors.append(BulkInvitationError(
                        email=invitation_item.email,
                        error=f"Failed to create invitation: {str(e)}"
                    ))
                created_invitations = []
        
        # Convert created invitations to response format
        created_responses = [
            InvitationResponse.model_validate(inv) for inv in created_invitations
        ]
        
        return BulkInvitationResponse(
            created=created_responses,
            errors=errors,
            total=len(bulk_data.invitations),
            successful=len(created_responses),
            failed=len(errors)
        )
    
    async def send_bulk_invitation_emails(
        self,
        invitations: List[InvitationResponse],
        org_id: UUID,
        inviter_id: UUID
    ) -> None:
        """
        Send invitation emails for bulk invitations in background.
        
        Args:
            invitations: List of created invitations
            org_id: Organization ID
            inviter_id: Inviter user ID
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Get organization and inviter details
        organization = self.org_repository.get_by_uuid(org_id)
        inviter = self.user_repository.get_by_uuid(inviter_id)
        
        if not organization or not inviter:
            logger.error(f"Failed to get organization or inviter details for bulk email sending")
            return
        
        for invitation in invitations:
            try:
                await self.email_service.send_invitation_email(
                    to_email=invitation.email,
                    organization_name=organization.name,
                    inviter_name=inviter.full_name,
                    invitation_token=str(invitation.token),
                    role=invitation.role
                )
            except Exception as e:
                # Log error but don't fail - emails are sent in background
                logger.error(f"Failed to send invitation email to {invitation.email}: {str(e)}")