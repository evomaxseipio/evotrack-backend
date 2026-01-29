"""Pydantic schemas for Team models."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Team Schemas
class TeamBase(BaseModel):
    """Base team schema."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Team name")
    description: Optional[str] = Field(None, description="Team description")
    team_lead_id: Optional[UUID] = Field(None, description="Team lead user ID")


class TeamCreate(TeamBase):
    """Schema for creating a team."""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    team_lead_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    """Schema for team response."""
    
    id: UUID
    department_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class TeamDetailResponse(TeamResponse):
    """Schema for detailed team response."""
    
    team_lead: Optional[dict] = None
    members: List["TeamMemberResponse"] = Field(default_factory=list)
    member_count: int = Field(default=0)
    
    model_config = {"from_attributes": True}


# Team Member Schemas
class TeamMemberCreate(BaseModel):
    """Schema for adding a team member."""
    
    user_id: UUID = Field(..., description="User ID to add to team")
    role: Optional[str] = Field(None, max_length=100, description="Role within the team")


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    
    id: UUID
    team_id: UUID
    user_id: UUID
    role: Optional[str] = None
    joined_at: datetime
    user: Optional[dict] = None  # User details
    
    model_config = {"from_attributes": True}


# Pagination Response
class TeamListResponse(BaseModel):
    """Schema for paginated team list."""
    
    items: List[TeamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


# Rebuild models to resolve forward references
TeamDetailResponse.model_rebuild()
