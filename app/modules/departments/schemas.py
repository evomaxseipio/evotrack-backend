"""Pydantic schemas for Department models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Import TeamResponse for DepartmentDetailResponse
from app.modules.teams.schemas import TeamResponse


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
    
    model_config = {"from_attributes": True}


class DepartmentTreeResponse(DepartmentResponse):
    """Schema for department with hierarchical structure."""
    
    sub_departments: List["DepartmentTreeResponse"] = Field(default_factory=list)
    user_count: int = Field(default=0, description="Number of users in this department")
    team_count: int = Field(default=0, description="Number of teams in this department")
    
    model_config = {"from_attributes": True}


class DepartmentDetailResponse(DepartmentResponse):
    """Schema for detailed department response."""
    
    parent_department: Optional[DepartmentResponse] = None
    department_head: Optional[dict] = None
    teams: List[TeamResponse] = Field(default_factory=list)
    users: List[dict] = Field(default_factory=list)
    user_count: int = Field(default=0)
    
    model_config = {"from_attributes": True}


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


# Rebuild models to resolve forward references
DepartmentTreeResponse.model_rebuild()
