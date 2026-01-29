"""Authentication service with business logic."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.modules.users.models import User, UserStatus
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    AuthResponse,
    OrganizationBasic,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.modules.organizations.repository import OrganizationRepository
from app.shared.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    UnauthorizedException,
    ValidationException
)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, user_repository: UserRepository, organization_repository: OrganizationRepository):
        self.user_repository = user_repository
        self.organization_repository = organization_repository
    
    def register_user(self, user_data: UserCreate) -> AuthResponse:
        """
        Register a new user (Self-registration).
        """
        # Check if email already exists
        if self.user_repository.email_exists(user_data.email):
            raise AlreadyExistsException("User", "email", user_data.email)
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user (Self-reg is ACTIVE immediately unless email verification is enforced)
        user_dict = {
            "email": user_data.email.lower(),
            "password_hash": password_hash,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "timezone": user_data.timezone,
            "status": UserStatus.ACTIVE,
            "is_active": True,
            "activated_at": datetime.utcnow(),
            "email_verified": False  # Could be handled by email verification flow
        }
        
        user = self.user_repository.create(user_dict)
        
        # Generate tokens
        tokens = self._generate_tokens(user.id)
        
        # Get user organizations (should be empty for new self-reg)
        organizations = self._get_user_organizations(user.id)
        
        # Build response
        user_response = self._build_user_response(user)
        
        return AuthResponse(
            user=user_response,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def login(self, credentials: UserLogin) -> AuthResponse:
        """
        Authenticate user and generate tokens.
        """
        # Get user by email
        user = self.user_repository.get_by_email(credentials.email)
        
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        # Check if user can login (status + has password)
        if not user.can_login:
            if user.status == UserStatus.PENDING_ACTIVATION:
                raise UnauthorizedException("Account is pending activation. Please check your email.")
            elif user.status == UserStatus.INACTIVE:
                raise UnauthorizedException("Account is inactive. Please contact support.")
            else:
                raise UnauthorizedException("Cannot login to this account.")
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        self.user_repository.db.commit()
        
        # Generate tokens
        tokens = self._generate_tokens(user.id)
        
        # Build user response
        user_response = self._build_user_response(user)
        
        return AuthResponse(
            user=user_response,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token from refresh token.
        """
        from app.core.security import decode_token
        
        # Decode refresh token
        payload = decode_token(refresh_token)
        
        if not payload:
            raise UnauthorizedException("Invalid refresh token")
        
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")
        
        # Verify user exists and can login
        user = self.user_repository.get_by_uuid(UUID(user_id))
        if not user or not user.can_login:
            raise UnauthorizedException("User not found or cannot login")
        
        # Generate new access token
        access_token = create_access_token({"sub": user_id, "type": "access"})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def get_current_user(self, user_id: UUID) -> User:
        """
        Get current user by ID and verify they can login.
        """
        user = self.user_repository.get_by_uuid(user_id)
        
        if not user:
            raise NotFoundException("User", user_id)
        
        if not user.can_login:
            raise UnauthorizedException("User account status prevents login.")
        
        return user
    
    def _get_user_organizations(self, user_id: UUID) -> List[OrganizationBasic]:
        """
        Get user's organizations with roles.
        """
        orgs_with_roles = self.organization_repository.get_user_organizations_with_roles(user_id)
        
        organizations = []
        for org, role in orgs_with_roles:
            role_str = role.value if hasattr(role, 'value') else str(role)
            organizations.append(
                OrganizationBasic(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    role=role_str
                )
            )
        
        return organizations
    
    def _build_user_response(self, user: User) -> UserResponse:
        """
        Build UserResponse.
        """
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            phone=user.phone,
            language=user.language,
            timezone=user.timezone,
            status=user.status.value,
            can_login=user.can_login,
            created_at=user.created_at,
            activated_at=user.activated_at
        )
    
    def _generate_tokens(self, user_id: UUID) -> dict:
        """
        Generate tokens.
        """
        user_id_str = str(user_id)
        return {
            "access_token": create_access_token(data={"sub": user_id_str, "type": "access"}),
            "refresh_token": create_refresh_token(data={"sub": user_id_str, "type": "refresh"})
        }
