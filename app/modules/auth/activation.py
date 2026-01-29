"""User account activation endpoints."""

from fastapi import APIRouter, Depends, status

from app.modules.users.dependencies import get_user_service
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    UserActivation,
    ResendActivation,
    AuthResponse,
    UserResponse
)
from app.shared.responses import MessageResponse

router = APIRouter()


@router.post(
    "/activate",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate user account",
    description="Activate account with token and set password"
)
def activate_account(
    activation_data: UserActivation,
    service: UserService = Depends(get_user_service)
) -> AuthResponse:
    """
    Activate user account.
    
    User clicks link in activation email and sets password.
    After activation, user can login immediately.
    
    **Request Body:**
    - **token**: Activation token from email
    - **password**: Password to set (min 8 chars, letter + number)
    
    **Returns**: 
    - User information
    - Access token (user is automatically logged in)
    - Refresh token
    
    **Note**: This is a public endpoint (no auth required)
    """
    user = service.activate_user_account(activation_data)
    
    # Ideally inject AuthService properly, but for now we'll import it here
    # to avoid circular dependencies if any.
    from app.modules.auth.service import AuthService
    from app.modules.users.repository import UserRepository
    from app.modules.organizations.repository import OrganizationRepository
    from app.core.database import SessionLocal
    
    # Use a new session for generating tokens if needed, 
    # but preferably we should use the existing one from the service.
    # For now, let's assume we can create a temporary auth service.
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        org_repo = OrganizationRepository(db)
        auth_service = AuthService(user_repo, org_repo)
        
        # Generate tokens
        tokens = auth_service._generate_tokens(user.id)
        
        # Get user organizations
        organizations = auth_service._get_user_organizations(user.id)
        
        # Build user response
        user_response = auth_service._build_user_response(user, organizations)
        
        from app.core.config import settings
        
        return AuthResponse(
            user=user_response,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    finally:
        db.close()


@router.post(
    "/resend-activation",
    response_model=MessageResponse,
    summary="Resend activation email",
    description="Resend activation email to user"
)
def resend_activation_email(
    resend_data: ResendActivation,
    service: UserService = Depends(get_user_service)
) -> MessageResponse:
    """
    Resend activation email.
    
    **Request Body:**
    - **email**: User email address
    
    **Returns**: Success message
    """
    service.resend_activation_email(resend_data.email)
    
    return MessageResponse(
        success=True,
        message="Activation email sent successfully"
    )
