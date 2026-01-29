"""Department models for organizational structure."""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, Column, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Department(Base):
    """Department model with hierarchical structure."""
    
    __tablename__ = "departments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    parent_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    department_head_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Department details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    budget = Column(Numeric(15, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="departments")
    parent_department = relationship("Department", remote_side=[id], backref="sub_departments")
    department_head = relationship("User", foreign_keys=[department_head_id], backref="headed_departments")
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Department {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert department to dictionary."""
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "parent_department_id": str(self.parent_department_id) if self.parent_department_id else None,
            "department_head_id": str(self.department_head_id) if self.department_head_id else None,
            "name": self.name,
            "description": self.description,
            "budget": float(self.budget) if self.budget else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
