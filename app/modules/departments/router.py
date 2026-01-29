"""Department API endpoints."""

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
    DepartmentDetailResponse
)
from app.shared.responses import MessageResponse

router = APIRouter()


# Department Endpoints


@router.get(
    "/departments/{dept_id}",
    response_model=DepartmentDetailResponse,
    summary="Get department",
    description="Get department details with users and teams"
)
def get_department(
    dept_id: UUID,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> DepartmentDetailResponse:
    """
    Get department by ID with full details.
    
    **Requires organization membership.**
    
    **Returns:**
    - Department details
    - List of users in department
    - List of teams in department
    - Parent department info
    - Department head info
    
    **Errors:**
    - **404**: Department not found
    - **403**: Not a member of organization
    """
    return dept_service.get_department(dept_id, current_user.id)


@router.put(
    "/departments/{dept_id}",
    response_model=DepartmentResponse,
    summary="Update department",
    description="Update department details"
)
def update_department(
    dept_id: UUID,
    dept_data: DepartmentUpdate,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> DepartmentResponse:
    """
    Update department.
    
    **Requires admin or owner role.**
    
    **Request Body:**
    - All fields optional
    
    **Returns:**
    - Updated department
    
    **Errors:**
    - **404**: Department not found
    - **403**: Insufficient permissions
    - **400**: Invalid hierarchy (circular reference)
    """
    return dept_service.update_department(dept_id, dept_data, current_user.id)


@router.delete(
    "/departments/{dept_id}",
    response_model=MessageResponse,
    summary="Delete department",
    description="Delete department (soft delete)"
)
def delete_department(
    dept_id: UUID,
    current_user: CurrentUser,
    dept_service: DepartmentService = Depends(get_department_service)
) -> MessageResponse:
    """
    Delete department (soft delete).
    
    **Requires admin or owner role.**
    
    **Returns:**
    - Success message
    
    **Errors:**
    - **404**: Department not found
    - **403**: Insufficient permissions
    - **400**: Department has active sub-departments
    """
    dept_service.delete_department(dept_id, current_user.id)
    return MessageResponse(
        success=True,
        message="Department deleted successfully"
    )


@router.get(
    "/departments/{dept_id}/users",
    response_model=List[dict],
    summary="Get department users",
    description="Get users in a department"
)
def get_department_users(
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
    
    **Query Parameters:**
    - **include_children**: Include users from sub-departments (default: false)
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records (default: 100, max: 100)
    
    **Returns:**
    - List of users in department
    
    **Errors:**
    - **404**: Department not found
    - **403**: Not a member of organization
    """
    return dept_service.get_department_users(
        dept_id, current_user.id, include_children, skip, limit
    )


