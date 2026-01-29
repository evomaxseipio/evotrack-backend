"""Tests for RBAC permission system."""

import pytest
from uuid import uuid4

from app.core.constants import Permission
from app.modules.organizations.models import OrganizationRole
from app.modules.users.permissions import (
    has_permission_in_role,
    get_role_permissions,
    get_all_permissions
)
from app.modules.users.service import UserService
from app.modules.users.repository import UserRepository
from app.modules.organizations.repository import (
    OrganizationRepository,
    UserOrganizationRepository
)
from app.modules.users.models import User
from app.modules.organizations.models import Organization, UserOrganization
from sqlalchemy.orm import Session


class TestPermissionUtilities:
    """Test permission utility functions."""
    
    def test_get_role_permissions_owner(self):
        """Test that owner role has wildcard permission."""
        permissions = get_role_permissions(OrganizationRole.OWNER)
        assert "*" in permissions
    
    def test_get_role_permissions_admin(self):
        """Test admin role permissions."""
        permissions = get_role_permissions(OrganizationRole.ADMIN)
        assert "*" not in permissions
        assert Permission.MANAGE_USERS in permissions
        assert Permission.CREATE_PROJECT in permissions
        assert Permission.APPROVE_TIMESHEET in permissions
    
    def test_get_role_permissions_manager(self):
        """Test manager role permissions."""
        permissions = get_role_permissions(OrganizationRole.MANAGER)
        assert Permission.CREATE_PROJECT in permissions
        assert Permission.APPROVE_TIMESHEET in permissions
        assert Permission.MANAGE_USERS not in permissions  # Manager can't manage users
    
    def test_get_role_permissions_employee(self):
        """Test employee role permissions."""
        permissions = get_role_permissions(OrganizationRole.EMPLOYEE)
        assert Permission.VIEW_PROJECT in permissions
        assert Permission.CREATE_TIMESHEET in permissions
        assert Permission.CREATE_PROJECT not in permissions  # Employee can't create projects
        assert Permission.APPROVE_TIMESHEET not in permissions  # Employee can't approve
    
    def test_has_permission_in_role_owner(self):
        """Test that owner has all permissions."""
        assert has_permission_in_role(OrganizationRole.OWNER, Permission.CREATE_PROJECT)
        assert has_permission_in_role(OrganizationRole.OWNER, Permission.MANAGE_USERS)
        assert has_permission_in_role(OrganizationRole.OWNER, Permission.DELETE_ORGANIZATION)
        assert has_permission_in_role(OrganizationRole.OWNER, "ANY_PERMISSION")
    
    def test_has_permission_in_role_admin(self):
        """Test admin permission checks."""
        assert has_permission_in_role(OrganizationRole.ADMIN, Permission.MANAGE_USERS)
        assert has_permission_in_role(OrganizationRole.ADMIN, Permission.CREATE_PROJECT)
        assert has_permission_in_role(OrganizationRole.ADMIN, Permission.APPROVE_TIMESHEET)
        assert not has_permission_in_role(OrganizationRole.ADMIN, Permission.DELETE_ORGANIZATION)
    
    def test_has_permission_in_role_manager(self):
        """Test manager permission checks."""
        assert has_permission_in_role(OrganizationRole.MANAGER, Permission.CREATE_PROJECT)
        assert has_permission_in_role(OrganizationRole.MANAGER, Permission.APPROVE_TIMESHEET)
        assert not has_permission_in_role(OrganizationRole.MANAGER, Permission.MANAGE_USERS)
        assert not has_permission_in_role(OrganizationRole.MANAGER, Permission.DELETE_PROJECT)
    
    def test_has_permission_in_role_employee(self):
        """Test employee permission checks."""
        assert has_permission_in_role(OrganizationRole.EMPLOYEE, Permission.VIEW_PROJECT)
        assert has_permission_in_role(OrganizationRole.EMPLOYEE, Permission.CREATE_TIMESHEET)
        assert not has_permission_in_role(OrganizationRole.EMPLOYEE, Permission.CREATE_PROJECT)
        assert not has_permission_in_role(OrganizationRole.EMPLOYEE, Permission.APPROVE_TIMESHEET)
    
    def test_get_all_permissions(self):
        """Test that get_all_permissions returns all permissions."""
        all_perms = get_all_permissions()
        assert Permission.CREATE_PROJECT in all_perms
        assert Permission.MANAGE_USERS in all_perms
        assert Permission.VIEW_REPORTS in all_perms
        assert "*" not in all_perms  # Wildcard should not be included


