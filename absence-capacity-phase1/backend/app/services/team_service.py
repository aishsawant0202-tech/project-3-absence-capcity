"""Business rules for teams (Member 2 – Team Management)."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Employee, EmployeeStatus, Team, TeamStatus
from app.schemas.team import TeamCreate


def _name_taken(db: Session, name: str) -> bool:
    """True if a team already uses this name (ignoring case and outer spaces)."""
    stmt = select(Team.id).where(func.lower(func.trim(Team.name)) == name.lower())
    return db.execute(stmt).first() is not None


def create_team(db: Session, data: TeamCreate, creator_employee_id: int) -> Team:
    """Create a team. The creator becomes its lead and a member of it.

    Rules (team decision 19.11.2026):
    - team names are unique, ignoring upper/lower case and outer spaces -> 409
    - one person leads at most one team -> 409
    - the lead is a member of their own team; one person = one team, so the
      creator is moved out of any team they were only a member of
    """
    creator = db.get(Employee, creator_employee_id)
    if creator is None or creator.status != EmployeeStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your employee record is missing or inactive.",
        )

    if _name_taken(db, data.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A team with this name already exists.",
        )

    already_lead = db.execute(
        select(Team.id).where(Team.team_lead_employee_id == creator.id)
    ).first()
    if already_lead is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already lead a team.",
        )

    team = Team(
        name=data.name,
        description=data.description,
        min_required_fte=data.min_required_fte,
        team_lead_employee_id=creator.id,
        status=TeamStatus.ACTIVE,
    )
    db.add(team)
    db.flush()  # gives team.id without committing yet

    creator.team_id = team.id  # creator joins (or moves to) the new team

    db.commit()  # team + membership saved together, or not at all
    db.refresh(team)
    return team
