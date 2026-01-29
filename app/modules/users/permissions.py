"""Role-Based Access Control (RBAC) for users."""

from enum import Enum
from typing import Set, Dict
from uuid import UUID

from fastapi import HTTPException, status

from app.modules.users.models import User


class Permission(str, Enum):
    """System permissions."""
    
    # User management
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    
    # Project management
    VIEW_PROJECTS = "view_projects"
    CREATE_PROJECTS = "create_projects"
    EDIT_PROJECTS = "edit_projects"
    DELETE_PROJECTS = "delete_projects"
    
    # Timesheet management
    VIEW_OWN_TIMESHEET = "view_own_timesheet"
    EDIT_OWN_TIMESHEET = "edit_own_timesheet"
    VIEW_ALL_TIMESHEETS = "view_all_timesheets"
    APPROVE_TIMESHEETS = "approve_timesheets"
    
    # Reports
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"
    
    # Admin
    MANAGE_ORGANIZATION = "manage_organization"
    MANAGE_SETTINGS = "manage_settings"


class Role(str, Enum):
    """User roles in organization."""
    
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


# Role -> Permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.OWNER: {
        # All permissions
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
        Permission.VIEW_PROJECTS,
        Permission.CREATE_PROJECTS,
        Permission.EDIT_PROJECTS,
        Permission.DELETE_PROJECTS,
        Permission.VIEW_OWN_TIMESHEET,
        Permission.EDIT_OWN_TIMESHEET,
        Permission.VIEW_ALL_TIMESHEETS,
        Permission.APPROVE_TIMESHEETS,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_ORGANIZATION,
        Permission.MANAGE_SETTINGS,
    },
    Role.ADMIN: {
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.VIEW_PROJECTS,
        Permission.CREATE_PROJECTS,
        Permission.EDIT_PROJECTS,
        Permission.VIEW_OWN_TIMESHEET,
        Permission.EDIT_OWN_TIMESHEET,
        Permission.VIEW_ALL_TIMESHEETS,
        Permission.APPROVE_TIMESHEETS,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.MANAGE_SETTINGS,
    },
    Role.MANAGER: {
        Permission.VIEW_USERS,
        Permission.VIEW_PROJECTS,
        Permission.CREATE_PROJECTS,
        Permission.EDIT_PROJECTS,
        Permission.VIEW_OWN_TIMESHEET,
        Permission.EDIT_OWN_TIMESHEET,
        Permission.VIEW_ALL_TIMESHEETS,
        Permission.APPROVE_TIMESHEETS,
        Permission.VIEW_REPORTS,
    },
    Role.EMPLOYEE: {
        Permission.VIEW_PROJECTS,
        Permission.VIEW_OWN_TIMESHEET,
        Permission.EDIT_OWN_TIMESHEET,
    },
}


def has_permission(
    user: User,
    organization_id: UUID,
    permission: Permission
) -> bool:
    """
    Check if user has permission in organization.
    
    TODO: Integrate with UserOrganization table to get actual role.
    """
    # For now, this is a placeholder. Integration with DB needed.
    return True


def has_permission_in_role(role_name: str, permission: str) -> bool:
    """
    Check if a specific role name has a permission.
    """
    try:
        role = Role(role_name.lower())
        perm = Permission(permission.lower())
        allowed_permissions = ROLE_PERMISSIONS.get(role, set())
        return perm in allowed_permissions
    except (ValueError, KeyError):
        return False
