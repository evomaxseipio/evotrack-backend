"""Tests for organization endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestCreateOrganization:
    """Test create organization endpoint."""
    
    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """Create user and get auth token."""
        user_data = {
            "email": "orgtest@example.com",
            "password": "TestPass123",
            "first_name": "Org",
            "last_name": "Test"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_organization_success(self, client: TestClient, auth_headers):
        """Test successful organization creation."""
        org_data = {
            "name": "Test Company",
            "timezone": "America/New_York",
            "currency_code": "USD"
        }
        
        response = client.post(
            "/api/v1/organizations/",
            json=org_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify ApiResponse structure
        assert response_data["success"] is True
        assert "data" in response_data
        assert response_data["messageResponse"] == "Organization created successfully"
        assert response_data["errorMessage"] == ""
        
        # Verify organization data
        data = response_data["data"]
        assert data["name"] == org_data["name"]
        assert data["timezone"] == org_data["timezone"]
        assert data["currency_code"] == org_data["currency_code"]
        assert "id" in data
        assert data["is_active"] is True
    
    def test_create_organization_without_auth(self, client: TestClient):
        """Test creating organization without authentication."""
        org_data = {"name": "Test Company"}
        
        response = client.post("/api/v1/organizations/", json=org_data)
        
        assert response.status_code == 401
    
    def test_create_multiple_organizations(self, client: TestClient, auth_headers):
        """Test user can create multiple organizations."""
        org1 = {"name": "Company 1"}
        org2 = {"name": "Company 2"}
        
        response1 = client.post("/api/v1/organizations/", json=org1, headers=auth_headers)
        response2 = client.post("/api/v1/organizations/", json=org2, headers=auth_headers)
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.json()["data"]["id"] != response2.json()["data"]["id"]


class TestListOrganizations:
    """Test list organizations endpoint."""
    
    @pytest.fixture
    def user_with_orgs(self, client: TestClient):
        """Create user with organizations."""
        # Register user
        user_data = {
            "email": "listtest@example.com",
            "password": "TestPass123",
            "first_name": "List",
            "last_name": "Test"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create organizations
        client.post("/api/v1/organizations/", json={"name": "Org 1"}, headers=headers)
        client.post("/api/v1/organizations/", json={"name": "Org 2"}, headers=headers)
        
        return headers
    
    def test_list_user_organizations(self, client: TestClient, user_with_orgs):
        """Test listing user's organizations."""
        response = client.get("/api/v1/organizations/", headers=user_with_orgs)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify ApiResponse structure
        assert response_data["success"] is True
        assert "data" in response_data
        assert isinstance(response_data["data"], list)
        
        # Verify organizations data
        data = response_data["data"]
        assert len(data) == 2
        assert all("id" in org for org in data)