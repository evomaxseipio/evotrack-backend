"""Standardized API response formats."""

from typing import Any, Dict, List, Optional, TypeVar, Generic, Union
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


# ============================================================================
# New Generic Response Schemas (following the new API structure)
# ============================================================================

class PaginationInfo(BaseModel):
    """Pagination metadata."""
    
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items per page")
    page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        total: int,
        skip: int,
        limit: int
    ) -> "PaginationInfo":
        """
        Create pagination info from skip/limit parameters.
        
        Args:
            total: Total number of items
            skip: Number of items skipped
            limit: Maximum number of items per page
        
        Returns:
            PaginationInfo instance
        """
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return cls(
            total=total,
            skip=skip,
            limit=limit,
            page=page,
            total_pages=total_pages,
            has_next=skip + limit < total,
            has_previous=skip > 0
        )


class ApiResponse(BaseModel, Generic[T]):
    """
    Generic API response wrapper following the standard structure.
    
    This is the standard response format for all API endpoints.
    """
    
    success: bool = Field(..., description="Indicates if the operation was successful")
    data: Union[T, List[T], None] = Field(..., description="Response data (can be object, list, or null)")
    messageResponse: str = Field(default="", description="Message response (title for errors, success message for success)")
    errorMessage: str = Field(default="", description="Detailed error message (empty for success)")
    
    model_config = {"json_schema_extra": {
        "example": {
            "success": True,
            "data": {},
            "messageResponse": "Operation successful",
            "errorMessage": ""
        }
    }}


class PaginatedApiResponse(BaseModel, Generic[T]):
    """
    Paginated API response wrapper following the standard structure.
    
    This is the standard response format for paginated list endpoints.
    """
    
    success: bool = Field(..., description="Indicates if the operation was successful")
    data: List[T] = Field(..., description="List of items")
    messageResponse: str = Field(default="", description="Message response (title for errors, success message for success)")
    errorMessage: str = Field(default="", description="Detailed error message (empty for success)")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")
    
    model_config = {"json_schema_extra": {
        "example": {
            "success": True,
            "data": [],
            "messageResponse": "Items retrieved successfully",
            "errorMessage": "",
            "pagination": {
                "total": 0,
                "skip": 0,
                "limit": 20,
                "page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False
            }
        }
    }}


# Helper functions for creating responses
def create_success_response(
    data: Union[T, List[T]],
    message: str = "Operation successful"
) -> ApiResponse[T]:
    """
    Create a success response.
    
    Args:
        data: Response data (can be object or list)
        message: Success message
    
    Returns:
        ApiResponse instance
    """
    return ApiResponse(
        success=True,
        data=data,
        messageResponse=message,
        errorMessage=""
    )


def create_error_response(
    message_title: str,
    error_detail: str,
    data: Optional[Any] = None
) -> ApiResponse[Any]:
    """
    Create an error response.
    
    Args:
        message_title: Error title (for messageResponse field)
        error_detail: Detailed error message (for errorMessage field)
        data: Optional data (usually null for errors)
    
    Returns:
        ApiResponse instance
    """
    return ApiResponse(
        success=False,
        data=data,
        messageResponse=message_title,
        errorMessage=error_detail
    )


def create_paginated_response(
    data: List[T],
    total: int,
    skip: int,
    limit: int,
    message: str = "Items retrieved successfully"
) -> PaginatedApiResponse[T]:
    """
    Create a paginated success response.
    
    Args:
        data: List of items
        total: Total number of items
        skip: Number of items skipped
        limit: Maximum number of items per page
        message: Success message
    
    Returns:
        PaginatedApiResponse instance
    """
    pagination = PaginationInfo.create(total=total, skip=skip, limit=limit)
    
    return PaginatedApiResponse(
        success=True,
        data=data,
        messageResponse=message,
        errorMessage="",
        pagination=pagination
    )
