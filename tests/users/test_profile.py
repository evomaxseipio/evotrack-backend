"""Tests for user profile management endpoints."""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from pathlib import Path
import os


class TestGetMyProfile:
    """Test GET /api/v1/users/me endpoint."""
    
    @pytest.fixture
    def setup_user_and_org(self, client: TestClient):
        """Create user and organization for testing."""
        # Register user
        user_data = {
            "email": "profile@example.com",
            "password": "TestPass123",
            "first_name": "Profile",
            "last_name": "User"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = response.json()["user"]["id"]
        
        # Create organization
        org_response = client.post(
            "/api/v1/organizations/",
            json={"name": "Profile Org", "tax_id": "111222333"},
            headers=headers
        )
        org_id = org_response.json()["id"]
        
        return headers, user_id, org_id
    
    def test_get_my_profile_success(self, client: TestClient, setup_user_and_org):
        """Test successful retrieval of own profile."""
        headers, user_id, org_id = setup_user_and_org
        
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "profile@example.com"
        assert data["first_name"] == "Profile"
        assert data["last_name"] == "User"
        assert "organizations" in data
        assert len(data["organizations"]) == 1
        assert data["organizations"][0]["id"] == org_id
        assert data["organizations"][0]["role"] == "owner"
    
    def test_get_my_profile_without_auth(self, client: TestClient):
        """Test getting profile without authentication."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401


class TestUpdateMyProfile:
    """Test PUT /api/v1/users/me endpoint."""
    
    @pytest.fixture
    def setup_user(self, client: TestClient):
        """Create user for testing."""
        user_data = {
            "email": "updateprofile@example.com",
            "password": "TestPass123",
            "first_name": "Update",
            "last_name": "Profile"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = response.json()["user"]["id"]
        
        return headers, user_id
    
    def test_update_my_profile_success(self, client: TestClient, setup_user):
        """Test successful profile update."""
        headers, user_id = setup_user
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+1234567890",
            "language": "es",
            "timezone": "America/New_York"
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["phone"] == "+1234567890"
        assert data["language"] == "es"
        assert data["timezone"] == "America/New_York"
        # Email should not change
        assert data["email"] == "updateprofile@example.com"
    
    def test_update_my_profile_partial(self, client: TestClient, setup_user):
        """Test partial profile update."""
        headers, user_id = setup_user
        
        update_data = {
            "phone": "+9876543210"
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+9876543210"
        # Other fields should remain unchanged
        assert data["first_name"] == "Update"
        assert data["last_name"] == "Profile"
    
    def test_update_my_profile_with_preferences(self, client: TestClient, setup_user):
        """Test updating profile with preferences."""
        headers, user_id = setup_user
        
        update_data = {
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "language": "en"
            }
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferences"]["theme"] == "dark"
        assert data["preferences"]["notifications"] is True
    
    def test_update_my_profile_without_auth(self, client: TestClient):
        """Test updating profile without authentication."""
        update_data = {"first_name": "Test"}
        
        response = client.put("/api/v1/users/me", json=update_data)
        
        assert response.status_code == 401


class TestUploadAvatar:
    """Test POST /api/v1/users/me/avatar endpoint."""
    
    @pytest.fixture
    def setup_user(self, client: TestClient):
        """Create user for testing."""
        user_data = {
            "email": "avatar@example.com",
            "password": "TestPass123",
            "first_name": "Avatar",
            "last_name": "User"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = response.json()["user"]["id"]
        
        return headers, user_id
    
    def test_upload_avatar_success_png(self, client: TestClient, setup_user):
        """Test successful avatar upload (PNG)."""
        headers, user_id = setup_user
        
        # Create a simple PNG file (1x1 pixel PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {"file": ("avatar.png", BytesIO(png_data), "image/png")}
        
        response = client.post("/api/v1/users/me/avatar", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
        assert data["avatar_url"] is not None
        assert data["avatar_url"].startswith("/uploads/avatars/")
        assert str(user_id) in data["avatar_url"]
    
    def test_upload_avatar_success_jpg(self, client: TestClient, setup_user):
        """Test successful avatar upload (JPG)."""
        headers, user_id = setup_user
        
        # Create a simple JPG file (minimal valid JPEG)
        jpg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xff\xd9'
        
        files = {"file": ("avatar.jpg", BytesIO(jpg_data), "image/jpeg")}
        
        response = client.post("/api/v1/users/me/avatar", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
        assert data["avatar_url"] is not None
    
    def test_upload_avatar_invalid_format(self, client: TestClient, setup_user):
        """Test avatar upload with invalid file format."""
        headers, user_id = setup_user
        
        # Create a text file (invalid format)
        text_data = b"This is not an image"
        
        files = {"file": ("avatar.txt", BytesIO(text_data), "text/plain")}
        
        response = client.post("/api/v1/users/me/avatar", files=files, headers=headers)
        
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["error"]
    
    def test_upload_avatar_too_large(self, client: TestClient, setup_user):
        """Test avatar upload with file too large."""
        headers, user_id = setup_user
        
        # Create a file larger than 2MB
        large_data = b"x" * (3 * 1024 * 1024)  # 3MB
        
        files = {"file": ("avatar.png", BytesIO(large_data), "image/png")}
        
        response = client.post("/api/v1/users/me/avatar", files=files, headers=headers)
        
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["error"].lower()
    
    def test_upload_avatar_without_auth(self, client: TestClient):
        """Test avatar upload without authentication."""
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {"file": ("avatar.png", BytesIO(png_data), "image/png")}
        
        response = client.post("/api/v1/users/me/avatar", files=files)
        
        assert response.status_code == 401


class TestChangePassword:
    """Test PUT /api/v1/users/me/password endpoint."""
    
    @pytest.fixture
    def setup_user(self, client: TestClient):
        """Create user for testing."""
        user_data = {
            "email": "password@example.com",
            "password": "TestPass123",
            "first_name": "Password",
            "last_name": "User"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = response.json()["user"]["id"]
        
        return headers, user_id
    
    def test_change_password_success(self, client: TestClient, setup_user):
        """Test successful password change."""
        headers, user_id = setup_user
        
        password_data = {
            "current_password": "TestPass123",
            "new_password": "NewPass456"
        }
        
        response = client.put("/api/v1/users/me/password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "changed successfully" in data["message"].lower()
        
        # Verify new password works by logging in
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "password@example.com", "password": "NewPass456"}
        )
        assert login_response.status_code == 200
    
    def test_change_password_wrong_current(self, client: TestClient, setup_user):
        """Test password change with wrong current password."""
        headers, user_id = setup_user
        
        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPass456"
        }
        
        response = client.put("/api/v1/users/me/password", json=password_data, headers=headers)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["error"].lower()
    
    def test_change_password_weak_new(self, client: TestClient, setup_user):
        """Test password change with weak new password."""
        headers, user_id = setup_user
        
        password_data = {
            "current_password": "TestPass123",
            "new_password": "weak"
        }
        
        response = client.put("/api/v1/users/me/password", json=password_data, headers=headers)
        
        assert response.status_code == 422
        # Should have validation error
        errors = response.json()["details"]["errors"]
        assert any("password" in str(error).lower() for error in errors)
    
    def test_change_password_no_letter(self, client: TestClient, setup_user):
        """Test password change with password that has no letter."""
        headers, user_id = setup_user
        
        password_data = {
            "current_password": "TestPass123",
            "new_password": "12345678"
        }
        
        response = client.put("/api/v1/users/me/password", json=password_data, headers=headers)
        
        assert response.status_code == 422
    
    def test_change_password_no_number(self, client: TestClient, setup_user):
        """Test password change with password that has no number."""
        headers, user_id = setup_user
        
        password_data = {
            "current_password": "TestPass123",
            "new_password": "Password"
        }
        
        response = client.put("/api/v1/users/me/password", json=password_data, headers=headers)
        
        assert response.status_code == 422
    
    def test_change_password_without_auth(self, client: TestClient):
        """Test password change without authentication."""
        password_data = {
            "current_password": "TestPass123",
            "new_password": "NewPass456"
        }
        
        response = client.put("/api/v1/users/me/password", json=password_data)
        
        assert response.status_code == 401
