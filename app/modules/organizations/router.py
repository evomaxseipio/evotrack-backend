"""Organization API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.modules.auth.dependencies import CurrentUser
from app.modules.organizations.dependencies import get_organization_service
from app.modules.organizations.service import OrganizationService
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    OrganizationListResponse
)
from app.shared.responses import MessageResponse, ApiResponse, create_success_response
from app.modules.organizations.messages import SuccessMessages

from app.modules.organizations.invitation_service import InvitationService
from app.modules.organizations.invitation_schemas import (
    InvitationCreate,
    InvitationResponse,
    MemberResponse,
    UpdateMemberRole,
    BulkInvitationCreate,
    BulkInvitationResponse
)
from app.modules.organizations.dependencies import get_invitation_service
from app.modules.users.dependencies import get_user_service
from app.modules.users.service import UserService
from app.modules.users.schemas import UserListResponse
from app.modules.organizations.models import OrganizationRole
from app.modules.departments.dependencies import get_department_service
from app.modules.departments.service import DepartmentService
from app.modules.departments.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeResponse,
    UserDepartmentAssignment
)

router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[OrganizationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
    description="Create a new organization and assign creator as owner"
)
def create_organization(
    org_data: OrganizationCreate,
    current_user: CurrentUser,
    org_service: OrganizationService = Depends(get_organization_service)
) -> ApiResponse[OrganizationResponse]:
    """
    Create new organization.
    
    **Requires authentication.**
    
    **Request Body:**
    - **name**: Organization name (required)
    - **timezone**: Timezone (default: UTC)
    - **currency_code**: ISO 4217 currency code (default: USD)
    
    **Returns:**
    - Standard API response with:
      - success: true
      - data: Created organization with ID
      - messageResponse: Success message
      - errorMessage: Empty string
    - Creator automatically assigned as owner
    
    **Permissions:**
    - Any authenticated user can create organizations
    - User can create multiple organizations
    """
    organization = org_service.create_organization(org_data, current_user.id)
    return create_success_response(
        data=organization,
        message=SuccessMessages.ORGANIZATION_CREATED
    )


@router.get(
    "/",
    response_model=ApiResponse[List[OrganizationListResponse]],
    summary="List user's organizations",
    description="Get all organizations the current user belongs to with user role and statistics"
)
def list_user_organizations(
    current_user: CurrentUser,
    org_service: OrganizationService = Depends(get_organization_service)
) -> ApiResponse[List[OrganizationListResponse]]:
    """
    Get all organizations for current user.
    
    **Requires authentication.**
    
    **Returns:**
    - Standard API response with:
      - success: true
      - data: List of organizations user is member of
      - messageResponse: Success message
      - errorMessage: Empty string
    - Each organization includes:
      - Basic organization details (id, name, slug, tax_id, logo_url, timezone, currency_code, is_active)
      - user_role: The role of the current user in this organization
      - stats: Statistics including users_count, projects_count, and departments_count
      - Timestamps (created_at, updated_at)
    """
    organizations = org_service.get_user_organizations(current_user.id)
    return create_success_response(
        data=organizations,
        message=SuccessMessages.ORGANIZATIONS_RETRIEVED
    )


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
    description="Get organization by ID"
)
def get_organization(
    org_id: UUID,
    current_user: CurrentUser,
    org_service: OrganizationService = Depends(get_organization_service)
) -> OrganizationResponse:
    """
    Get organization by ID.
    
    **Requires authentication and membership.**
    
    **Returns:**
    - Organization details
    
    **Errors:**
    - **404**: Organization not found
    - **403**: User not member of organization
    """
    return org_service.get_organization(org_id, current_user.id)


@router.put(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update organization details"
)
def update_organization(
    org_id: UUID,
    org_data: OrganizationUpdate,
    current_user: CurrentUser,
    org_service: OrganizationService = Depends(get_organization_service)
) -> OrganizationResponse:
    """
    Update organization.
    
    **Requires owner or admin role.**
    
    **Request Body:**
    - All fields optional
    
    **Returns:**
    - Updated organization
    
    **Errors:**
    - **404**: Organization not found
    - **403**: Insufficient permissions (requires admin/owner)
    """
    return org_service.update_organization(org_id, org_data, current_user.id)


@router.delete(
    "/{org_id}",
    response_model=MessageResponse,
    summary="Delete organization",
    description="Delete organization (soft delete)"
)
def delete_organization(
    org_id: UUID,
    current_user: CurrentUser,
    org_service: OrganizationService = Depends(get_organization_service)
) -> MessageResponse:
    """
    Delete organization (soft delete).
    
    **Requires owner role.**
    
    **Returns:**
    - Success message
    
    **Errors:**
    - **404**: Organization not found
    - **403**: Only owners can delete organizations
    """
    org_service.delete_organization(org_id, current_user.id)
    return MessageResponse(
        success=True,
        message="Organization deleted successfully"
    )


# Invitation endpoints
@router.post(
    "/{org_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite user to organization",
    description="Send invitation email to user"
)
async def invite_member(
    org_id: UUID,
    invitation_data: InvitationCreate,
    current_user: CurrentUser,
    invitation_service: InvitationService = Depends(get_invitation_service)
) -> InvitationResponse:
    """
    Invite user to organization.
    
    **Requires owner or admin role.**
    
    **Request Body:**
    - **email**: Email of user to invite
    - **role**: Role to assign (employee/manager/admin)
    
    **Returns:**
    - Invitation details with token
    - Email sent to invited user
    
    **Errors:**
    - **403**: Insufficient permissions (requires owner/admin)
    - **409**: User already member or invitation exists
    """
    return await invitation_service.create_invitation(org_id, invitation_data, current_user.id)


@router.post(
    "/{org_id}/invitations/bulk",
    response_model=BulkInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk invite users to organization",
    description="Invite multiple users at once (max 50 per request)"
)
async def bulk_invite_members(
    org_id: UUID,
    bulk_data: BulkInvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    invitation_service: InvitationService = Depends(get_invitation_service)
) -> BulkInvitationResponse:
    """
    Invite multiple users to organization in bulk.
    
    **Requires owner or admin role.**
    
    **Request Body:**
    - **invitations**: Array of invitation objects (max 50)
      - **email**: Email of user to invite
      - **role**: Role to assign (employee/manager/admin)
    
    **Returns:**
    - List of successfully created invitations
    - List of errors for failed invitations
    - Summary statistics (total, successful, failed)
    - Emails sent in background (non-blocking)
    
    **Validation:**
    - Maximum 50 invitations per request
    - Each email validated for format
    - Duplicate emails in request are rejected
    - Existing members are rejected
    - Existing pending invitations are rejected
    
    **Transaction:**
    - All valid invitations created in single transaction (all or nothing)
    - Invalid invitations reported as errors without blocking valid ones
    
    **Errors:**
    - **403**: Insufficient permissions (requires owner/admin)
    - **400**: Invalid request (e.g., too many invitations, invalid role)
    - **404**: Organization not found
    """
    # Create bulk invitations
    result = await invitation_service.create_bulk_invitations(
        org_id=org_id,
        bulk_data=bulk_data,
        inviter_id=current_user.id
    )
    
    # Send emails in background if there are successful invitations
    if result.created:
        background_tasks.add_task(
            invitation_service.send_bulk_invitation_emails,
            invitations=result.created,
            org_id=org_id,
            inviter_id=current_user.id
        )
    
    return result


@router.post(
    "/invitations/accept",
    response_model=MessageResponse,
    summary="Accept invitation",
    description="Accept organization invitation"
)
async def accept_invitation(
    token: UUID,
    current_user: CurrentUser,
    invitation_service: InvitationService = Depends(get_invitation_service)
) -> MessageResponse:
    """
    Accept organization invitation.
    
    **Requires authentication.**
    
    **Query Parameter:**
    - **token**: Invitation token (UUID)
    
    **Returns:**
    - Success message
    - User added to organization
    
    **Errors:**
    - **404**: Invitation not found
    - **400**: Invitation expired or invalid
    """
    await invitation_service.accept_invitation(token, current_user.id)
    return MessageResponse(
        success=True,
        message="Invitation accepted successfully"
    )


# User list endpoint moved to organizations/users_router.py


@router.get(
    "/{org_id}/members",
    response_model=List[MemberResponse],
    summary="List organization members",
    description="Get all members of the organization"
)
def list_members(
    org_id: UUID,
    current_user: CurrentUser,
    invitation_service: InvitationService = Depends(get_invitation_service)
) -> List[MemberResponse]:
    """
    List organization members.
    
    **Requires membership.**
    
    **Returns:**
    - List of members with roles
    
    **Errors:**
    - **403**: Not a member of organization
    """
    return invitation_service.list_members(org_id, current_user.id)


@router.put(
    "/{org_id}/members/{member_id}",
    response_model=MemberResponse,
    summary="Update member role",
    description="Change member's role in organization"
)
def update_member_role(
    org_id: UUID,
    member_id: UUID,
    role_data: UpdateMemberRole,
    current_user: CurrentUser,
    invitation_service: InvitationService = Depends(get_invitation_service)
) -> MemberResponse:
    """
    Update member role.
    
    **Requires owner or admin role.**
    
    **Request Body:**
    - **role**: New role (employee/manager/admin)
    
    **Returns:**
    - Updated member details
    
    **Errors:**
    - **403**: Insufficient permissions
    - **400**: Cannot modify owner role
    """
    return invitation_service.update_member_role(org_id, member_id, role_data, current_user.id)


@router.delete(
    "/{org_id}/members/{member_id}",
    response_model=MessageResponse,
    summary="Remove member",
    description="Remove member from organization"
)
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    current_user: CurrentUser,
    invitation_service: InvitationService = Depends(get_invitation_service)
) -> MessageResponse:
    """
    Remove member from organization.
    
    **Requires owner or admin role.**
    
    **Returns:**
    - Success message
    - Member removed
    - Notification email sent
    
    **Errors:**
    - **403**: Insufficient permissions
    - **400**: Cannot remove owner or yourself
    """
    await invitation_service.remove_member(org_id, member_id, current_user.id)
    return MessageResponse(
        success=True,
        message="Member removed successfully"
    )


# Department endpoints within organizations
@router.post(
    "/{org_id}/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
    description="Create a new department in an organization"
)
def create_department(
    org_id: UUID,
    dept_data: DepartmentCreate,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> DepartmentResponse:
    """
    Create a new department.
    
    **Requires admin or owner role.**
    
    **Request Body:**
    - **name**: Department name (required)
    - **description**: Department description (optional)
    - **parent_department_id**: Parent department ID for hierarchy (optional)
    - **department_head_id**: Department head user ID (optional)
    - **budget**: Department budget (optional)
    
    **Returns:**
    - Created department
    
    **Errors:**
    - **403**: Insufficient permissions
    - **404**: Parent department not found
    - **400**: Invalid parent department or department head
    """
    return dept_service.create_department(org_id, dept_data, current_user.id)


@router.get(
    "/{org_id}/departments",
    response_model=List[DepartmentTreeResponse],
    summary="List departments",
    description="Get all departments for an organization in tree format"
)
def list_departments(
    org_id: UUID,
    current_user: CurrentUser,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, min_length=1, description="Search in name/description"),
    dept_service: DepartmentService = Depends(get_department_service)
) -> List[DepartmentTreeResponse]:
    """
    List all departments for an organization in hierarchical tree format.
    
    **Requires organization membership.**
    
    **Query Parameters:**
    - **is_active**: Filter by active status (optional)
    - **search**: Search in name/description (optional)
    
    **Returns:**
    - Tree structure of departments with user and team counts
    
    **Errors:**
    - **403**: Not a member of organization
    """
    return dept_service.get_departments(org_id, current_user.id, is_active, search)


@router.put(
    "/{org_id}/users/{user_id}/department",
    response_model=dict,
    summary="Assign user to department",
    description="Assign a user to a department"
)
def assign_user_to_department(
    org_id: UUID,
    user_id: UUID,
    assignment: UserDepartmentAssignment,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> dict:
    """
    Assign user to department.
    
    **Requires admin or owner role.**
    
    **Request Body:**
    - **department_id**: Department ID to assign user to
    
    **Returns:**
    - Updated user with department assignment
    
    **Errors:**
    - **403**: Insufficient permissions
    - **404**: User or department not found
    - **400**: User not member of organization
    """
    return dept_service.assign_user_to_department(
        org_id, user_id, assignment.department_id, current_user.id
    )
    