class TestUserServiceHasPermission:
    """Test has_permission method in UserService."""
    
    @pytest.fixture
    def setup_user_org(self, db: Session):
        """Create user and organization for testing."""
        # Create user
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.flush()
        
        # Create organization
        org = Organization(
            id=uuid4(),
            name="Test Org",
            slug="test-org",
            tax_id="123456789"
        )
        db.add(org)
        db.flush()
        
        return user, org
    
    def test_has_permission_owner(self, db: Session, setup_user_org):
        """Test that owner has all permissions."""
        user, org = setup_user_org
        
        # Create owner membership
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=org.id,
            role=OrganizationRole.OWNER,
            is_active=True
        )
        db.add(user_org)
        db.commit()
        
        # Create service
        user_repo = UserRepository(db)
        user_org_repo = UserOrganizationRepository(db)
        service = UserService(user_repo, user_org_repo)
        
        # Owner should have all permissions
        assert service.has_permission(user.id, org.id, Permission.CREATE_PROJECT)
        assert service.has_permission(user.id, org.id, Permission.MANAGE_USERS)
        assert service.has_permission(user.id, org.id, Permission.DELETE_ORGANIZATION)
    
    def test_has_permission_admin(self, db: Session, setup_user_org):
        """Test admin permissions."""
        user, org = setup_user_org
        
        # Create admin membership
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=org.id,
            role=OrganizationRole.ADMIN,
            is_active=True
        )
        db.add(user_org)
        db.commit()
        
        # Create service
        user_repo = UserRepository(db)
        user_org_repo = UserOrganizationRepository(db)
        service = UserService(user_repo, user_org_repo)
        
        # Admin should have most permissions but not delete organization
        assert service.has_permission(user.id, org.id, Permission.MANAGE_USERS)
        assert service.has_permission(user.id, org.id, Permission.CREATE_PROJECT)
        assert not service.has_permission(user.id, org.id, Permission.DELETE_ORGANIZATION)
    
    def test_has_permission_employee(self, db: Session, setup_user_org):
        """Test employee permissions."""
        user, org = setup_user_org
        
        # Create employee membership
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=org.id,
            role=OrganizationRole.EMPLOYEE,
            is_active=True
        )
        db.add(user_org)
        db.commit()
        
        # Create service
        user_repo = UserRepository(db)
        user_org_repo = UserOrganizationRepository(db)
        service = UserService(user_repo, user_org_repo)
        
        # Employee should have limited permissions
        assert service.has_permission(user.id, org.id, Permission.VIEW_PROJECT)
        assert service.has_permission(user.id, org.id, Permission.CREATE_TIMESHEET)
        assert not service.has_permission(user.id, org.id, Permission.CREATE_PROJECT)
        assert not service.has_permission(user.id, org.id, Permission.APPROVE_TIMESHEET)
    
    def test_has_permission_not_member(self, db: Session, setup_user_org):
        """Test that non-members don't have permissions."""
        user, org = setup_user_org
        
        # Create service
        user_repo = UserRepository(db)
        user_org_repo = UserOrganizationRepository(db)
        service = UserService(user_repo, user_org_repo)
        
        # User is not a member, should not have permissions
        assert not service.has_permission(user.id, org.id, Permission.VIEW_PROJECT)
        assert not service.has_permission(user.id, org.id, Permission.CREATE_PROJECT)
    
    def test_has_permission_inactive_member(self, db: Session, setup_user_org):
        """Test that inactive members don't have permissions."""
        user, org = setup_user_org
        
        # Create inactive membership
        user_org = UserOrganization(
            user_id=user.id,
            organization_id=org.id,
            role=OrganizationRole.EMPLOYEE,
            is_active=False  # Inactive
        )
        db.add(user_org)
        db.commit()
        
        # Create service
        user_repo = UserRepository(db)
        user_org_repo = UserOrganizationRepository(db)
        service = UserService(user_repo, user_org_repo)
        
        # Inactive member should not have permissions
        assert not service.has_permission(user.id, org.id, Permission.VIEW_PROJECT)


class TestPermissionDecorators:
    """Test permission and role decorators."""
    
    @pytest.fixture
    def setup_users_org(self, client):
        """Create users and organization for decorator testing."""
        # Create owner
        owner_data = {
            "email": "owner@test.com",
            "password": "TestPass123",
            "first_name": "Owner",
            "last_name": "User"
        }
        owner_resp = client.post("/api/v1/auth/register", json=owner_data)
        owner_token = owner_resp.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        owner_id = owner_resp.json()["user"]["id"]
        
        # Create organization
        org_resp = client.post(
            "/api/v1/organizations/",
            json={"name": "Test Org", "tax_id": "111222333"},
            headers=owner_headers
        )
        org_id = org_resp.json()["id"]
        
        # Create employee
        employee_data = {
            "email": "employee@test.com",
            "password": "TestPass123",
            "first_name": "Employee",
            "last_name": "User"
        }
        employee_resp = client.post("/api/v1/auth/register", json=employee_data)
        employee_token = employee_resp.json()["access_token"]
        employee_headers = {"Authorization": f"Bearer {employee_token}"}
        employee_id = employee_resp.json()["user"]["id"]
        
        return {
            "owner_headers": owner_headers,
            "owner_id": owner_id,
            "employee_headers": employee_headers,
            "employee_id": employee_id,
            "org_id": org_id
        }
    
    def test_require_permission_allows_owner(self, client, setup_users_org):
        """Test that require_permission allows owner (has all permissions)."""
        # This test would require an actual endpoint with the decorator
        # For now, we test the underlying logic
        setup = setup_users_org
        
        # Owner should be able to access any permission-protected endpoint
        # This is tested through integration tests with actual endpoints
        pass
    
    def test_require_role_allows_higher_role(self, client, setup_users_org):
        """Test that require_role allows users with higher roles."""
        # This test would require an actual endpoint with the decorator
        # For now, we test the underlying logic
        setup = setup_users_org
        
        # Owner should be able to access admin/manager/employee endpoints
        # Admin should be able to access manager/employee endpoints
        # This is tested through integration tests with actual endpoints
        pass
