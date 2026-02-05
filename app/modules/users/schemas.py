"""Pydantic schemas for User model."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


# ========================================
# Base Schemas
# ========================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    timezone: str = Field(default="UTC", description="User timezone")


# ========================================
# Creation Schemas
# ========================================

class UserCreate(UserBase):
    """Schema for user self-registration (public)."""
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 characters)"
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter or not has_number:
            raise ValueError("Password must contain at least one letter and one number")
        
        return v
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email."""
        return v.lower().strip()


class UserCreateByAdmin(BaseModel):
    """Schema for admin creating users in organization."""

    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    identification: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(default="employee")
    department_id: Optional[UUID] = None
    avatar: Optional[str] = Field(None, max_length=500)
    timezone: str = Field(default="UTC")
    language: str = Field(default="en", max_length=10)
    send_activation_email: bool = Field(
        default=True,
        description="Send activation email to user"
    )

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email."""
        return v.lower().strip()


class UserBulkCreate(BaseModel):
    """Schema for bulk user creation."""
    
    users: List[UserCreateByAdmin] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of users to create (max 50)"
    )


# ========================================
# Update Schemas
# ========================================

class UserUpdate(BaseModel):
    """Schema for admin updating user information."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    identification: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = None
    department_id: Optional[UUID] = None
    avatar: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None
    status: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class ProfileUpdate(BaseModel):
    """Schema for user updating own profile."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    identification: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    preferences: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class PasswordChange(BaseModel):
    """Schema for password change."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (min 8 characters)"
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter or not has_number:
            raise ValueError(
                "Password must contain at least one letter and one number"
            )
        
        return v


# ========================================
# Activation Schemas
# ========================================

