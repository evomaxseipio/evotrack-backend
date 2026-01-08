"""Common utility functions."""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import pytz


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def from_utc(dt: datetime, tz: str = "UTC") -> datetime:
    """Convert UTC datetime to specific timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    target_tz = pytz.timezone(tz)
    return dt.astimezone(target_tz)


def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    return filename


def snake_to_camel(snake_str: str) -> str:
    """
    Convert snake_case to camelCase.
    
    Args:
        snake_str: String in snake_case
    
    Returns:
        String in camelCase
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    Convert camelCase to snake_case.
    
    Args:
        camel_str: String in camelCase
    
    Returns:
        String in snake_case
    """
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', camel_str).lower()


def dict_to_camel(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from snake_case to camelCase."""
    return {snake_to_camel(key): value for key, value in data.items()}


def dict_to_snake(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from camelCase to snake_case."""
    return {camel_to_snake(key): value for key, value in data.items()}


def generate_unique_code(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique alphanumeric code.
    
    Args:
        prefix: Optional prefix for the code
        length: Length of random part
    
    Returns:
        Unique code string
    """
    import secrets
    import string
    
    alphabet = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return f"{prefix}{random_part}" if prefix else random_part


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_currency(
    amount: float,
    currency: str = "USD",
    locale: str = "en_US"
) -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code (USD, EUR, etc.)
        locale: Locale for formatting
    
    Returns:
        Formatted currency string
    """
    # Simple implementation - can be enhanced with babel library
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "MXN": "$",
        "BRL": "R$",
        "COP": "$",
        "DOP": "RD$"
    }
    
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"
