"""Authentication service with business logic."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    AuthResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.shared.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    UnauthorizedException,
)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def register_user(self, user_data: UserCreate) -> AuthResponse:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
        
        Returns:
            AuthResponse with user data and tokens
        
        Raises:
            AlreadyExistsException: If email already exists
        """
        # Check if email already exists
        if self.user_repository.email_exists(user_data.email):
            raise AlreadyExistsException("User", "email", user_data.email)
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["password_hash"] = password_hash
        user_dict["email"] = user_data.email.lower()  # Normalize email
        
        user = self.user_repository.create(user_dict)
        
        # Generate tokens
        tokens = self._generate_tokens(user.id)
        
        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def login(self, credentials: UserLogin) -> AuthResponse:
        """
        Authenticate user and generate tokens.
        
        Args:
            credentials: User login credentials
        
        Returns:
            AuthResponse with user data and tokens
        
        Raises:
            UnauthorizedException: If credentials are invalid
        """
        # Get user by email
        user = self.user_repository.get_by_email(credentials.email)
        
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")
        
        # Generate tokens
        tokens = self._generate_tokens(user.id)
        
        return AuthResponse(
            user=UserResponse.model_validate(user),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            TokenResponse with new access token
        
        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        from app.core.security import decode_token
        
        # Decode refresh token
        payload = decode_token(refresh_token)
        
        if not payload:
            raise UnauthorizedException("Invalid refresh token")
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")
        
        # Verify user exists and is active
        user = self.user_repository.get_by_uuid(UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")
        
        # Generate new access token
        access_token = create_access_token({"sub": user_id, "type": "access"})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def get_current_user(self, user_id: UUID) -> User:
        """
        Get current user by ID.
        
        Args:
            user_id: User UUID
        
        Returns:
            User object
        
        Raises:
            NotFoundException: If user not found
            UnauthorizedException: If user is inactive
        """
        user = self.user_repository.get_by_uuid(user_id)
        
        if not user:
            raise NotFoundException("User", user_id)
        
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")
        
        return user
    
    def _generate_tokens(self, user_id: UUID) -> dict:
        """
        Generate access and refresh tokens.
        
        Args:
            user_id: User UUID
        
        Returns:
            Dictionary with access_token and refresh_token
        """
        user_id_str = str(user_id)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_id_str, "type": "access"}
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            data={"sub": user_id_str, "type": "refresh"}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
