"""Repository for User database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.users.models import User
from app.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model database operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address (case-insensitive)
        
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(
            User.email == email.lower()
        ).first()
    
    def get_by_uuid(self, user_id: UUID) -> Optional[User]:
        """
        Get user by UUID.
        
        Args:
            user_id: User UUID
        
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email address to check
        
        Returns:
            True if email exists, False otherwise
        """
        return self.db.query(User).filter(
            User.email == email.lower()
        ).count() > 0
    
    def get_active_users(self, skip: int = 0, limit: int = 100):
        """
        Get all active users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of active users
        """
        return self.db.query(User).filter(
            User.is_active == True
        ).offset(skip).limit(limit).all()
    
    def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate user (soft delete).
        
        Args:
            user_id: User UUID
        
        Returns:
            Updated user or None if not found
        """
        user = self.get_by_uuid(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Activate user.
        
        Args:
            user_id: User UUID
        
        Returns:
            Updated user or None if not found
        """
        user = self.get_by_uuid(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
        return user
