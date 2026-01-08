"""Shared utilities and common code."""

from app.shared.exceptions import (
    EvoTrackException,
    NotFoundException,
    AlreadyExistsException,
    UnauthorizedException,
    ForbiddenException,
    ValidationException,
    DatabaseException,
    BusinessLogicException,
)
from app.shared.responses import (
    SuccessResponse,
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    success_response,
    error_response,
)
from app.shared.pagination import (
    PaginationParams,
    Page,
    paginate,
)
from app.shared.utils import (
    to_utc,
    from_utc,
    now_utc,
    sanitize_filename,
    snake_to_camel,
    camel_to_snake,
    generate_unique_code,
    truncate_text,
    format_currency,
)

__all__ = [
    # Exceptions
    "EvoTrackException",
    "NotFoundException",
    "AlreadyExistsException",
    "UnauthorizedException",
    "ForbiddenException",
    "ValidationException",
    "DatabaseException",
    "BusinessLogicException",
    # Responses
    "SuccessResponse",
    "ErrorResponse",
    "MessageResponse",
    "PaginatedResponse",
    "success_response",
    "error_response",
    # Pagination
    "PaginationParams",
    "Page",
    "paginate",
    # Utils
    "to_utc",
    "from_utc",
    "now_utc",
    "sanitize_filename",
    "snake_to_camel",
    "camel_to_snake",
    "generate_unique_code",
    "truncate_text",
    "format_currency",
]
