"""Pydantic schemas for Organization model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OrganizationBase(BaseModel):
    """Base organization schema."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Organization name")
    slug: Optional[str] = Field(None, min_length=1, max_length=200, description="Organization slug (URL-friendly identifier, auto-generated from name if not provided)")
    tax_id: str = Field(..., min_length=1, max_length=50, description="Tax identification number (RNC, EIN, NIT, etc.)")
    timezone: str = Field(default="UTC", description="Organization timezone")
    currency_code: str = Field(default="USD", min_length=3, max_length=3, description="ISO 4217 currency code")
    
    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate currency code is uppercase."""
        return v.upper()
    
    @field_validator("tax_id")
    @classmethod
    def validate_tax_id(cls, v: str) -> str:
        """Normalize tax_id (trim whitespace)."""
        return v.strip()


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, min_length=1, max_length=50)
    timezone: Optional[str] = None
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    logo_url: Optional[str] = Field(None, max_length=500)
    
    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency code is uppercase."""
        return v.upper() if v else None
    
    @field_validator("tax_id")
    @classmethod
    def validate_tax_id(cls, v: Optional[str]) -> Optional[str]:
        """Normalize tax_id (trim whitespace)."""
        return v.strip() if v else None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    
    id: UUID
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserOrganizationResponse(BaseModel):
    """Schema for user-organization relationship."""
    
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    is_active: bool
    created_at: datetime
    organization: OrganizationResponse
    
    model_config = {"from_attributes": True}


class OrganizationStats(BaseModel):
    """Statistics for an organization."""
    
    users_count: int = Field(..., description="Number of active users in the organization")
    projects_count: int = Field(default=0, description="Number of projects in the organization")
    departments_count: int = Field(..., description="Number of active departments in the organization")


class OrganizationListResponse(OrganizationBase):
    """Schema for organization list response with user role and stats."""
    
    id: UUID
    logo_url: Optional[str] = None
    is_active: bool
    user_role: str = Field(..., description="Role of the current user in this organization")
    stats: OrganizationStats = Field(..., description="Organization statistics")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}