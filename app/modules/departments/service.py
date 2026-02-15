"""Service for Department business logic."""

from typing import List, Optional
from uuid import UUID

from app.modules.departments.models import Department
from app.modules.departments.repository import DepartmentRepository
from app.modules.departments.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    DepartmentTreeResponse,
    DepartmentDetailResponse
)
from app.modules.teams.repository import TeamRepository
from app.modules.teams.schemas import TeamResponse
from app.modules.organizations.models import OrganizationRole
from app.modules.organizations.repository import UserOrganizationRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.shared.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    BusinessLogicException
)


class DepartmentService:
    """Service for department operations."""
    
    def __init__(
        self,
        department_repository: DepartmentRepository,
        team_repository: TeamRepository,
        user_org_repository: UserOrganizationRepository,
        user_repository: UserRepository
    ):
        self.department_repository = department_repository
        self.team_repository = team_repository
        self.user_org_repository = user_org_repository
        self.user_repository = user_repository
    
    def _check_permissions(self, user_id: UUID, org_id: UUID, required_roles: List[OrganizationRole] = None):
        """Check if user has required permissions."""
        if required_roles is None:
            required_roles = [OrganizationRole.OWNER, OrganizationRole.ADMIN]
        
        role = self.user_org_repository.get_user_role(user_id, org_id)
        if not role or role not in required_roles:
            raise ForbiddenException("You don't have permission to perform this action")
    
    def _check_membership(self, user_id: UUID, org_id: UUID):
        """Check if user is member of organization."""
        if not self.user_org_repository.is_member(user_id, org_id):
            raise ForbiddenException("You don't have access to this organization")
    
    def create_department(
        self,
        org_id: UUID,
        dept_data: DepartmentCreate,
        user_id: UUID
    ) -> DepartmentResponse:
        """Create a new department."""
        # Check permissions
        self._check_permissions(user_id, org_id)
        
        # Validate parent department if provided
        if dept_data.parent_department_id:
            parent = self.department_repository.get_by_uuid(dept_data.parent_department_id)
            if not parent:
                raise NotFoundException("Department", dept_data.parent_department_id)
            if parent.organization_id != org_id:
                raise ValidationException("Parent department must belong to the same organization")
        
        # Validate department head if provided
        if dept_data.department_head_id:
            if not self.user_org_repository.is_member(dept_data.department_head_id, org_id):
                raise ValidationException("Department head must be a member of the organization")
        
        # Create department
        dept_dict = dept_data.model_dump()
        dept_dict["organization_id"] = org_id
        department = self.department_repository.create(dept_dict)
        
        return DepartmentResponse.model_validate(department)
    
    def get_departments(
        self,
        org_id: UUID,
        user_id: UUID,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[DepartmentTreeResponse]:
        """Get all departments for an organization in tree format."""
        self._check_membership(user_id, org_id)
        
        departments = self.department_repository.get_by_organization(
            org_id, is_active, search
        )
        
        # Build tree structure
        dept_dict = {dept.id: dept for dept in departments}
        root_departments = []
        
        for dept in departments:
            if dept.parent_department_id is None:
                root_departments.append(dept)
        
        def build_tree(dept: Department) -> DepartmentTreeResponse:
            """Recursively build department tree."""
            user_count = self.department_repository.get_user_count(dept.id)
            # Get team count from repository
            teams = self.team_repository.get_by_department(dept.id)
            team_count = len(teams)
            
            sub_depts = [
                build_tree(sub_dept)
                for sub_dept in departments
                if sub_dept.parent_department_id == dept.id
            ]
            
            dept_response = DepartmentTreeResponse.model_validate(dept)
            dept_response.sub_departments = sub_depts
            dept_response.user_count = user_count
            dept_response.team_count = team_count
            
            return dept_response
        
        return [build_tree(dept) for dept in root_departments]

    def get_organization_stats(self, org_id: UUID, user_id: UUID) -> dict:
        """Get statistics for organization departments."""
        self._check_membership(user_id, org_id)
        return self.department_repository.get_organization_stats(org_id)
    
    def get_department(self, dept_id: UUID, user_id: UUID) -> DepartmentDetailResponse:
        """Get department by ID with details."""
        department = self.department_repository.get_by_uuid(dept_id)
        if not department:
            raise NotFoundException("Department", dept_id)
        
        self._check_membership(user_id, department.organization_id)
        
        # Get users (limit to first 100 for detail view)
        users = self.department_repository.get_department_users(dept_id, False, 0, 100)
        user_list = [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "full_name": u.full_name
            }
            for u in users
        ]
        
        # Get teams
        teams = self.team_repository.get_by_department(dept_id)
        team_list = [TeamResponse.model_validate(team) for team in teams]
        
        # Build response
        response = DepartmentDetailResponse.model_validate(department)
        response.users = user_list
        response.user_count = len(user_list)
        response.teams = team_list
        
        if department.parent_department:
            response.parent_department = DepartmentResponse.model_validate(department.parent_department)
        
        if department.department_head:
            response.department_head = {
                "id": str(department.department_head.id),
                "email": department.department_head.email,
                "first_name": department.department_head.first_name,
                "last_name": department.department_head.last_name,
                "full_name": department.department_head.full_name
            }
        
        return response
    
    def update_department(
        self,
        dept_id: UUID,
        dept_data: DepartmentUpdate,
        user_id: UUID
    ) -> DepartmentResponse:
        """Update department."""
        department = self.department_repository.get_by_uuid(dept_id)
        if not department:
            raise NotFoundException("Department", dept_id)
        
        self._check_permissions(user_id, department.organization_id)
        
        # Validate parent department if being updated
        if dept_data.parent_department_id is not None:
            if dept_data.parent_department_id:
                parent = self.department_repository.get_by_uuid(dept_data.parent_department_id)
                if not parent:
                    raise NotFoundException("Department", dept_data.parent_department_id)
                if parent.organization_id != department.organization_id:
                    raise ValidationException("Parent department must belong to the same organization")
            
            # Validate no cycle
            if not self.department_repository.validate_no_cycle(
                dept_id, dept_data.parent_department_id
            ):
                raise BusinessLogicException("Cannot create circular reference in department hierarchy")
        
        # Validate department head if being updated
        if dept_data.department_head_id is not None:
            if dept_data.department_head_id:
                if not self.user_org_repository.is_member(
                    dept_data.department_head_id, department.organization_id
                ):
                    raise ValidationException("Department head must be a member of the organization")
        
        # Update department
        update_dict = dept_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(department, key, value)
        
        self.department_repository.db.commit()
        self.department_repository.db.refresh(department)
        
        return DepartmentResponse.model_validate(department)
    
    def delete_department(self, dept_id: UUID, user_id: UUID) -> bool:
        """Delete department (soft delete)."""
        department = self.department_repository.get_by_uuid(dept_id)
        if not department:
            raise NotFoundException("Department", dept_id)
        
        self._check_permissions(user_id, department.organization_id)
        
        # Check if has active sub-departments
        if self.department_repository.has_active_sub_departments(dept_id):
            raise BusinessLogicException("Cannot delete department with active sub-departments")
        
        # Soft delete
        department.is_active = False
        self.department_repository.db.commit()
        
        return True
    
    def get_department_users(
        self,
        dept_id: UUID,
        user_id: UUID,
        include_children: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """Get users in department."""
        department = self.department_repository.get_by_uuid(dept_id)
        if not department:
            raise NotFoundException("Department", dept_id)
        
        self._check_membership(user_id, department.organization_id)
        
        users = self.department_repository.get_department_users(
            dept_id, include_children, skip, limit
        )
        
        return [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "full_name": u.full_name,
                "avatar_url": u.avatar_url,
                "is_active": u.is_active
            }
            for u in users
        ]
    
    def assign_user_to_department(
        self,
        org_id: UUID,
        user_id: UUID,
        dept_id: UUID,
        requester_id: UUID
    ) -> dict:
        """Assign user to department."""
        self._check_permissions(requester_id, org_id)
        
        # Validate user is member of organization
        if not self.user_org_repository.is_member(user_id, org_id):
            raise ValidationException("User must be a member of the organization")
        
        # Validate department
        department = self.department_repository.get_by_uuid(dept_id)
        if not department:
            raise NotFoundException("Department", dept_id)
        if department.organization_id != org_id:
            raise ValidationException("Department must belong to the organization")
        
        # Get user and update
        user = self.user_repository.get_by_uuid(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        
        user.department_id = dept_id
        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)
        
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "department_id": str(dept_id)
        }

    def get_organization_departments_json(
        self,
        organization_id: UUID,
        current_user_id: UUID,
        limit: int = 20,
        cursor: Optional[dict] = None,
        include_inactive: bool = False,
        search: Optional[str] = None
    ) -> dict:
        """Get organization departments using database function."""
        # Simple membership check (perms handled inside DB function)
        self._check_membership(current_user_id, organization_id)
        
        return self.department_repository.get_organization_departments_json(
            organization_id=organization_id,
            current_user_id=current_user_id,
            limit=limit,
            cursor=cursor,
            include_inactive=include_inactive,
            search=search
        )
