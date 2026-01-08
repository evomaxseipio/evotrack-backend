"""Tests for core functionality."""

import pytest
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.shared.exceptions import NotFoundException
from app.shared.pagination import Page, PaginationParams
from app.shared.utils import (
    format_currency,
    generate_unique_code,
    sanitize_filename,
    truncate_text,
)


class TestConfig:
    """Test configuration management."""
    
    def test_settings_loaded(self):
        """Test that settings are loaded correctly."""
        assert settings.APP_NAME == "EvoTrack"
        assert settings.APP_VERSION is not None
        assert settings.SECRET_KEY is not None
    
    def test_database_url_configured(self):
        """Test that database URL is configured."""
        assert settings.DATABASE_URL is not None
        assert "postgresql" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL


class TestSecurity:
    """Test security utilities."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)
    
    def test_create_access_token(self):
        """Test JWT access token creation."""
        data = {"sub": 123}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == 123
    
    def test_create_refresh_token(self):
        """Test JWT refresh token creation."""
        data = {"sub": 123}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        result = decode_token("invalid.token.here")
        assert result is None


class TestPagination:
    """Test pagination utilities."""
    
    def test_pagination_params(self):
        """Test pagination parameters calculation."""
        params = PaginationParams(page=2, page_size=20)
        
        assert params.skip == 20
        assert params.limit == 20
    
    def test_pagination_params_defaults(self):
        """Test pagination parameters with defaults."""
        params = PaginationParams()
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.skip == 0
    
    def test_page_metadata(self):
        """Test Page object calculates metadata correctly."""
        items = list(range(20))
        page = Page(items=items, total=100, page=2, page_size=20)
        
        assert page.total_pages == 5
        assert page.has_next is True
        assert page.has_previous is True
    
    def test_page_first_page(self):
        """Test Page object on first page."""
        items = list(range(20))
        page = Page(items=items, total=100, page=1, page_size=20)
        
        assert page.has_previous is False
        assert page.has_next is True
    
    def test_page_last_page(self):
        """Test Page object on last page."""
        items = list(range(10))
        page = Page(items=items, total=50, page=5, page_size=10)
        
        assert page.has_previous is True
        assert page.has_next is False


class TestUtils:
    """Test utility functions."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("test file.pdf") == "test_file.pdf"
        assert sanitize_filename("file@#$%.doc") == "file.doc"
        assert sanitize_filename("report   2024.xlsx") == "report_2024.xlsx"
    
    def test_truncate_text(self):
        """Test text truncation."""
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, max_length=20)
        
        assert len(result) <= 20
        assert result.endswith("...")
    
    def test_truncate_short_text(self):
        """Test that short text is not truncated."""
        text = "Short text"
        result = truncate_text(text, max_length=20)
        
        assert result == text
    
    def test_generate_unique_code(self):
        """Test unique code generation."""
        code1 = generate_unique_code()
        code2 = generate_unique_code()
        
        assert len(code1) == 8
        assert code1 != code2
    
    def test_generate_unique_code_with_prefix(self):
        """Test unique code generation with prefix."""
        code = generate_unique_code(prefix="TEST-", length=6)
        
        assert code.startswith("TEST-")
        assert len(code) == 11  # TEST- (5) + 6 random chars
    
    def test_format_currency(self):
        """Test currency formatting."""
        assert "$1,234.56" in format_currency(1234.56, "USD")
        assert "€" in format_currency(1000, "EUR")
        assert "RD$" in format_currency(5000, "DOP")


class TestExceptions:
    """Test custom exceptions."""
    
    def test_not_found_exception(self):
        """Test NotFoundException."""
        exc = NotFoundException("User", 123)
        
        assert "User" in exc.message
        assert "123" in exc.message
        assert exc.status_code == 404
