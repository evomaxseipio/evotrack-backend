"""Custom exceptions for the application."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from app.shared.error_codes import ErrorCode


class EvoTrackException(Exception):
    """Base exception for EvoTrack application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(EvoTrackException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, identifier: Any):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND)


class AlreadyExistsException(EvoTrackException):
    """Resource already exists exception."""
    
    def __init__(self, resource: str, field: str, value: Any):
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(message, status.HTTP_409_CONFLICT, ErrorCode.ALREADY_EXISTS)


class UnauthorizedException(EvoTrackException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized access", error_code: str = ErrorCode.UNAUTHORIZED):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, error_code)


class ForbiddenException(EvoTrackException):
    """Forbidden access exception."""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, ErrorCode.FORBIDDEN)


class ValidationException(EvoTrackException):
    """Validation error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, ErrorCode.VALIDATION_ERROR, details)


class DatabaseException(EvoTrackException):
    """Database operation exception."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.DATABASE_ERROR)


class BusinessLogicException(EvoTrackException):
    """Business logic validation exception."""
    
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, ErrorCode.BUSINESS_LOGIC_ERROR)
