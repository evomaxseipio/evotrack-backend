"""Team models for organizational structure."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Team(Base):
    """Team model within departments."""
    
    __tablename__ = "teams"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    team_lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Team details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department", back_populates="teams")
    team_lead = relationship("User", foreign_keys=[team_lead_id], backref="led_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Team {self.name}>"
    
    def to_dict(self) -> dict:
        """Convert team to dictionary."""
        return {
            "id": str(self.id),
            "department_id": str(self.department_id),
            "team_lead_id": str(self.team_lead_id) if self.team_lead_id else None,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TeamMember(Base):
    """Join table for Team-User many-to-many relationship."""
    
    __tablename__ = "team_members"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Member details
    role = Column(String(100), nullable=True)  # Role within the team
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", backref="team_memberships")
    
    def __repr__(self) -> str:
        return f"<TeamMember team_id={self.team_id} user_id={self.user_id}>"
    
    def to_dict(self) -> dict:
        """Convert team member to dictionary."""
        return {
            "id": str(self.id),
            "team_id": str(self.team_id),
            "user_id": str(self.user_id),
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }
