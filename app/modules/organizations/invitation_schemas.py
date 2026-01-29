"""Pydantic schemas for Invitation model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InvitationCreate(BaseModel):
    """Schema for creating an invitation."""
    
    email: EmailStr = Field(..., description="Email of user to invite")
    role: str = Field(
        default="employee",
        description="Role to assign (owner/admin/manager/employee)"
    )


class InvitationResponse(BaseModel):
    """Schema for invitation response."""
    
    id: UUID
    organization_id: UUID
    email: str
    role: str
    token: UUID
    status: str
    invited_by: UUID
    expires_at: datetime
    created_at: datetime
    
    model_config = {"from_attributes": True}


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""
    
    token: UUID = Field(..., description="Invitation token")


class MemberResponse(BaseModel):
    """Schema for organization member."""
    
    user_id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    joined_at: datetime
    
    model_config = {"from_attributes": True}


class UpdateMemberRole(BaseModel):
    """Schema for updating member role."""
    
    role: str = Field(..., description="New role (owner/admin/manager/employee)")


class BulkInvitationItem(BaseModel):
    """Schema for a single invitation in bulk request."""
    
    email: EmailStr = Field(..., description="Email of user to invite")
    role: str = Field(
        default="employee",
        description="Role to assign (owner/admin/manager/employee)"
    )


class BulkInvitationCreate(BaseModel):
    """Schema for creating multiple invitations."""
    
    invitations: list[BulkInvitationItem] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of invitations to create (max 50)"
    )


class BulkInvitationError(BaseModel):
    """Schema for invitation error in bulk response."""
    
    email: str = Field(..., description="Email that failed")
    error: str = Field(..., description="Error message")


class BulkInvitationResponse(BaseModel):
    """Schema for bulk invitation response."""
    
    created: list[InvitationResponse] = Field(
        default_factory=list,
        description="Successfully created invitations"
    )
    errors: list[BulkInvitationError] = Field(
        default_factory=list,
        description="Failed invitations with error details"
    )
    total: int = Field(..., description="Total invitations in request")
    successful: int = Field(..., description="Number of successful invitations")
    failed: int = Field(..., description="Number of failed invitations")