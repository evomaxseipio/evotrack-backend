"""Pagination utilities for database queries."""

from typing import Any, Generic, List, TypeVar
from sqlalchemy.orm import Query
from pydantic import BaseModel, Field


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for requests."""
    
    page: int = Field(default=1, ge=1, description="Page number (starts at 1)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def skip(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class Page(Generic[T]):
    """Generic pagination container."""
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
    
    def dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous
        }


def paginate(
    query: Query,
    params: PaginationParams
) -> Page[Any]:
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query to paginate
        params: Pagination parameters
    
    Returns:
        Page object with items and metadata
    """
    total = query.count()
    items = query.offset(params.skip).limit(params.limit).all()
    
    return Page(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size
    )
