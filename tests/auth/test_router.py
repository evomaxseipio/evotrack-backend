"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.modules.users.models import User


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_user_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe",
            "timezone": "America/New_York"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        user = data["user"]
        assert user["email"] == user_data["email"].lower()
        assert user["first_name"] == user_data["first_name"]
        assert user["last_name"] == user_data["last_name"]
        assert user["timezone"] == user_data["timezone"]
        assert user["is_active"] is True
        assert "id" in user
        assert "password" not in user
        assert "password_hash" not in user
    
    def test_register_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Register first user
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to register with same email
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 409  # Conflict
        assert "already exists" in response2.json()["error"].lower()
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email."""
        user_data = {
            "email": "not-an-email",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        user_data = {
            "email": "user@example.com",
            "password": "weak",  # Too short
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_password_no_number(self, client: TestClient):
        """Test registration with password without number."""
        user_data = {
            "email": "user@example.com",
            "password": "OnlyLetters",  # No number
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        response = client.post("/api/v1/auth/register", json={
            "email": "user@example.com"
            # Missing password, first_name, last_name
        })
        
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint."""
    
    @pytest.fixture
    def registered_user(self, client: TestClient):
        """Create and return a registered user."""
        user_data = {
            "email": "logintest@example.com",
            "password": "TestPass123",
            "first_name": "Login",
            "last_name": "Test"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        return {**user_data, **response.json()}
    
    def test_login_success(self, client: TestClient, registered_user):
        """Test successful login."""
        credentials = {
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == credentials["email"]
    
    def test_login_wrong_password(self, client: TestClient, registered_user):
        """Test login with wrong password."""
        credentials = {
            "email": registered_user["email"],
            "password": "WrongPassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["error"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent email."""
        credentials = {
            "email": "nonexistent@example.com",
            "password": "SomePass123"
        }
        
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == 401
    
    def test_login_case_insensitive_email(self, client: TestClient, registered_user):
        """Test that email is case-insensitive."""
        credentials = {
            "email": registered_user["email"].upper(),
            "password": registered_user["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == 200


class TestCurrentUser:
    """Test get current user endpoint."""
    
    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """Create user and return auth headers."""
        user_data = {
            "email": "authtest@example.com",
            "password": "TestPass123",
            "first_name": "Auth",
            "last_name": "Test"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_current_user_success(self, client: TestClient, auth_headers):
        """Test getting current user info with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "email" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "id" in data
        assert "password" not in data
    
    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401


class TestRefreshToken:
    """Test refresh token endpoint."""
    
    @pytest.fixture
    def tokens(self, client: TestClient):
        """Create user and return tokens."""
        user_data = {
            "email": "refresh@example.com",
            "password": "TestPass123",
            "first_name": "Refresh",
            "last_name": "Test"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        return response.json()
    
    def test_refresh_token_success(self, client: TestClient, tokens):
        """Test refreshing access token."""
        refresh_token = tokens["refresh_token"]
        
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # Should return new access token but same refresh token
        assert data["refresh_token"] == refresh_token
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401


class TestLogout:
    """Test logout endpoint."""
    
    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """Create user and return auth headers."""
        user_data = {
            "email": "logout@example.com",
            "password": "TestPass123",
            "first_name": "Logout",
            "last_name": "Test"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "logged out" in data["message"].lower()
    
    def test_logout_no_token(self, client: TestClient):
        """Test logout without token."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401
