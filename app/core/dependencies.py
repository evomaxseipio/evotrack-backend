from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/form")


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> UUID:
    """
    Get current user ID from JWT token.
    
    Args:
        token: JWT access token
    
    Returns:
        User UUID
    
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
    
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    # Verify token type
    token_type = payload.get("type")
    if token_type != "access":
        raise credentials_exception
    
    try:
        return UUID(user_id_str)
    except ValueError:
        raise credentials_exception
