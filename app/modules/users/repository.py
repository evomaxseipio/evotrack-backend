"""Repository for User database operations."""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.modules.users.models import User, UserStatus
from app.modules.organizations.models import UserOrganization, OrganizationRole
from app.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model database operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    # ========================================
    # Basic Queries
    # ========================================
    
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
    
    # ========================================
    # Status-based Queries
    # ========================================
    
    def get_by_status(
        self,
        status: UserStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get users by status.
        
        Args:
            status: User status to filter
            skip: Pagination offset
            limit: Max results
        
        Returns:
            List of users
        """
        return self.db.query(User).filter(
            User.status == status
        ).offset(skip).limit(limit).all()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of active users
        """
        return self.db.query(User).filter(
            User.status == UserStatus.ACTIVE
        ).offset(skip).limit(limit).all()
    
    def get_pending_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users pending activation.
        
        Args:
            skip: Pagination offset
            limit: Max results
        
        Returns:
            List of pending users
        """
        return self.get_by_status(UserStatus.PENDING_ACTIVATION, skip, limit)
    
    # ========================================
    # Search and Filter
    # ========================================
    
    def search_users(
        self,
        search_term: str,
        status: Optional[UserStatus] = None,
        limit: int = 10
    ) -> List[User]:
        """
        Search users by name or email.
        
        Args:
            search_term: Search query
            status: Optional status filter
            limit: Max results
        
        Returns:
            List of matching users
        """
        query = self.db.query(User)
        
        # Search filter
        search_filter = or_(
            User.email.ilike(f"%{search_term}%"),
            User.first_name.ilike(f"%{search_term}%"),
            User.last_name.ilike(f"%{search_term}%")
        )
        query = query.filter(search_filter)
        
        # Status filter
        if status:
            query = query.filter(User.status == status)
        
        return query.limit(limit).all()
    
    def get_organization_users(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        role: Optional[OrganizationRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """
        Get users by organization with filters.
        """
        query = (
            self.db.query(User)
            .join(UserOrganization, User.id == UserOrganization.user_id)
            .filter(UserOrganization.organization_id == organization_id)
            .filter(UserOrganization.is_active == True)
        )
        
        # Apply filters
        if role is not None:
            query = query.filter(UserOrganization.role == role)
        
        if status is not None:
            query = query.filter(User.status == status)
        
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
        
        # Apply pagination and ordering
        users = (
            query.order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return users
    
    # ========================================
    # Status Management
    # ========================================
    
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
            user.status = UserStatus.INACTIVE
            user.is_active = False  # Legacy field
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Activate user (change status to active).
        
        Args:
            user_id: User UUID
        
        Returns:
            Updated user or None if not found
        """
        user = self.get_by_uuid(user_id)
        if user:
            user.status = UserStatus.ACTIVE
            user.is_active = True  # Legacy field
            if not user.activated_at:
                user.activated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user
    
    # ========================================
    # Activation Token Management
    # ========================================
    
    def get_by_activation_token(self, token: str) -> Optional[User]:
        """
        Get user by activation token.
        
        Args:
            token: Activation token
        
        Returns:
            User or None if not found/expired
        """
        user = self.db.query(User).filter(
            User.activation_token == token,
            User.activation_token_expires > datetime.utcnow()
        ).first()
        
        return user
    
    def set_activation_token(self, user_id: UUID, token: str, expires_hours: int = 72) -> Optional[User]:
        """
        Set activation token for user.
        
        Args:
            user_id: User UUID
            token: Activation token
            expires_hours: Token validity in hours
        
        Returns:
            Updated user
        """
        user = self.get_by_uuid(user_id)
        if user:
            user.activation_token = token
            user.activation_token_expires = datetime.utcnow() + timedelta(hours=expires_hours)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def clear_activation_token(self, user_id: UUID) -> Optional[User]:
        """
        Clear activation token after successful activation.
        
        Args:
            user_id: User UUID
        
        Returns:
            Updated user
        """
        user = self.get_by_uuid(user_id)
        if user:
            user.activation_token = None
            user.activation_token_expires = None
            self.db.commit()
            self.db.refresh(user)
        return user
    
    # ========================================
    # Bulk Operations
    # ========================================
    
    def create_bulk(self, users_data: List[dict]) -> List[User]:
        """
        Create multiple users in single transaction.
        
        Args:
            users_data: List of user data dictionaries
        
        Returns:
            List of created users
        """
        users = []
        for data in users_data:
            user = User(**data)
            self.db.add(user)
            users.append(user)
        
        self.db.commit()
        
        for user in users:
            self.db.refresh(user)
        
        return users
    
    # ========================================
    # Stored Procedures (Inherited from previous task)
    # ========================================
    
    def create_via_sp(
        self,
        email: str,
        password_hash: Optional[str],
        first_name: str,
        last_name: str,
        timezone: str = "UTC"
    ) -> Optional[User]:
        """
        Create a new user using the stored procedure 'create_user_sp'.
        """
        sql = text("SELECT create_user_sp(:email, :password_hash, :first_name, :last_name, :timezone)")
        result = self.db.execute(sql, {
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "timezone": timezone
        })
        user_id = result.scalar()
        if user_id:
            return self.get_by_uuid(user_id)
        return None

    def update_via_sp(
        self,
        user_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> bool:
        """
        Update user fields using the stored procedure 'update_user_sp'.
        """
        sql = text("SELECT update_user_sp(:user_id, :first_name, :last_name, :email)")
        result = self.db.execute(sql, {
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email
        })
        return result.scalar() or False

    # ========================================
    # Statistics
    # ========================================
    
    def count_by_status(self, status: UserStatus) -> int:
        """
        Count users by status.
        
        Args:
            status: User status
        
        Returns:
            Count of users
        """
        return self.db.query(User).filter(User.status == status).count()
    
    def get_user_stats(self) -> dict:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user counts by status
        """
        return {
            "total": self.db.query(User).count(),
            "active": self.count_by_status(UserStatus.ACTIVE),
            "pending": self.count_by_status(UserStatus.PENDING_ACTIVATION),
            "inactive": self.count_by_status(UserStatus.INACTIVE)
        }

    def get_organization_user_stats(self, organization_id: UUID) -> dict:
        """
        Get user statistics for a specific organization.
        """
        base_query = (
            self.db.query(User)
            .join(UserOrganization, User.id == UserOrganization.user_id)
            .filter(UserOrganization.organization_id == organization_id)
            .filter(UserOrganization.is_active == True)
        )
        
        return {
            "total": base_query.count(),
            "active": base_query.filter(User.status == UserStatus.ACTIVE).count(),
            "pending": base_query.filter(User.status == UserStatus.PENDING_ACTIVATION).count(),
            "inactive": base_query.filter(User.status == UserStatus.INACTIVE).count()
        }

    def get_user_organizations_shared(
        self,
        user_id: UUID,
        requester_id: UUID
    ) -> List[UUID]:
        """
        Get organization IDs shared between user and requester.
        """
        # Get user's organizations
        user_orgs = (
            self.db.query(UserOrganization.organization_id)
            .filter(UserOrganization.user_id == user_id)
            .filter(UserOrganization.is_active == True)
            .subquery()
        )
        
        # Get requester's organizations
        requester_orgs = (
            self.db.query(UserOrganization.organization_id)
            .filter(UserOrganization.user_id == requester_id)
            .filter(UserOrganization.is_active == True)
            .subquery()
        )
        
        # Find intersection
        shared = (
            self.db.query(user_orgs.c.organization_id)
            .join(
                requester_orgs,
                user_orgs.c.organization_id == requester_orgs.c.organization_id
            )
            .all()
        )
        
        return [org_id[0] for org_id in shared]