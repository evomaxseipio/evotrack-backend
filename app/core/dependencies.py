from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> int:
    """
    Get current user ID from JWT token.
    
    Args:
        token: JWT access token
        db: Database session
    
    Returns:
        User ID
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    return int(user_id)


async def get_current_active_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current active user from database.
    Will be implemented after User model is created.
    
    Args:
        user_id: User ID from token
        db: Database session
    
    Returns:
        User object
    
    Raises:
        HTTPException: If user not found or inactive
    """
    # TODO: Implement after User model is created
    # from app.modules.users.models import User
    # user = db.query(User).filter(User.id == user_id).first()
    # if user is None or not user.is_active:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return user
    
    return {"id": user_id, "message": "User retrieval to be implemented"}