class UserActivation(BaseModel):
    """Schema for user account activation."""
    
    token: str = Field(..., description="Activation token from email")
    password: str = Field(
        ...,
        min_length=8,
        description="Password to set for account"
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter or not has_number:
            raise ValueError(
                "Password must contain at least one letter and one number"
            )
        
        return v


class ResendActivation(BaseModel):
    """Schema for resending activation email."""
    
    email: EmailStr = Field(..., description="User email address")


# ========================================
# Response Schemas
# ========================================

class OrganizationBasic(BaseModel):
    """Basic organization information for user response."""
    
    id: UUID
    name: str
    slug: str
    role: str = Field(..., description="User's role in the organization")
    
    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """Schema for user response (public data)."""

    id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    identification: Optional[str] = None
    nationality: Optional[str] = None
    department_id: Optional[UUID] = None
    department: Optional[str] = None
    language: str
    status: str
    role: Optional[str] = None
    is_active: bool = True
    can_login: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class UserDetailResponse(UserResponse):
    """Schema for detailed user response."""

    preferences: Optional[Dict[str, Any]] = None
    last_login_at: Optional[datetime] = None
    organizations: List[OrganizationBasic] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserBulkCreateResponse(BaseModel):
    """Schema for bulk creation response."""
    
    created: List[UserResponse]
    failed: List[Dict[str, Any]]
    total_created: int
    total_failed: int


# Keep existing schemas for backward compatibility
class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email."""
        return v.lower().strip()


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token", serialization_alias="access_token")
    refresh_token: str = Field(..., description="JWT refresh token", serialization_alias="refresh_token")
    token_type: str = Field(default="bearer", description="Token type", serialization_alias="token_type")
    expires_in: int = Field(..., description="Token expiration time in seconds", serialization_alias="expires_in")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


# ========================================
# Auth Response Schemas (camelCase)
# ========================================

class AuthOrganizationItem(BaseModel):
    """Organization item with counts for auth response."""

    id: UUID
    name: str
    slug: str
    logo_url: Optional[str] = None
    role: str
    members_count: int = 0
    projects_count: int = 0
    departments_count: int = 0

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class AuthUserResponse(BaseModel):
    """User response for auth endpoints with organizations."""

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    timezone: str
    language: str
    status: str
    is_active: bool
    has_organization: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    organizations: List[AuthOrganizationItem] = Field(default_factory=list)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class AuthResponse(BaseModel):
    """Schema for authentication response with user data."""

    user: AuthUserResponse
    access_token: str = Field(..., serialization_alias="access_token")
    refresh_token: str = Field(..., serialization_alias="refresh_token")
    token_type: str = Field(default="bearer", serialization_alias="token_type")
    expires_in: int = Field(..., serialization_alias="expires_in")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class UserUpdateRequest(UserUpdate):
    """Legacy alias if needed."""
    pass


# ========================================
# Organization Users Response (DB Function)
# ========================================

class OrganizationUserItem(BaseModel):
    """Schema for user item returned by fn_get_organization_users_json."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None
    status: str
    role: str
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class PaginationCursor(BaseModel):
    """Cursor for pagination."""

    id: Optional[UUID] = None
    ts: Optional[datetime] = None


class OrganizationUsersRequest(BaseModel):
    """Request schema for listing organization users."""

    limit: int = Field(default=20, ge=1, le=100, description="Max results 1-100")
    nextCursor: Optional[PaginationCursor] = Field(default=None, description="Pagination cursor")
    search: Optional[str] = Field(default=None, description="Search by name or email")
    
    # Filtros avanzados
    status: Optional[List[str]] = Field(default=None, description="Filter by user status (active, pending_activation, inactive)")
    role: Optional[List[str]] = Field(default=None, description="Filter by organization role (owner, admin, manager, employee, member)")
    is_active: Optional[bool] = Field(default=None, description="Filter by active/inactive status")
    created_from: Optional[datetime] = Field(default=None, description="Filter users created from this date")
    created_to: Optional[datetime] = Field(default=None, description="Filter users created until this date")
    
    # Deprecated (mantener para compatibilidad)
    include_inactive: bool = Field(default=False, description="[DEPRECATED] Use isActive instead. Include inactive users")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate status values."""
        if v is None:
            return None
        valid_statuses = {"active", "pending_activation", "inactive"}
        for status in v:
            if status not in valid_statuses:
                raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")
        # Remove duplicates
        return list(set(v))
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate role values."""
        if v is None:
            return None
        valid_roles = {"owner", "admin", "manager", "employee", "member"}
        for role in v:
            if role not in valid_roles:
                raise ValueError(f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}")
        # Remove duplicates
        return list(set(v))
    
    @field_validator("created_to")
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate that created_to is after created_from."""
        if v is None:
            return None
        created_from = info.data.get("created_from")
        if created_from and v < created_from:
            raise ValueError("createdTo must be greater than or equal to createdFrom")
        return v


class OrganizationUsersMeta(BaseModel):
    """Meta information for organization users response."""

    user_role: str
    can_see_emails: bool
    organization_id: UUID

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class OrganizationUsersPagination(BaseModel):
    """Pagination info for organization users response."""

    count: int
    limit: int
    has_more: bool
    next_cursor: Optional[PaginationCursor] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class UserStatsByRole(BaseModel):
    """User counts by role."""
    
    owner: int = 0
    admin: int = 0
    manager: int = 0
    employee: int = 0
    member: int = 0

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class UserStatsByStatus(BaseModel):
    """User counts by status."""
    
    active: int = 0
    pending_activation: int = 0
    inactive: int = 0

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class OrganizationUsersStats(BaseModel):
    """Statistics for organization users."""
    
    total_users: int = Field(..., description="Total users matching filters")
    active_users: int = Field(..., description="Users with status 'active'")
    pending_activation: int = Field(..., description="Users with status 'pending_activation'")
    inactive_users: int = Field(..., description="Users with status 'inactive'")
    by_role: UserStatsByRole = Field(..., description="User counts by role")
    by_status: UserStatsByStatus = Field(..., description="User counts by status")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class OrganizationUsersResponse(BaseModel):
    """Response schema for organization users with cursor pagination and statistics."""

    success: bool = True
    data: List[Optional[OrganizationUserItem]]
    meta: OrganizationUsersMeta
    stats: OrganizationUsersStats
    pagination: OrganizationUsersPagination

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
