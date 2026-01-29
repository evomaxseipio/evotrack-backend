"""Message constants for organizations module.

This module contains all message constants used in the organizations module.
Following DRY and KISS principles, all messages are centralized here for easy maintenance.
"""

# Success messages
class SuccessMessages:
    """Success message constants."""
    
    ORGANIZATION_CREATED = "Organization created successfully"
    ORGANIZATION_RETRIEVED = "Organization retrieved successfully"
    ORGANIZATIONS_RETRIEVED = "Organizations retrieved successfully"
    ORGANIZATION_UPDATED = "Organization updated successfully"
    ORGANIZATION_DELETED = "Organization deleted successfully"
    
    INVITATION_CREATED = "Invitation created successfully"
    INVITATIONS_CREATED = "Invitations created successfully"
    INVITATION_ACCEPTED = "Invitation accepted successfully"
    
    MEMBER_ROLE_UPDATED = "Member role updated successfully"
    MEMBER_REMOVED = "Member removed successfully"
    
    DEPARTMENT_CREATED = "Department created successfully"
    DEPARTMENTS_RETRIEVED = "Departments retrieved successfully"
    DEPARTMENT_UPDATED = "Department updated successfully"
    USER_ASSIGNED_TO_DEPARTMENT = "User assigned to department successfully"
    
    USERS_RETRIEVED = "Users retrieved successfully"


# Error message titles
class ErrorTitles:
    """Error title constants (for messageResponse field)."""
    
    NOT_FOUND = "Resource not found"
    ALREADY_EXISTS = "Resource already exists"
    FORBIDDEN = "Forbidden"
    UNAUTHORIZED = "Unauthorized"
    VALIDATION_ERROR = "Validation error"
    BUSINESS_LOGIC_ERROR = "Business logic error"
    DATABASE_ERROR = "Database error"
    INTERNAL_ERROR = "Internal server error"


# Error message details
class ErrorMessages:
    """Error message detail constants (for errorMessage field)."""
    
    # Organization errors
    ORGANIZATION_NOT_FOUND = "The organization with ID '{org_id}' does not exist in the system"
    ORGANIZATION_TAX_ID_EXISTS = "The tax_id '{tax_id}' is already registered to another organization"
    ORGANIZATION_SLUG_EXISTS = "The slug '{slug}' is already registered to another organization"
    ORGANIZATION_ACCESS_DENIED = "You don't have access to this organization"
    ORGANIZATION_UPDATE_DENIED = "You don't have permission to update this organization. Only admins and owners can update organizations"
    ORGANIZATION_DELETE_DENIED = "You don't have permission to delete this organization. Only organization owners can delete organizations"
    ORGANIZATION_OWNER_DELETE_DENIED = "You cannot delete an organization where you are the owner"
    
    # Invitation errors
    INVITATION_NOT_FOUND = "The invitation with token '{token}' does not exist or has expired"
    INVITATION_EXPIRED = "The invitation has expired. Please request a new invitation"
    INVITATION_ALREADY_ACCEPTED = "This invitation has already been accepted"
    INVITATION_ALREADY_EXISTS = "An invitation for email '{email}' already exists and is pending"
    USER_ALREADY_MEMBER = "The user with email '{email}' is already a member of this organization"
    INVITATION_INVALID_EMAIL = "The email '{email}' is not valid"
    
    # Member errors
    MEMBER_NOT_FOUND = "The member with ID '{member_id}' does not exist in this organization"
    MEMBER_ROLE_UPDATE_DENIED = "You don't have permission to update member roles. Only admins and owners can update roles"
    MEMBER_REMOVE_DENIED = "You don't have permission to remove members. Only admins and owners can remove members"
    MEMBER_OWNER_ROLE_CHANGE = "Cannot change the role of an organization owner"
    MEMBER_CANNOT_REMOVE_OWNER = "Cannot remove an organization owner"
    MEMBER_CANNOT_REMOVE_SELF = "You cannot remove yourself from the organization"
    
    # Department errors
    DEPARTMENT_NOT_FOUND = "The department with ID '{department_id}' does not exist"
    DEPARTMENT_ACCESS_DENIED = "You don't have access to this department"
    DEPARTMENT_CREATE_DENIED = "You don't have permission to create departments. Only admins and owners can create departments"
    DEPARTMENT_UPDATE_DENIED = "You don't have permission to update departments. Only admins and owners can update departments"
    DEPARTMENT_PARENT_INVALID = "The parent department does not belong to this organization"
    DEPARTMENT_HEAD_INVALID = "The department head is not a member of this organization"
    USER_NOT_IN_ORGANIZATION = "The user is not a member of this organization"
    
    # User errors
    USER_NOT_FOUND = "The user with ID '{user_id}' does not exist"
    USER_ACCESS_DENIED = "You don't have access to view users in this organization"
    
    # General errors
    INVALID_ROLE = "Invalid role '{role}'. Valid roles are: owner, admin, manager, employee"
    INVALID_UUID = "Invalid UUID format: '{value}'"
    MISSING_REQUIRED_FIELD = "Required field '{field}' is missing"
    INVALID_PAGINATION = "Invalid pagination parameters. 'skip' must be >= 0 and 'limit' must be between 1 and 100"


def format_error_message(template: str, **kwargs) -> str:
    """
    Format error message template with provided values.
    
    Args:
        template: Error message template with placeholders
        **kwargs: Values to fill in the template placeholders
    
    Returns:
        Formatted error message string
    
    Example:
        format_error_message(ErrorMessages.ORGANIZATION_NOT_FOUND, org_id="123")
        # Returns: "The organization with ID '123' does not exist in the system"
    """
    return template.format(**kwargs)
