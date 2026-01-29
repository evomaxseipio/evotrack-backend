"""User management within organizations (admin endpoints)."""

import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.users.dependencies import (
    get_user_service,
    get_current_user
)
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    UserCreateByAdmin,
    UserBulkCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    UserBulkCreateResponse,
    OrganizationUsersResponse
)
from app.modules.users.models import User, UserStatus
from app.shared.responses import MessageResponse

router = APIRouter()


# ========================================
# User Management in Organization
# ========================================

@router.post(
    "/organizations/{org_id}/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user in organization",
    description="Admin creates user directly (pending activation)"
)
def create_user_in_organization(
    org_id: UUID,
    user_data: UserCreateByAdmin,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Create user in organization (admin only).
    
    User is created in **pending_activation** state.
    Activation email is sent automatically.
    User appears in all lists and can be assigned to teams/projects.
    User cannot login until they activate their account.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    
    **Request Body:**
    - **email**: User email (required)
    - **first_name**: First name (required)
    - **last_name**: Last name (required)
    - **phone**: Optional phone
    - **timezone**: Timezone (default: UTC)
    - **language**: Language code (default: en)
    - **send_activation_email**: Send email (default: true)
    
    **Requires**: Authentication + Admin role
    
    **Returns**: Created user
    
    **Errors:**
    - **409**: Email already exists
    - **403**: Not admin
    """
    user = service.create_user_by_admin(org_id, user_data, current_user)
    return UserResponse.model_validate(user)


@router.post(
    "/organizations/{org_id}/users/bulk",
    response_model=UserBulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple users",
    description="Bulk create users in organization"
)
def create_users_bulk(
    org_id: UUID,
    bulk_data: UserBulkCreate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserBulkCreateResponse:
    """
    Create multiple users in organization.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    
    **Request Body:**
    - **users**: List of user data (max 50)
    
    **Requires**: Authentication + Admin role
    
    **Returns**: 
    - List of created users
    - List of failed creations with errors
    
    **Note**: This is a partial success operation.
    Some users may be created while others fail.
    """
    result = service.create_users_bulk(
        org_id,
        bulk_data.users,
        current_user
    )
    
    return UserBulkCreateResponse(
        created=[UserResponse.model_validate(u) for u in result["created"]],
        failed=result["failed"],
        total_created=result["total_created"],
        total_failed=result["total_failed"]
    )


@router.get(
    "/organizations/{org_id}/users",
    response_model=OrganizationUsersResponse,
    summary="List organization users",
    description="Get all users in organization with filters using cursor-based pagination"
)
def list_organization_users(
    org_id: UUID,
    skip: int = Query(0, ge=0, description="Pagination offset (deprecated, use cursor)"),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None, description="Pagination cursor (JSON)"),
    search: Optional[str] = Query(None, description="Search by name/email"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> OrganizationUsersResponse:
    """
    List users in organization using database function.

    **Path Parameters:**
    - **org_id**: Organization UUID

    **Query Parameters:**
    - **skip**: Pagination offset (deprecated, use cursor instead)
    - **limit**: Max results 1-100 (default: 20)
    - **cursor**: Pagination cursor (JSON string)
    - **search**: Search by name or email
    - **include_inactive**: Include inactive users (default: false)

    **Requires**: Authentication + Organization membership

    **Returns**: Users with pagination info (cursor-based)

    **Note**: Uses fn_get_organization_users_json database function.
    """
    # Parse cursor if provided
    cursor_dict = None
    if cursor:
        try:
            cursor_dict = json.loads(cursor)
        except json.JSONDecodeError:
            cursor_dict = None

    result = service.get_organization_users_json(
        organization_id=org_id,
        current_user_id=current_user.id,
        limit=limit,
        cursor=cursor_dict,
        include_inactive=include_inactive,
        search=search
    )

    return OrganizationUsersResponse(**result)


@router.get(
    "/organizations/{org_id}/users/{user_id}",
    response_model=UserDetailResponse,
    summary="Get user details",
    description="Get detailed information about user in organization"
)
def get_organization_user(
    org_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserDetailResponse:
    """
    Get user details in organization context.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    - **user_id**: User UUID
    
    **Requires**: Authentication + Organization membership
    
    **Returns**: User details
    
    **Errors:**
    - **404**: User not found
    """
    user = service.get_user(user_id)
    return UserDetailResponse.model_validate(user)


@router.put(
    "/organizations/{org_id}/users/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information (admin only)"
)
def update_organization_user(
    org_id: UUID,
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Update user in organization.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    - **user_id**: User UUID
    
    **Request Body:**
    - **first_name**: Optional
    - **last_name**: Optional
    - **phone**: Optional
    - **timezone**: Optional
    - **language**: Optional
    
    **Requires**: Authentication + Admin role
    
    **Returns**: Updated user
    
    **Errors:**
    - **404**: User not found
    - **403**: Not admin
    """
    user = service.update_user(user_id, user_data, current_user)
    return UserResponse.model_validate(user)


@router.delete(
    "/organizations/{org_id}/users/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate user",
    description="Deactivate user in organization (soft delete)"
)
def deactivate_organization_user(
    org_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> MessageResponse:
    """
    Deactivate user.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    - **user_id**: User UUID
    
    **Requires**: Authentication + Admin role
    
    **Returns**: Success message
    
    **Errors:**
    - **404**: User not found
    - **403**: Not admin
    - **400**: Cannot deactivate self
    
    **Note**: This is a soft delete. User status changes to inactive.
    """
    service.deactivate_user(user_id, current_user)
    
    return MessageResponse(
        success=True,
        message=f"User deactivated successfully"
    )


@router.post(
    "/organizations/{org_id}/users/{user_id}/reactivate",
    response_model=UserResponse,
    summary="Reactivate user",
    description="Reactivate deactivated user"
)
def reactivate_organization_user(
    org_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Reactivate user.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    - **user_id**: User UUID
    
    **Requires**: Authentication + Admin role
    
    **Returns**: Reactivated user
    """
    user = service.reactivate_user(user_id, current_user)
    return UserResponse.model_validate(user)


# ========================================
# Search
# ========================================

@router.get(
    "/organizations/{org_id}/users/search",
    response_model=List[UserResponse],
    summary="Search users",
    description="Search users in organization"
)
def search_organization_users(
    org_id: UUID,
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> List[UserResponse]:
    """
    Search users in organization.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    
    **Query Parameters:**
    - **q**: Search term (min 2 chars)
    - **limit**: Max results (1-50, default: 10)
    
    **Requires**: Authentication + Organization membership
    
    **Returns**: List of matching users
    """
    users = service.search_users(org_id, q, limit)
    return [UserResponse.model_validate(user) for user in users]


# ========================================
# Statistics
# ========================================

@router.get(
    "/organizations/{org_id}/users/stats",
    summary="Get user statistics",
    description="Get user counts by status"
)
def get_organization_user_stats(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> dict:
    """
    Get user statistics.
    
    **Path Parameters:**
    - **org_id**: Organization UUID
    
    **Requires**: Authentication + Admin role
    
    **Returns**: 
    - total: Total users
    - active: Active users
    - pending: Pending activation
    - inactive: Deactivated users
    """
    return service.get_user_stats(org_id)
