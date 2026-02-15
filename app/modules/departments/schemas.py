"""Pydantic schemas for Department models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

# Import TeamResponse for DepartmentDetailResponse
from app.modules.teams.schemas import TeamResponse


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


# Department Schemas
class DepartmentBase(BaseModel):
    """Base department schema."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Department name")
    description: Optional[str] = Field(None, description="Department description")
    parent_department_id: Optional[UUID] = Field(None, description="Parent department ID for hierarchy")
    department_head_id: Optional[UUID] = Field(None, description="Department head user ID")
    budget: Optional[Decimal] = Field(None, ge=0, description="Department budget")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department."""
    pass


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    parent_department_id: Optional[UUID] = None
    department_head_id: Optional[UUID] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema for department response."""
    
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )



class DepartmentTreeResponse(DepartmentResponse):
    """Schema for department with hierarchical structure."""
    
    sub_departments: List["DepartmentTreeResponse"] = Field(default_factory=list)
    user_count: int = Field(default=0, description="Number of users in this department")
    team_count: int = Field(default=0, description="Number of teams in this department")
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )



class DepartmentDetailResponse(DepartmentResponse):
    """Schema for detailed department response."""
    
    parent_department: Optional[DepartmentResponse] = None
    department_head: Optional[dict] = None
    teams: List[TeamResponse] = Field(default_factory=list)
    users: List[dict] = Field(default_factory=list)
    user_count: int = Field(default=0)
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )



# User Assignment Schema
class UserDepartmentAssignment(BaseModel):
    """Schema for assigning user to department."""
    
    department_id: UUID = Field(..., description="Department ID to assign user to")


# Pagination Response
class DepartmentListResponse(BaseModel):
    """Schema for paginated department list."""
    
    items: List[DepartmentTreeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


# ========================================
# Organization Departments Response (DB Function)
# ========================================

class OrganizationDepartmentItem(BaseModel):
    """Schema for department item returned by fn_get_organization_departments_json."""

    id: UUID
    name: str
    description: Optional[str] = None
    budget: Optional[Decimal] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    parent_department_id: Optional[UUID] = None
    parent_department_name: Optional[str] = None
    department_head_id: Optional[UUID] = None
    department_head_name: Optional[str] = None
    department_head_avatar: Optional[str] = None
    employee_count: int = 0
    meta: Dict[str, Any]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class PaginationCursor(BaseModel):
    """Cursor for pagination."""
    id: Optional[UUID] = None
    ts: Optional[datetime] = None

class OrganizationDepartmentsRequest(BaseModel):
    """Request schema for listing organization departments."""

    limit: int = Field(default=20, ge=1, le=100, description="Max results 1-100")
    nextCursor: Optional[PaginationCursor] = Field(default=None, description="Pagination cursor")
    search: Optional[str] = Field(default=None, description="Search by name or description")
    include_inactive: bool = Field(default=False, description="Include inactive departments")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class OrganizationDepartmentsStats(BaseModel):
    """Statistics for organization departments."""
    
    total_departments: int = Field(..., description="Total departments")
    active_departments: int = Field(..., description="Active departments")
    inactive_departments: int = Field(..., description="Inactive departments")
    root_departments: int = Field(..., description="Root departments (no parent)")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class OrganizationDepartmentsPagination(BaseModel):
    """Pagination info for organization departments response."""

    count: int
    limit: int
    has_more: bool
    next_cursor: Optional[PaginationCursor] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class OrganizationDepartmentsMeta(BaseModel):
    """Meta information for organization departments response."""
    user_role: str
    organization_id: UUID
    can_see_budget: bool = False

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class OrganizationDepartmentsResponse(BaseModel):
    """Response schema for organization departments with cursor pagination and statistics."""

    success: bool = True
    data: List[Optional[OrganizationDepartmentItem]]
    stats: OrganizationDepartmentsStats
    pagination: OrganizationDepartmentsPagination
    meta: OrganizationDepartmentsMeta
    message: str = ""

class OrganizationDepartmentsTreeResponse(BaseModel):
    """Response schema for department tree with success, data, stats and message."""

    success: bool = True
    data: List[DepartmentTreeResponse]
    stats: OrganizationDepartmentsStats
    message: str = ""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

# Rebuild models to resolve forward references
DepartmentTreeResponse.model_rebuild()
