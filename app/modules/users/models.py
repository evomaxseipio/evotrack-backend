"""User model for authentication and user management."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime, Enum as SQLEnum, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserStatus(str, enum.Enum):
    """User account status."""
    PENDING_ACTIVATION = "pending_activation"  # Created by admin, awaiting activation
    ACTIVE = "active"  # Account activated, can login
    INACTIVE = "inactive"  # Deactivated by admin


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary key as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL for pending users
    
    # Profile information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    identification = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    nationality = Column(String(100), nullable=True)
    
    # Settings
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    preferences = Column(JSONB, nullable=True)
    
    # Department assignment
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    
    # Status and activation
    status = Column(
        SQLEnum(UserStatus),
        default=UserStatus.PENDING_ACTIVATION,
        nullable=False,
        index=True
    )
    activation_token = Column(String(255), nullable=True, unique=True, index=True)
    activation_token_expires = Column(DateTime, nullable=True)
    
    # Email verification (complementary to activation)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Legacy field (for backward compatibility)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    
    # Relationships
    # organization_memberships = relationship("UserOrganization", back_populates="user")
    department = relationship("Department", foreign_keys=[department_id])
    
    def __repr__(self) -> str:
        return f"<User {self.email} ({self.status.value})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def can_login(self) -> bool:
        """Check if user can login."""
        return self.status == UserStatus.ACTIVE and self.password_hash is not None
    
    @property
    def is_pending(self) -> bool:
        """Check if user is pending activation."""
        return self.status == UserStatus.PENDING_ACTIVATION
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "language": self.language,
            "timezone": self.timezone,
            "status": self.status.value,
            "can_login": self.can_login,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }
