"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.modules.auth.dependencies import CurrentUser, get_auth_service
from app.modules.auth.service import AuthService
from app.modules.users.schemas import (
    AuthResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.shared.responses import MessageResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account and return authentication tokens"
)
def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """
    Register a new user.
    
    **Request Body:**
    - **email**: Valid email address (unique)
    - **password**: Minimum 8 characters with at least one letter and number
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **timezone**: User's timezone (default: UTC)
    
    **Returns:**
    - User information
    - Access token (JWT)
    - Refresh token (JWT)
    - Token expiration time
    
    **Errors:**
    - **400**: Email already exists
    - **422**: Validation errors (invalid email, weak password, etc.)
    """
    return auth_service.register_user(user_data)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User login",
    description="Authenticate user and return tokens"
)
def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """
    Authenticate user with email and password.
    
    **Request Body:**
    - **email**: User's email address
    - **password**: User's password
    
    **Returns:**
    - User information
    - Access token (JWT)
    - Refresh token (JWT)
    - Token expiration time
    
    **Errors:**
    - **401**: Invalid credentials or inactive account
    """
    return auth_service.login(credentials)


@router.post(
    "/login/form",
    response_model=AuthResponse,
    summary="User login (OAuth2 compatible)",
    description="Authenticate user using OAuth2 password flow"
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """
    OAuth2-compatible login endpoint.
    
    This endpoint follows OAuth2 password flow specification and is compatible
    with tools like Swagger UI's "Authorize" button.
    
    **Form Data:**
    - **username**: User's email address
    - **password**: User's password
    
    **Returns:**
    - User information
    - Access token (JWT)
    - Refresh token (JWT)
    """
    credentials = UserLogin(email=form_data.username, password=form_data.password)
    return auth_service.login(credentials)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generate new access token using refresh token"
)
def refresh_token(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Refresh access token.
    
    Use a valid refresh token to generate a new access token without
    requiring the user to log in again.
    
    **Request Body:**
    - **refresh_token**: Valid JWT refresh token
    
    **Returns:**
    - New access token
    - Same refresh token
    - Token expiration time
    
    **Errors:**
    - **401**: Invalid or expired refresh token
    """
    return auth_service.refresh_access_token(refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
def get_current_user_info(
    current_user: CurrentUser
) -> UserResponse:
    """
    Get current user information.
    
    This endpoint requires authentication. Include the access token in the
    Authorization header: `Authorization: Bearer <token>`
    
    **Returns:**
    - Current user's information
    
    **Errors:**
    - **401**: Not authenticated or invalid token
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout current user (client-side token invalidation)"
)
def logout(
    current_user: CurrentUser
) -> MessageResponse:
    """
    Logout current user.
    
    Note: Since we're using stateless JWT tokens, actual logout is handled
    client-side by removing the tokens. This endpoint mainly serves as a
    standard REST endpoint and could be extended for token blacklisting.
    
    **Returns:**
    - Success message
    
    **Errors:**
    - **401**: Not authenticated
    """
    return MessageResponse(
        success=True,
        message="Successfully logged out"
    )
