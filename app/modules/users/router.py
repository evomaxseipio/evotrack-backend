"""User profile API endpoints (self-service)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, status

from app.modules.users.dependencies import (
    get_user_service,
    get_current_user,
    CurrentUser
)
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    UserDetailResponse,
    ProfileUpdate,
    PasswordChange
)
from app.modules.users.models import User
from app.shared.responses import MessageResponse

router = APIRouter()


# ========================================
# Profile Endpoints
# ========================================

@router.get(
    "/me",
    response_model=UserDetailResponse,
    summary="Get my profile",
    description="Get current user's detailed profile"
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
) -> UserDetailResponse:
    """
    Get current user profile.
    
    **Requires**: Authentication
    
    **Returns**: Current user details including preferences
    """
    return UserDetailResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserDetailResponse,
    summary="Update my profile",
    description="Update current user's profile information"
)
def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserDetailResponse:
    """
    Update own profile.
    
    **Request Body:**
    - **first_name**: Optional first name
    - **last_name**: Optional last name
    - **phone**: Optional phone number
    - **timezone**: Optional timezone
    - **language**: Optional language code
    - **preferences**: Optional JSON preferences
    
    **Requires**: Authentication
    
    **Returns**: Updated profile
    """
    user = service.update_my_profile(current_user.id, profile_data)
    return UserDetailResponse.model_validate(user)


@router.put(
    "/me/password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change current user's password"
)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> MessageResponse:
    """
    Change password.
    
    **Request Body:**
    - **current_password**: Current password
    - **new_password**: New password (min 8 chars, letter + number)
    
    **Requires**: Authentication
    
    **Returns**: Success message
    
    **Errors:**
    - **400**: Invalid current password
    - **422**: Weak new password
    """
    service.change_password(current_user.id, password_data)
    
    return MessageResponse(
        success=True,
        message="Password changed successfully"
    )


@router.post(
    "/me/avatar",
    response_model=UserDetailResponse,
    summary="Upload avatar",
    description="Upload user avatar image"
)
async def upload_avatar(
    file: UploadFile = File(..., description="Avatar image (jpg/png, max 2MB)"),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserDetailResponse:
    """
    Upload avatar.
    
    **Form Data:**
    - **file**: Image file (jpg, png, webp, max 2MB)
    
    **Requires**: Authentication
    
    **Returns**: Updated user with avatar URL
    """
    file_content = await file.read()
    user = service.upload_avatar(current_user.id, file_content, file.filename or "avatar.jpg")
    return UserDetailResponse.model_validate(user)


@router.delete(
    "/me/avatar",
    response_model=MessageResponse,
    summary="Remove avatar",
    description="Remove user avatar"
)
def remove_avatar(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> MessageResponse:
    """
    Remove avatar.
    
    **Requires**: Authentication
    
    **Returns**: Success message
    """
    service.update_avatar(current_user.id, None)
    
    return MessageResponse(
        success=True,
        message="Avatar removed successfully"
    )
