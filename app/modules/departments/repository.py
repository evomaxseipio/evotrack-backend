"""Repository for Department database operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.modules.departments.models import Department
from app.modules.users.models import User
from app.shared.base_repository import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    """Repository for Department model."""
    
    def __init__(self, db: Session):
        super().__init__(Department, db)
    
    def get_by_uuid(self, dept_id: UUID) -> Optional[Department]:
        """Get department by UUID."""
        return (
            self.db.query(Department)
            .options(
                joinedload(Department.parent_department),
                joinedload(Department.department_head),
                joinedload(Department.teams)
            )
            .filter(Department.id == dept_id)
            .first()
        )
    
    def get_by_organization(
        self,
        org_id: UUID,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Department]:
        """Get all departments for an organization."""
        query = self.db.query(Department).filter(Department.organization_id == org_id)
        
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Department.name.ilike(search_pattern),
                    Department.description.ilike(search_pattern)
                )
            )
        
        return query.order_by(Department.name).all()
    
    def get_root_departments(self, org_id: UUID) -> List[Department]:
        """Get root departments (no parent) for an organization."""
        return (
            self.db.query(Department)
            .filter(Department.organization_id == org_id)
            .filter(Department.parent_department_id.is_(None))
            .filter(Department.is_active == True)
            .order_by(Department.name)
            .all()
        )
    
    def get_sub_departments(self, parent_id: UUID) -> List[Department]:
        """Get sub-departments of a parent department."""
        return (
            self.db.query(Department)
            .filter(Department.parent_department_id == parent_id)
            .filter(Department.is_active == True)
            .order_by(Department.name)
            .all()
        )
    
    def has_active_sub_departments(self, dept_id: UUID) -> bool:
        """Check if department has active sub-departments."""
        return (
            self.db.query(Department)
            .filter(Department.parent_department_id == dept_id)
            .filter(Department.is_active == True)
            .count() > 0
        )
    
    def get_user_count(self, dept_id: UUID, include_children: bool = False) -> int:
        """Get count of users in department."""
        if include_children:
            # Get all sub-departments recursively
            dept_ids = self._get_all_sub_department_ids(dept_id)
            dept_ids.append(dept_id)
            return (
                self.db.query(User)
                .filter(User.department_id.in_(dept_ids))
                .filter(User.is_active == True)
                .count()
            )
        else:
            return (
                self.db.query(User)
                .filter(User.department_id == dept_id)
                .filter(User.is_active == True)
                .count()
            )
    
    def _get_all_sub_department_ids(self, parent_id: UUID) -> List[UUID]:
        """Recursively get all sub-department IDs."""
        result = []
        sub_depts = self.get_sub_departments(parent_id)
        for sub_dept in sub_depts:
            result.append(sub_dept.id)
            result.extend(self._get_all_sub_department_ids(sub_dept.id))
        return result
    
    def validate_no_cycle(self, dept_id: UUID, parent_id: UUID) -> bool:
        """Validate that assigning parent_id won't create a cycle."""
        if parent_id is None:
            return True
        
        if dept_id == parent_id:
            return False
        
        # Check if parent_id is a descendant of dept_id
        current = parent_id
        visited = set()
        while current:
            if current in visited or current == dept_id:
                return False
            visited.add(current)
            parent = (
                self.db.query(Department)
                .filter(Department.id == current)
                .first()
            )
            if not parent or not parent.parent_department_id:
                break
            current = parent.parent_department_id
        
        return True
    
    def get_department_users(
        self,
        dept_id: UUID,
        include_children: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users in department."""
        if include_children:
            dept_ids = self._get_all_sub_department_ids(dept_id)
            dept_ids.append(dept_id)
            return (
                self.db.query(User)
                .filter(User.department_id.in_(dept_ids))
                .filter(User.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            return (
                self.db.query(User)
                .filter(User.department_id == dept_id)
                .filter(User.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
