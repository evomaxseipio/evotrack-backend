"""Department management within organizations."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.auth.dependencies import CurrentUser
from app.modules.departments.dependencies import get_department_service
from app.modules.departments.service import DepartmentService
from app.modules.departments.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    DepartmentTreeResponse,
    DepartmentDetailResponse,
    UserDepartmentAssignment,
    OrganizationDepartmentsRequest,
    OrganizationDepartmentsResponse,
    OrganizationDepartmentsTreeResponse
)
from app.shared.responses import MessageResponse, ApiResponse

router = APIRouter()


# ========================================
# Search & List
# ========================================

@router.post(
    "/organizations/{org_id}/departments/search",
    response_model=OrganizationDepartmentsResponse,
    summary="List organization departments",
    description="Get all departments in organization with advanced filters using cursor-based pagination"
)
def list_organization_departments(
    org_id: UUID,
    current_user: CurrentUser,
    request: OrganizationDepartmentsRequest = OrganizationDepartmentsRequest(),
    service: DepartmentService = Depends(get_department_service)
) -> OrganizationDepartmentsResponse:
    """
    List departments in organization using database function with advanced filters.

    **Path Parameters:**
    - **org_id**: Organization UUID

    **Request Body:**
    - **limit**: Max results 1-100 (default: 20)
    - **nextCursor**: Pagination cursor object
    - **search**: Search by name or description
    - **includeInactive**: Include inactive departments

    **Requires**: Authentication + Organization membership

    **Returns**: Departments with statistics and pagination info (cursor-based)

    **Note**: Uses fn_get_organization_departments_json database function.
    """
    cursor_dict = None
    if request.nextCursor:
        cursor_dict = request.nextCursor.model_dump(mode='json', exclude_none=True)

    result = service.get_organization_departments_json(
        organization_id=org_id,
        current_user_id=current_user.id,
        limit=request.limit,
        cursor=cursor_dict,
        include_inactive=request.include_inactive,
        search=request.search
    )

    return OrganizationDepartmentsResponse(**result)


@router.get(
    "/organizations/{org_id}/departments",
    response_model=OrganizationDepartmentsTreeResponse,
    summary="List departments (Tree)",
    description="Get all departments for an organization in tree format"
)
def list_departments_tree(
    org_id: UUID,
    current_user: CurrentUser,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, min_length=1, description="Search in name/description"),
    dept_service: DepartmentService = Depends(get_department_service)
) -> OrganizationDepartmentsTreeResponse:
    """
    List all departments for an organization in hierarchical tree format.
    
    **Requires organization membership.**
    """
    departments = dept_service.get_departments(org_id, current_user.id, is_active, search)
    stats = dept_service.get_organization_stats(org_id, current_user.id)
    
    return OrganizationDepartmentsTreeResponse(
        success=True,
        data=departments,
        stats=stats,
        message="Departments retrieved successfully"
    )


# ========================================
# CRUD Operations
# ========================================

@router.post(
    "/organizations/{org_id}/departments",
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
    """
    return dept_service.create_department(org_id, dept_data, current_user.id)


@router.get(
    "/organizations/{org_id}/departments/{dept_id}",
    response_model=DepartmentDetailResponse,
    summary="Get department details",
    description="Get department details with users and teams"
)
def get_department(
    org_id: UUID,
    dept_id: UUID,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> DepartmentDetailResponse:
    """
    Get department by ID with full details.
    
    **Requires organization membership.**
    """
    return dept_service.get_department(dept_id, current_user.id)


@router.put(
    "/organizations/{org_id}/departments/{dept_id}",
    response_model=DepartmentResponse,
    summary="Update department",
    description="Update department details"
)
def update_department(
    org_id: UUID,
    dept_id: UUID,
    dept_data: DepartmentUpdate,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> DepartmentResponse:
    """
    Update department.
    
    **Requires admin or owner role.**
    """
    return dept_service.update_department(dept_id, dept_data, current_user.id)


@router.delete(
    "/organizations/{org_id}/departments/{dept_id}",
    response_model=MessageResponse,
    summary="Delete department",
    description="Delete department (soft delete)"
)
def delete_department(
    org_id: UUID,
    dept_id: UUID,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> MessageResponse:
    """
    Delete department (soft delete).
    
    **Requires admin or owner role.**
    """
    dept_service.delete_department(dept_id, current_user.id)
    return MessageResponse(
        success=True,
        message="Department deleted successfully"
    )


# ========================================
# Relationships
# ========================================

@router.get(
    "/organizations/{org_id}/departments/{dept_id}/users",
    response_model=List[dict],
    summary="Get department users",
    description="Get users in a department"
)
def get_department_users(
    org_id: UUID,
    dept_id: UUID,
    current_user: CurrentUser,
    include_children: bool = Query(False, description="Include users from sub-departments"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    dept_service: DepartmentService = Depends(get_department_service)
) -> List[dict]:
    """
    Get users in a department.
    
    **Requires organization membership.**
    """
    return dept_service.get_department_users(
        dept_id, current_user.id, include_children, skip, limit
    )


@router.put(
    "/organizations/{org_id}/departments/users/{user_id}",
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
    """
    return dept_service.assign_user_to_department(
        org_id, user_id, assignment.department_id, current_user.id
    )
