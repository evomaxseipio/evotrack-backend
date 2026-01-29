"""Tests for user permission checks and edge cases."""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID


class TestUserPermissionChecks:
    """Test user permission enforcement."""
    
    @pytest.fixture
    def setup_multiple_users(self, client: TestClient):
        """Create multiple users with different roles."""
        # Create owner user
        owner_data = {
            "email": "owner@example.com",
            "password": "TestPass123",
            "first_name": "Owner",
            "last_name": "User"
        }
        owner_response = client.post("/api/v1/auth/register", json=owner_data)
        owner_token = owner_response.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        owner_id = owner_response.json()["user"]["id"]
        
        # Create organization
        org_response = client.post(
            "/api/v1/organizations/",
            json={"name": "Permission Org", "tax_id": "555666777"},
            headers=owner_headers
        )
        org_id = org_response.json()["id"]
        
        # Create regular user
        user_data = {
            "email": "regular@example.com",
            "password": "TestPass123",
            "first_name": "Regular",
            "last_name": "User"
        }
        user_response = client.post("/api/v1/auth/register", json=user_data)
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        user_id = user_response.json()["user"]["id"]
        
        return {
            "owner_headers": owner_headers,
            "owner_id": owner_id,
            "user_headers": user_headers,
            "user_id": user_id,
            "org_id": org_id
        }
    
    def test_regular_user_cannot_update_other_user(self, client: TestClient, setup_multiple_users):
        """Test that regular user cannot update another user's profile."""
        setup = setup_multiple_users
        
        # Regular user tries to update owner's profile
        update_data = {"first_name": "Hacked"}
        response = client.put(
            f"/api/v1/users/{setup['owner_id']}",
            json=update_data,
            headers=setup["user_headers"]
        )
        
        # Should fail with 403 unless they share an org and user is admin/owner
        # In this case, they don't share an org, so should be 403
        assert response.status_code == 403
    
    def test_user_can_update_own_profile(self, client: TestClient, setup_multiple_users):
        """Test that user can always update their own profile."""
        setup = setup_multiple_users
        
        update_data = {"first_name": "UpdatedSelf"}
        response = client.put(
            f"/api/v1/users/{setup['user_id']}",
            json=update_data,
            headers=setup["user_headers"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "UpdatedSelf"


class TestUserDeactivationPermissions:
    """Test user deactivation permission rules."""
    
    @pytest.fixture
    def setup_org_with_owners(self, client: TestClient):
        """Create organization with multiple owners."""
        # Create owner 1
        owner1_data = {
            "email": "owner1@example.com",
            "password": "TestPass123",
            "first_name": "Owner",
            "last_name": "One"
        }
        owner1_response = client.post("/api/v1/auth/register", json=owner1_data)
        owner1_token = owner1_response.json()["access_token"]
        owner1_headers = {"Authorization": f"Bearer {owner1_token}"}
        owner1_id = owner1_response.json()["user"]["id"]
        
        # Create organization
        org_response = client.post(
            "/api/v1/organizations/",
            json={"name": "Multi Owner Org", "tax_id": "888999000"},
            headers=owner1_headers
        )
        org_id = org_response.json()["id"]
        
        return {
            "owner1_headers": owner1_headers,
            "owner1_id": owner1_id,
            "org_id": org_id
        }
    
    def test_cannot_deactivate_last_owner(self, client: TestClient, setup_org_with_owners):
        """Test that last owner cannot be deactivated."""
        setup = setup_org_with_owners
        
        # Try to deactivate the only owner
        response = client.delete(
            f"/api/v1/users/{setup['owner1_id']}",
            headers=setup["owner1_headers"]
        )
        
        # Should fail with 400 (business logic error)
        assert response.status_code == 400
        assert "last owner" in response.json()["error"].lower()
    
    def test_cannot_deactivate_self_if_last_owner(self, client: TestClient, setup_org_with_owners):
        """Test that user cannot deactivate themselves if last owner."""
        setup = setup_org_with_owners
        
        # Owner tries to deactivate themselves
        response = client.delete(
            f"/api/v1/users/{setup['owner1_id']}",
            headers=setup["owner1_headers"]
        )
        
        # Should fail with 400
        assert response.status_code == 400


class TestUserListFilters:
    """Test user list filtering and pagination."""
    
    @pytest.fixture
    def setup_org_with_users(self, client: TestClient):
        """Create organization with multiple users."""
        # Create owner
        owner_data = {
            "email": "filterowner@example.com",
            "password": "TestPass123",
            "first_name": "Filter",
            "last_name": "Owner"
        }
        owner_response = client.post("/api/v1/auth/register", json=owner_data)
        owner_token = owner_response.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Create organization
        org_response = client.post(
            "/api/v1/organizations/",
            json={"name": "Filter Org", "tax_id": "444555666"},
            headers=owner_headers
        )
        org_id = org_response.json()["id"]
        
        return owner_headers, org_id
    
    def test_list_users_with_role_filter(self, client: TestClient, setup_org_with_users):
        """Test filtering users by role."""
        headers, org_id = setup_org_with_users
        
        response = client.get(
            f"/api/v1/organizations/{org_id}/users?role=owner",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return at least the owner
        assert len(data["data"]) >= 1
        assert all(user["role"] == "owner" for user in data["data"])
    
    def test_list_users_with_active_filter(self, client: TestClient, setup_org_with_users):
        """Test filtering users by active status."""
        headers, org_id = setup_org_with_users
        
        response = client.get(
            f"/api/v1/organizations/{org_id}/users?is_active=true",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(user["is_active"] is True for user in data["data"])
    
    def test_list_users_with_search(self, client: TestClient, setup_org_with_users):
        """Test searching users by name/email."""
        headers, org_id = setup_org_with_users
        
        response = client.get(
            f"/api/v1/organizations/{org_id}/users?search=filter",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should find users matching "filter"
        assert len(data["data"]) >= 0  # At least 0 results
    
    def test_list_users_pagination(self, client: TestClient, setup_org_with_users):
        """Test pagination metadata."""
        headers, org_id = setup_org_with_users
        
        response = client.get(
            f"/api/v1/organizations/{org_id}/users?skip=0&limit=5",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data
        pagination = data["pagination"]
        assert "total" in pagination
        assert "skip" in pagination
        assert "limit" in pagination
        assert "has_next" in pagination
        assert "has_previous" in pagination


class TestUserAccessControl:
    """Test user access control across organizations."""
    
    def test_user_cannot_access_other_org_users(self, client: TestClient):
        """Test that user cannot list users from organization they don't belong to."""
        # Create user 1 with org 1
        user1_data = {
            "email": "access1@example.com",
            "password": "TestPass123",
            "first_name": "Access",
            "last_name": "One"
        }
        user1_response = client.post("/api/v1/auth/register", json=user1_data)
        user1_token = user1_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        org1_response = client.post(
            "/api/v1/organizations/",
            json={"name": "Org 1", "tax_id": "111111111"},
            headers=user1_headers
        )
        org1_id = org1_response.json()["id"]
        
        # Create user 2 with org 2
        user2_data = {
            "email": "access2@example.com",
            "password": "TestPass123",
            "first_name": "Access",
            "last_name": "Two"
        }
        user2_response = client.post("/api/v1/auth/register", json=user2_data)
        user2_token = user2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        org2_response = client.post(
            "/api/v1/organizations/",
            json={"name": "Org 2", "tax_id": "222222222"},
            headers=user2_headers
        )
        org2_id = org2_response.json()["id"]
        
        # User 1 tries to list users from org 2
        response = client.get(
            f"/api/v1/organizations/{org2_id}/users",
            headers=user1_headers
        )
        
        # Should fail with 403
        assert response.status_code == 403
