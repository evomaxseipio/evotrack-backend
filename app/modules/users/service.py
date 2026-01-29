"""User service with business logic."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from app.modules.users.models import User, UserStatus
from app.modules.users.repository import UserRepository
from app.modules.organizations.models import OrganizationRole
from app.modules.organizations.repository import UserOrganizationRepository
from app.modules.users.schemas import (
    UserCreateByAdmin,
    UserUpdate,
    ProfileUpdate,
    PasswordChange,
    UserActivation
)
from app.shared.exceptions import (
    NotFoundException,
    AlreadyExistsException,
    ValidationException,
    ForbiddenException,
    UnauthorizedException
)
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for user management operations."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        user_org_repository: UserOrganizationRepository
    ):
        self.user_repository = user_repository
        self.user_org_repository = user_org_repository
    
    # ========================================
    # User Creation (Admin)
    # ========================================
    
    def create_user_by_admin(
        self,
        organization_id: UUID,
        user_data: UserCreateByAdmin,
        created_by: User
    ) -> User:
        """
        Create user by admin (without password).
        
        User is created in pending_activation state.
        Activation email is sent if requested.
        
        Args:
            organization_id: Organization UUID
            user_data: User creation data
            created_by: Admin creating the user
            
        Returns:
            Created user
            
        Raises:
            AlreadyExistsException: If email already exists
        """
        # Check if email exists
        if self.user_repository.email_exists(user_data.email):
            raise AlreadyExistsException("User", "email", user_data.email)
        
        # Generate activation token
        activation_token = str(uuid4())
        
        # Create user
        user_dict = {
            "email": user_data.email.lower(),
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "phone": user_data.phone,
            "timezone": user_data.timezone,
            "language": user_data.language,
            "status": UserStatus.PENDING_ACTIVATION,
            "password_hash": None,  # No password yet
            "activation_token": activation_token,
        }
        
        user = self.user_repository.create(user_dict)
        
        # Set activation token expiry (72 hours default)
        self.user_repository.set_activation_token(user.id, activation_token)
        
        # Create User-Organization membership
        self.user_org_repository.create_membership(
            user_id=user.id,
            organization_id=organization_id,
            role=OrganizationRole.EMPLOYEE
        )
        
        # TODO: Send activation email if requested
        if user_data.send_activation_email:
            self._send_activation_email(user, activation_token)
        
        return user
    
    def create_users_bulk(
        self,
        organization_id: UUID,
        users_data: List[UserCreateByAdmin],
        created_by: User
    ) -> dict:
        """
        Create multiple users in bulk.
        
        Args:
            organization_id: Organization UUID
            users_data: List of user data
            created_by: Admin creating users
            
        Returns:
            Dictionary with created and failed users
        """
        created = []
        failed = []
        
        for user_data in users_data:
            try:
                user = self.create_user_by_admin(
                    organization_id,
                    user_data,
                    created_by
                )
                created.append(user)
            except Exception as e:
                failed.append({
                    "email": user_data.email,
                    "error": str(e)
                })
        
        return {
            "created": created,
            "failed": failed,
            "total_created": len(created),
            "total_failed": len(failed)
        }
    
    # ========================================
    # User Activation
    # ========================================
    
    def activate_user_account(
        self,
        activation_data: UserActivation
    ) -> User:
        """
        Activate user account with token and password.
        
        Args:
            activation_data: Activation data with token and password
            
        Returns:
            Activated user
            
        Raises:
            NotFoundException: If token invalid or expired
            ValidationException: If user already active
        """
        # Get user by token
        user = self.user_repository.get_by_activation_token(
            activation_data.token
        )
        
        if not user:
            raise NotFoundException(
                "Activation token",
                "Token is invalid or has expired"
            )
        
        # Check if already active
        if user.status == UserStatus.ACTIVE:
            raise ValidationException("Account is already activated")
        
        # Set password
        user.password_hash = get_password_hash(activation_data.password)
        user.status = UserStatus.ACTIVE
        user.is_active = True
        user.activated_at = datetime.utcnow()
        
        # Clear activation token
        self.user_repository.clear_activation_token(user.id)
        
        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)
        
        return user
    
    def resend_activation_email(self, email: str) -> bool:
        """
        Resend activation email to user.
        
        Args:
            email: User email
            
        Returns:
            True if sent
            
        Raises:
            NotFoundException: If user not found
            ValidationException: If user already active
        """
        user = self.user_repository.get_by_email(email)
        
        if not user:
            raise NotFoundException("User", email)
        
        if user.status == UserStatus.ACTIVE:
            raise ValidationException("User is already active")
        
        # Generate new token if expired
        if not user.activation_token:
            token = str(uuid4())
            self.user_repository.set_activation_token(user.id, token)
        else:
            token = user.activation_token
        
        # Send email
        self._send_activation_email(user, token)
        
        return True
    
    # ========================================
    # User Queries
    # ========================================
    
    def get_user(self, user_id: UUID) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User object
            
        Raises:
            NotFoundException: If user not found
        """
        user = self.user_repository.get_by_uuid(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        return user
    
    def get_organization_users(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[UserStatus] = None
    ) -> List[User]:
        """
        Get users in organization with filters.
        """
        return self.user_repository.get_organization_users(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status
        )

    def get_organization_users_json(
        self,
        organization_id: UUID,
        current_user_id: UUID,
        limit: int = 20,
        cursor: Optional[dict] = None,
        include_inactive: bool = False,
        search: Optional[str] = None
    ) -> dict:
        """
        Get users in organization using database function.

        Args:
            organization_id: Organization UUID
            current_user_id: Current user UUID
            limit: Max results (default: 20)
            cursor: Pagination cursor
            include_inactive: Include inactive users
            search: Search term

        Returns:
            Dictionary with users and pagination info
        """
        return self.user_repository.get_organization_users_json(
            organization_id=organization_id,
            current_user_id=current_user_id,
            limit=limit,
            cursor=cursor,
            include_inactive=include_inactive,
            search=search
        )
    
    def search_users(
        self,
        organization_id: UUID,
        search_term: str,
        limit: int = 10
    ) -> List[User]:
        """
        Search users by name or email within an organization.
        """
        return self.user_repository.get_organization_users(
            organization_id=organization_id,
            search=search_term,
            limit=limit
        )
    
    # ========================================
    # User Updates (Admin)
    # ========================================
    
    def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        current_user: User
    ) -> User:
        """
        Update user information (admin).
        """
        user = self.get_user(user_id)
        
        # Update fields
        update_dict = user_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)
        
        return user
    
    def deactivate_user(
        self,
        user_id: UUID,
        current_user: User
    ) -> User:
        """
        Deactivate user (soft delete).
        """
        if user_id == current_user.id:
            raise ValidationException(
                "You cannot deactivate your own account"
            )
        
        user = self.user_repository.deactivate_user(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        
        return user
    
    def reactivate_user(
        self,
        user_id: UUID,
        current_user: User
    ) -> User:
        """
        Reactivate deactivated user.
        """
        user = self.user_repository.activate_user(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        
        return user
    
    # ========================================
    # Profile Management (Self)
    # ========================================
    
    def update_my_profile(
        self,
        user_id: UUID,
        profile_data: ProfileUpdate
    ) -> User:
        """
        Update current user's profile.
        """
        user = self.get_user(user_id)
        
        update_dict = profile_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)
        
        return user
    
    def change_password(
        self,
        user_id: UUID,
        password_data: PasswordChange
    ) -> bool:
        """
        Change user password.
        """
        user = self.get_user(user_id)
        
        # Verify current password
        if not verify_password(
            password_data.current_password,
            user.password_hash
        ):
            raise UnauthorizedException("Current password is incorrect")
        
        # Update password
        user.password_hash = get_password_hash(password_data.new_password)
        
        self.user_repository.db.commit()
        
        return True
    
    def update_avatar(
        self,
        user_id: UUID,
        avatar_url: str
    ) -> User:
        """
        Update user avatar.
        """
        user = self.get_user(user_id)
        user.avatar_url = avatar_url
        
        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)
        
        return user
    
    # ========================================
    # Statistics
    # ========================================
    
    def get_user_stats(self, organization_id: UUID) -> dict:
        """
        Get user statistics for organization.
        """
        return self.user_repository.get_organization_user_stats(organization_id)
    
    # ========================================
    # Private Helpers
    # ========================================
    
    def _send_activation_email(self, user: User, token: str) -> None:
        """
        Send activation email to user.
        
        Args:
            user: User object
            token: Activation token
        """
        # TODO: Implement email sending
        activation_link = f"https://app.evotrack.com/activate/{token}"
        
        print(f"📧 Sending activation email to {user.email}")
        print(f"   Link: {activation_link}")
        
    def upload_avatar(
        self,
        user_id: UUID,
        file_content: bytes,
        filename: str
    ) -> User:
        """
        Upload and save user avatar.
        (Preserved from previous implementation)
        """
        from pathlib import Path
        from app.core.config import settings
        
        # Validate file size (2MB max)
        MAX_SIZE = 2 * 1024 * 1024  # 2MB
        if len(file_content) > MAX_SIZE:
            raise ValidationException("File size exceeds maximum allowed size of 2MB")
        
        # Validate file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise ValidationException(
                f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR) / "avatars"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename: {user_id}.{ext}
        avatar_filename = f"{user_id}{file_ext}"
        avatar_path = upload_dir / avatar_filename
        
        # Save file
        with open(avatar_path, 'wb') as f:
            f.write(file_content)
        
        # Update user avatar_url
        avatar_url = f"/uploads/avatars/{avatar_filename}"
        return self.update_avatar(user_id, avatar_url)