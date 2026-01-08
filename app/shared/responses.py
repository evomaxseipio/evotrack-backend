"""Standardized API response formats."""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field


T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""
    
    success: bool = Field(default=True, description="Indicates successful operation")
    message: str = Field(description="Success message")
    data: T = Field(description="Response data")


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    
    success: bool = Field(default=False, description="Indicates failed operation")
    error: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class MessageResponse(BaseModel):
    """Simple message response."""
    
    success: bool = Field(default=True)
    message: str = Field(description="Response message")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    success: bool = Field(default=True)
    data: List[T] = Field(description="List of items")
    pagination: Dict[str, Any] = Field(description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response with metadata."""
        total_pages = (total + page_size - 1) // page_size
        
        return cls(
            data=items,
            pagination={
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        )


def success_response(data: Any, message: str = "Operation successful") -> Dict[str, Any]:
    """Create success response dictionary."""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(
    error: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create error response dictionary."""
    response = {
        "success": False,
        "error": error
    }
    if error_code:
        response["error_code"] = error_code
    if details:
        response["details"] = details
    return response
