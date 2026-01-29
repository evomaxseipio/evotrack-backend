"""Tests for invitation endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestInvitations:
    """Test invitation system."""
    
    @pytest.fixture
    def org_with_owner(self, client: TestClient):
        """Create organization and return owner token + org_id."""
        # Register user
        user_data = {
            "email": "owner@example.com",
            "password": "TestPass123",
            "first_name": "Owner",
            "last_name": "Test"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        
        # Create organization
        org_data = {"name": "Test Company"}
        org_response = client.post(
            "/api/v1/organizations/",
            json=org_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        org_id = org_response.json()["id"]
        
        return {"token": token, "org_id": org_id}
    
    def test_invite_member_success(self, client: TestClient, org_with_owner):
        """Test successful member invitation."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        invitation_data = {
            "email": "newmember@example.com",
            "role": "employee"
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations",
            json=invitation_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == invitation_data["email"]
        assert data["role"] == invitation_data["role"]
        assert data["status"] == "pending"
        assert "token" in data
        assert "expires_at" in data
    
    def test_list_members(self, client: TestClient, org_with_owner):
        """Test listing organization members."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        
        response = client.get(
            f"/api/v1/organizations/{org_with_owner['org_id']}/members",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1  # Owner only
        assert data[0]["role"] == "owner"


class TestBulkInvitations:
    """Test bulk invitation system."""
    
    @pytest.fixture
    def org_with_owner(self, client: TestClient):
        """Create organization and return owner token + org_id."""
        # Register user
        user_data = {
            "email": "bulkowner@example.com",
            "password": "TestPass123",
            "first_name": "Bulk",
            "last_name": "Owner"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        
        # Create organization
        org_data = {"name": "Bulk Test Company"}
        org_response = client.post(
            "/api/v1/organizations/",
            json=org_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        org_id = org_response.json()["id"]
        
        return {"token": token, "org_id": org_id}
    
    def test_bulk_invite_success(self, client: TestClient, org_with_owner):
        """Test successful bulk invitation."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        bulk_data = {
            "invitations": [
                {"email": "user1@example.com", "role": "employee"},
                {"email": "user2@example.com", "role": "manager"},
                {"email": "user3@example.com", "role": "admin"}
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["total"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        assert len(data["created"]) == 3
        assert len(data["errors"]) == 0
        
        # Verify all invitations were created
        for invitation in data["created"]:
            assert invitation["status"] == "pending"
            assert "token" in invitation
            assert invitation["organization_id"] == org_with_owner["org_id"]
    
    def test_bulk_invite_with_duplicates_in_request(self, client: TestClient, org_with_owner):
        """Test bulk invitation with duplicate emails in request."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        bulk_data = {
            "invitations": [
                {"email": "duplicate@example.com", "role": "employee"},
                {"email": "duplicate@example.com", "role": "employee"},  # Duplicate
                {"email": "unique@example.com", "role": "employee"}
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["total"] == 3
        assert data["successful"] == 1  # Only unique email
        assert data["failed"] == 2  # Two duplicates (case-insensitive)
        assert len(data["created"]) == 1
        assert len(data["errors"]) == 2
        
        # Check error messages
        error_emails = [err["email"] for err in data["errors"]]
        assert "duplicate@example.com" in error_emails
        assert any("Duplicate email" in err["error"] for err in data["errors"])
    
    def test_bulk_invite_with_existing_member(self, client: TestClient, org_with_owner):
        """Test bulk invitation when one user is already a member."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        
        # First, invite and accept one user
        single_invite = {
            "email": "existing@example.com",
            "role": "employee"
        }
        invite_response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations",
            json=single_invite,
            headers=headers
        )
        assert invite_response.status_code == 201
        
        # Register and accept invitation
        user_data = {
            "email": "existing@example.com",
            "password": "TestPass123",
            "first_name": "Existing",
            "last_name": "User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "existing@example.com", "password": "TestPass123"}
        )
        existing_token = login_response.json()["access_token"]
        
        token = invite_response.json()["token"]
        client.post(
            f"/api/v1/organizations/invitations/accept?token={token}",
            headers={"Authorization": f"Bearer {existing_token}"}
        )
        
        # Now try bulk invite including existing member
        bulk_data = {
            "invitations": [
                {"email": "existing@example.com", "role": "employee"},  # Already member
                {"email": "newuser@example.com", "role": "employee"}
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["total"] == 2
        assert data["successful"] == 1
        assert data["failed"] == 1
        assert len(data["created"]) == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["email"] == "existing@example.com"
        assert "already a member" in data["errors"][0]["error"].lower()
    
    def test_bulk_invite_with_existing_pending_invitation(self, client: TestClient, org_with_owner):
        """Test bulk invitation when one email has pending invitation."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        
        # Create a pending invitation first
        single_invite = {
            "email": "pending@example.com",
            "role": "employee"
        }
        client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations",
            json=single_invite,
            headers=headers
        )
        
        # Now try bulk invite including same email
        bulk_data = {
            "invitations": [
                {"email": "pending@example.com", "role": "employee"},  # Already pending
                {"email": "newuser@example.com", "role": "employee"}
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["total"] == 2
        assert data["successful"] == 1
        assert data["failed"] == 1
        assert len(data["created"]) == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["email"] == "pending@example.com"
        assert "pending invitation" in data["errors"][0]["error"].lower()
    
    def test_bulk_invite_with_invalid_role(self, client: TestClient, org_with_owner):
        """Test bulk invitation with invalid role."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        bulk_data = {
            "invitations": [
                {"email": "user1@example.com", "role": "invalid_role"},
                {"email": "user2@example.com", "role": "employee"}
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["total"] == 2
        assert data["successful"] == 1
        assert data["failed"] == 1
        assert len(data["created"]) == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["email"] == "user1@example.com"
        assert "invalid role" in data["errors"][0]["error"].lower()
    
    def test_bulk_invite_max_limit(self, client: TestClient, org_with_owner):
        """Test bulk invitation respects maximum limit of 50."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        
        # Try with 51 invitations (over limit)
        bulk_data = {
            "invitations": [
                {"email": f"user{i}@example.com", "role": "employee"}
                for i in range(51)
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "maximum 50" in response.json()["error"].lower()
    
    def test_bulk_invite_empty_list(self, client: TestClient, org_with_owner):
        """Test bulk invitation with empty list."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        bulk_data = {
            "invitations": []
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        # Should fail validation (min_length=1)
        assert response.status_code == 422
    
    def test_bulk_invite_unauthorized(self, client: TestClient, org_with_owner):
        """Test bulk invitation requires owner/admin role."""
        # Create a regular employee user
        user_data = {
            "email": "employee@example.com",
            "password": "TestPass123",
            "first_name": "Employee",
            "last_name": "User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "employee@example.com", "password": "TestPass123"}
        )
        employee_token = login_response.json()["access_token"]
        
        # Invite employee to org
        invite_data = {"email": "employee@example.com", "role": "employee"}
        invite_response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations",
            json=invite_data,
            headers={"Authorization": f"Bearer {org_with_owner['token']}"}
        )
        token = invite_response.json()["token"]
        
        # Accept invitation
        client.post(
            f"/api/v1/organizations/invitations/accept?token={token}",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        # Try bulk invite as employee (should fail)
        bulk_data = {
            "invitations": [
                {"email": "newuser@example.com", "role": "employee"}
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 403
        assert "only owners and admins" in response.json()["error"].lower()
    
    def test_bulk_invite_mixed_success_and_failures(self, client: TestClient, org_with_owner):
        """Test bulk invitation with mix of valid and invalid invitations."""
        headers = {"Authorization": f"Bearer {org_with_owner['token']}"}
        
        # Create one pending invitation first
        single_invite = {"email": "pending@example.com", "role": "employee"}
        client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations",
            json=single_invite,
            headers=headers
        )
        
        bulk_data = {
            "invitations": [
                {"email": "valid1@example.com", "role": "employee"},  # Valid
                {"email": "valid2@example.com", "role": "manager"},   # Valid
                {"email": "pending@example.com", "role": "employee"},  # Already pending
                {"email": "invalid_role@example.com", "role": "invalid"},  # Invalid role
                {"email": "valid3@example.com", "role": "admin"}  # Valid
            ]
        }
        
        response = client.post(
            f"/api/v1/organizations/{org_with_owner['org_id']}/invitations/bulk",
            json=bulk_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["total"] == 5
        assert data["successful"] == 3  # valid1, valid2, valid3
        assert data["failed"] == 2  # pending, invalid_role
        assert len(data["created"]) == 3
        assert len(data["errors"]) == 2
        
        # Verify created invitations
        created_emails = [inv["email"] for inv in data["created"]]
        assert "valid1@example.com" in created_emails
        assert "valid2@example.com" in created_emails
        assert "valid3@example.com" in created_emails
        
        # Verify errors
        error_emails = [err["email"] for err in data["errors"]]
        assert "pending@example.com" in error_emails
        assert "invalid_role@example.com" in error_emails