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

    # ========================================
    # Database Functions
    # ========================================

    def get_organization_users_json(
        self,
        organization_id: UUID,
        current_user_id: UUID,
        limit: int = 20,
        cursor: Optional[dict] = None,
        include_inactive: bool = False,
        search: Optional[str] = None,
        status_filter: Optional[list] = None,
        role_filter: Optional[list] = None,
        is_active_filter: Optional[bool] = None,
        created_from: Optional[str] = None,
        created_to: Optional[str] = None
    ) -> dict:
        """
        Get organization users using the database function fn_get_organization_users_json.

        Args:
            organization_id: Organization UUID
            current_user_id: Current user UUID (for permissions)
            limit: Max results (default: 20)
            cursor: Cursor for pagination (JSONB)
            include_inactive: Include inactive users (default: False) [DEPRECATED]
            search: Search term for name/email
            status_filter: Filter by user status (active, pending_activation, inactive)
            role_filter: Filter by organization role (owner, admin, manager, employee)
            is_active_filter: Filter by active/inactive status
            created_from: Filter users created from this date
            created_to: Filter users created until this date

        Returns:
            Dictionary with users data, stats, and pagination info
        """
        import json

        # Prepare cursor as JSON string or NULL
        cursor_json = json.dumps(cursor) if cursor else None

        sql = text("""
            SELECT fn_get_organization_users_json(
                :org_id,
                :current_user_id,
                :limit,
                CAST(:cursor AS jsonb),
                :include_inactive,
                :search,
                :status_filter,
                :role_filter,
                :is_active_filter,
                CAST(:created_from AS timestamptz),
                CAST(:created_to AS timestamptz)
            )
        """)

        result = self.db.execute(sql, {
            "org_id": organization_id,
            "current_user_id": current_user_id,
            "limit": limit,
            "cursor": cursor_json,
            "include_inactive": include_inactive,
            "search": search,
            "status_filter": status_filter,
            "role_filter": role_filter,
            "is_active_filter": is_active_filter,
            "created_from": created_from,
            "created_to": created_to
        })

        json_result = result.scalar()

        # Parse JSON result if it's a string
        if isinstance(json_result, str):
            json_result = json.loads(json_result)

        if not json_result:
            return {
                "success": False,
                "data": [],
                "meta": {"userRole": "member", "canSeeEmails": False, "organizationId": str(organization_id)},
                "stats": {
                    "totalUsers": 0,
                    "activeUsers": 0,
                    "pendingActivation": 0,
                    "inactiveUsers": 0,
                    "byRole": {"owner": 0, "admin": 0, "manager": 0, "employee": 0},
                    "byStatus": {"active": 0, "pendingActivation": 0, "inactive": 0}
                },
                "pagination": {"count": 0, "limit": limit, "hasMore": False, "nextCursor": None}
            }

        # Filter None values from data array
        if "data" in json_result:
            json_result["data"] = [user for user in json_result["data"] if user is not None]

        return json_result

    def get_user_auth_response(self, user_id: UUID) -> dict:
        """
        Get user auth response with organization data using database function.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with user data including organizations with counts
        """
        import json
        
        sql = text("SELECT fn_get_user_auth_response(:user_id)")
        result = self.db.execute(sql, {"user_id": user_id})
        json_result = result.scalar()

        # Parse JSON result if it's a string
        if isinstance(json_result, str):
            json_result = json.loads(json_result)

        if not json_result:
            return {"success": False, "data": {}}

        return json_result

    def get_user_with_organizations(self, org_id: UUID, user_id: UUID = None, email: str = None) -> Optional[dict]:
        """
        Get user with organization details using the database function fn_get_user_with_organizations.

        Args:
            org_id: Organization UUID (mandatory)
            user_id: User UUID (optional, use either user_id or email, not both)
            email: User email (optional, use either user_id or email, not both)

        Returns:
            Dictionary with user and organization data or None if not found
        """
        import json
        from app.modules.users.models import User
        from app.modules.organizations.models import UserOrganization, Organization

        try:
            sql = text("""
                SELECT fn_get_user_with_organizations(
                    :org_id,
                    :user_id,
                    :email
                )
            """)

            result = self.db.execute(sql, {
                "org_id": org_id,
                "user_id": user_id,
                "email": email
            })
            json_result = result.scalar()

            # Parse JSON result if it's a string
            if json_result is not None:
                if isinstance(json_result, str):
                    json_result = json.loads(json_result)
                return json_result
            
            return None
        except Exception:
            # Fallback implementation if function doesn't exist
            # Get user by either ID or email
            user = None
            if user_id:
                # Join with UserOrganization to ensure user is in the specified org
                user = (
                    self.db.query(User)
                    .join(UserOrganization, User.id == UserOrganization.user_id)
                    .filter(User.id == user_id)
                    .filter(UserOrganization.organization_id == org_id)
                    .filter(UserOrganization.is_active == True)
                    .first()
                )
            elif email:
                user = (
                    self.db.query(User)
                    .join(UserOrganization, User.id == UserOrganization.user_id)
                    .filter(User.email == email.lower())
                    .filter(UserOrganization.organization_id == org_id)
                    .filter(UserOrganization.is_active == True)
                    .first()
                )
            
            if not user:
                return None
            
            # Get user's role in this specific organization
            user_org = (
                self.db.query(UserOrganization)
                .filter(UserOrganization.user_id == user.id)
                .filter(UserOrganization.organization_id == org_id)
                .filter(UserOrganization.is_active == True)
                .first()
            )
            
            # Get all organizations the user belongs to
            all_orgs = (
                self.db.query(Organization, UserOrganization.role)
                .join(UserOrganization, Organization.id == UserOrganization.organization_id)
                .filter(UserOrganization.user_id == user.id)
                .filter(UserOrganization.is_active == True)
                .all()
            )
            
            # Format the response similar to what the function would return
            user_data = {
                "id": str(user.id) if hasattr(user, 'id') and user.id else None,
                "email": getattr(user, 'email', ''),
                "firstName": getattr(user, 'first_name', ''),
                "lastName": getattr(user, 'last_name', ''),
                "fullName": getattr(user, 'full_name', ''),
                "avatarUrl": getattr(user, 'avatar_url', None),
                "phone": getattr(user, 'phone', None),
                "language": getattr(user, 'language', 'en'),
                "timezone": getattr(user, 'timezone', 'UTC'),
                "status": getattr(user.status, 'value', '') if hasattr(user, 'status') else '',
                "isActive": getattr(user, 'is_active', True),
                "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                "activatedAt": user.activated_at.isoformat() if hasattr(user, 'activated_at') and user.activated_at else None,
                "roleInOrg": user_org.role.value if user_org and hasattr(user_org, 'role') and hasattr(user_org.role, 'value') else None,
                "departmentId": str(user.department_id) if hasattr(user, 'department_id') and user.department_id else None,
                "departmentName": user.department.name if hasattr(user, 'department') and user.department and hasattr(user.department, 'name') else None
            }
            
            organizations = []
            for org, role in all_orgs:
                organizations.append({
                    "id": str(org.id) if hasattr(org, 'id') and org.id else None,
                    "name": getattr(org, 'name', ''),
                    "slug": getattr(org, 'slug', ''),
                    "role": role.value if hasattr(role, 'value') else str(role) if role else '',
                    "isPrimary": org.id == org_id if hasattr(org, 'id') else False  # Mark the requested org as primary
                })
            
            return {
                "user": user_data,
                "organizations": organizations,
                "organizationDetails": {
                    "id": str(org_id),
                    "role": user_org.role.value if user_org and hasattr(user_org, 'role') and hasattr(user_org.role, 'value') else None,
                    "canAccessSensitiveData": user_org.role in ['OWNER', 'ADMIN'] if user_org and hasattr(user_org, 'role') else False
                }
            }