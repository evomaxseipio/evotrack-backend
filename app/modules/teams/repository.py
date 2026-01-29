"""Repository for Team database operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.modules.teams.models import Team, TeamMember
from app.shared.base_repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """Repository for Team model."""
    
    def __init__(self, db: Session):
        super().__init__(Team, db)
    
    def get_by_uuid(self, team_id: UUID) -> Optional[Team]:
        """Get team by UUID."""
        return (
            self.db.query(Team)
            .options(
                joinedload(Team.team_lead),
                joinedload(Team.members).joinedload(TeamMember.user)
            )
            .filter(Team.id == team_id)
            .first()
        )
    
    def get_by_department(
        self,
        dept_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[Team]:
        """Get all teams for a department."""
        query = self.db.query(Team).filter(Team.department_id == dept_id)
        
        if is_active is not None:
            query = query.filter(Team.is_active == is_active)
        
        return query.order_by(Team.name).all()
    
    def get_member_count(self, team_id: UUID) -> int:
        """Get count of members in team."""
        return (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id)
            .count()
        )


class TeamMemberRepository(BaseRepository[TeamMember]):
    """Repository for TeamMember model."""
    
    def __init__(self, db: Session):
        super().__init__(TeamMember, db)
    
    def get_by_team(self, team_id: UUID) -> List[TeamMember]:
        """Get all members of a team."""
        return (
            self.db.query(TeamMember)
            .options(joinedload(TeamMember.user))
            .filter(TeamMember.team_id == team_id)
            .order_by(TeamMember.joined_at)
            .all()
        )
    
    def get_by_team_and_user(self, team_id: UUID, user_id: UUID) -> Optional[TeamMember]:
        """Get team member by team and user."""
        return (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id)
            .filter(TeamMember.user_id == user_id)
            .first()
        )
    
    def is_member(self, team_id: UUID, user_id: UUID) -> bool:
        """Check if user is member of team."""
        return (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id)
            .filter(TeamMember.user_id == user_id)
            .count() > 0
        )
