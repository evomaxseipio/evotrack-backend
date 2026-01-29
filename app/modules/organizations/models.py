"""Organization models for multi-tenancy."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime, Enum as SQLEnum, ForeignKey, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class OrganizationRole(str, enum.Enum):
    """Roles for users within an organization."""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class OrganizationRoleType(TypeDecorator):
    """Custom type to ensure enum values (lowercase) are used instead of enum names."""
    impl = String
    cache_ok = True
    
    def __init__(self):
        super().__init__(length=20)
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value (lowercase string) before inserting."""
        if value is None:
            return value
        if isinstance(value, OrganizationRole):
            return value.value  # Returns "owner", "admin", etc.
        return value
    
    def process_result_value(self, value, dialect):
        """Convert string value back to enum when reading."""
        if value is None:
            return value
        return OrganizationRole(value)




class Organization(Base):
    """Organization model for multi-tenancy."""
    
    __tablename__ = "organizations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Organization details
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    tax_id = Column(String(50), unique=True, nullable=False, index=True)  # RNC, EIN, NIT, etc.
    timezone = Column(String(50), default="UTC", nullable=False)
    currency_code = Column(String(3), default="USD", nullable=False)  # ISO 4217
    logo_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="organization")
    
    def __repr__(self) -> str:
        return f"<Organization {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert organization to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "tax_id": self.tax_id,
            "timezone": self.timezone,
            "currency_code": self.currency_code,
            "logo_url": self.logo_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserOrganization(Base):
    """Association table between Users and Organizations with roles."""
    
    __tablename__ = "user_organizations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Role - Using custom type to ensure lowercase values are stored
    role = Column(OrganizationRoleType(), nullable=False, default=OrganizationRole.EMPLOYEE)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="user_organizations")
    organization = relationship("Organization", back_populates="user_organizations")
    
    def __repr__(self) -> str:
        return f"<UserOrganization user_id={self.user_id} org_id={self.organization_id} role={self.role}>"

class InvitationStatus(str, enum.Enum):
    """Status for organization invitations."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InvitationStatusType(TypeDecorator):
    """Custom type to ensure enum values (lowercase) are used instead of enum names."""
    impl = String
    cache_ok = True
    
    def __init__(self):
        super().__init__(length=20)
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value (lowercase string) before inserting."""
        if value is None:
            return value
        if isinstance(value, InvitationStatus):
            return value.value  # Returns "pending", "accepted", etc.
        return value
    
    def process_result_value(self, value, dialect):
        """Convert string value back to enum when reading."""
        if value is None:
            return value
        return InvitationStatus(value)


class Invitation(Base):
    """Invitation model for organization membership."""
    
    __tablename__ = "invitations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    role = Column(OrganizationRoleType(), nullable=False, default=OrganizationRole.EMPLOYEE)
    token = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    status = Column(InvitationStatusType(), nullable=False, default=InvitationStatus.PENDING)
    
    # Expiration
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = relationship("Organization")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    def __repr__(self) -> str:
        return f"<Invitation {self.email} to {self.organization_id}>"
    
    def is_expired(self) -> bool:
        """Check if invitation is expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> dict:
        """Convert invitation to dictionary."""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "email": self.email,
            "role": self.role.value,
            "token": str(self.token),
            "status": self.status.value,
            "invited_by": str(self.invited_by),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }