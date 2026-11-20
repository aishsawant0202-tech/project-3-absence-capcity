"""Business rules for teams (Member 2 – Team Management)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import CurrentUser
from app.errors import ALREADY_TEAM_LEAD, FORBIDDEN, NOT_FOUND, TEAM_NAME_TAKEN, ApiError
from app.models import Employee, EmployeeStatus, SystemRole, Team, TeamStatus
from app.schemas.team import TeamCreate, TeamUpdate


def _name_taken(db: Session, name: str, except_team_id: int | None = None) -> bool:
    """True if a team already uses this name (ignoring case and outer spaces).

    except_team_id: when editing, the team's own name does not count.
    """
    stmt = select(Team.id).where(func.lower(func.trim(Team.name)) == name.lower())
    if except_team_id is not None:
        stmt = stmt.where(Team.id != except_team_id)
    return db.execute(stmt).first() is not None


def create_team(db: Session, data: TeamCreate, creator_employee_id: int) -> Team:
    """Create a team. The creator becomes its lead and a member of it.

    Rules (team decision 19.11.2026):
    - team names are unique, ignoring upper/lower case and outer spaces -> 409 TEAM_NAME_TAKEN
    - one person leads at most one team -> 409 ALREADY_TEAM_LEAD
    - the lead is a member of their own team; one person = one team, so the
      creator is moved out of any team they were only a member of
    """
    creator = db.get(Employee, creator_employee_id)
    if creator is None or creator.status != EmployeeStatus.ACTIVE:
        raise ApiError(403, FORBIDDEN, "Your employee record is missing or inactive.")

    if _name_taken(db, data.name):
        raise ApiError(409, TEAM_NAME_TAKEN, "A team with this name already exists.")

    already_lead = db.execute(
        select(Team.id).where(Team.team_lead_employee_id == creator.id)
    ).first()
    if already_lead is not None:
        raise ApiError(409, ALREADY_TEAM_LEAD, "You already lead a team.")

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


def list_teams(db: Session) -> list[Team]:
    """All teams, active and inactive, sorted by name (A before b, ignoring case). [] if there are none."""
    stmt = select(Team).order_by(func.lower(Team.name), Team.id)
    return list(db.scalars(stmt))


def get_team(db: Session, team_id: int) -> Team:
    """The team with this id (active or inactive). 404 NOT_FOUND if there is none."""
    team = db.get(Team, team_id)
    if team is None:
        raise ApiError(404, NOT_FOUND, "Team not found.")
    return team


def list_members(db: Session, team: Team, caller: CurrentUser) -> tuple[list[Employee], bool]:
    """The team's employees, sorted by last name, and whether the caller may see full details.

    Access (API contract v2): HR Admin, or a member of this team (employee.team_id == team.id;
    the team lead is a member too). Anyone else -> 403 FORBIDDEN.
    Full details (email, FTE, status, ...) only for HR Admin and the lead of this team;
    other members see only id and name.
    Read-only: employee data is changed by Member 3's feature.
    """
    is_hr = caller.role == SystemRole.HR_ADMIN
    if not is_hr:
        me = db.get(Employee, caller.employee_id)
        if me is None or me.team_id != team.id:
            raise ApiError(403, FORBIDDEN, "Only members of this team and HR Admin can see its members.")

    stmt = (
        select(Employee)
        .where(Employee.team_id == team.id)
        .order_by(func.lower(Employee.last_name), func.lower(Employee.first_name), Employee.id)
    )
    full_details = is_hr or team.team_lead_employee_id == caller.employee_id
    return list(db.scalars(stmt)), full_details


def update_team(db: Session, team: Team, data: TeamUpdate) -> Team:
    """Change only the fields that were sent (name, description, minimum FTE).

    Status and team lead are not touched. Keeping the team's own name is fine;
    the name of another team -> 409 TEAM_NAME_TAKEN. updated_at is set by the database.
    """
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes and _name_taken(db, changes["name"], except_team_id=team.id):
        raise ApiError(409, TEAM_NAME_TAKEN, "A team with this name already exists.")

    for field, value in changes.items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team


def set_status(db: Session, team: Team, new_status: TeamStatus) -> Team:
    """Activate or deactivate a team. Teams are never deleted; members stay assigned.

    Note for Member 3: assigning employees must reject an INACTIVE team.
    """
    team.status = new_status
    db.commit()
    db.refresh(team)
    return team
