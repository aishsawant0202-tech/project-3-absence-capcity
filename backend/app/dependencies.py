"""Shared request dependencies: who is calling, and are they allowed?

TEMPORARY STUB: until Member 4's login is ready, the caller says who they are
in two request headers:

    X-Role: TEAM_LEAD          (EMPLOYEE / TEAM_LEAD / HR_ADMIN)
    X-Employee-Id: 7

TODO(Member 4): replace the inside of `get_current_user` with the real login
(session or token). Endpoints using `require_role(...)` do not need to change.
Development only - anyone can send these headers.
"""

from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import FORBIDDEN, UNAUTHENTICATED, ApiError
from app.models import SystemRole, Team


@dataclass(frozen=True)
class CurrentUser:
    role: SystemRole
    employee_id: int


def get_current_user(
    x_role: str | None = Header(default=None),
    x_employee_id: int | None = Header(default=None),
) -> CurrentUser:
    """Return the caller. 401 UNAUTHENTICATED if we cannot tell who they are."""
    if x_role is None or x_employee_id is None:
        raise ApiError(401, UNAUTHENTICATED, "Not logged in.")
    try:
        role = SystemRole(x_role)
    except ValueError:
        raise ApiError(401, UNAUTHENTICATED, "Unknown role.")
    return CurrentUser(role=role, employee_id=x_employee_id)


def require_role(*allowed: SystemRole):
    """Use as `Depends(require_role(SystemRole.TEAM_LEAD))`. 403 FORBIDDEN for other roles."""

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise ApiError(403, FORBIDDEN, "Not allowed.")
        return user

    return checker


def require_lead_of_team(
    team_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Team:
    """Use as `team: Team = Depends(require_lead_of_team)` on routes with a `{team_id}` path.

    404 NOT_FOUND for an unknown team (checked first), 403 FORBIDDEN unless the caller is
    the Team Lead of exactly this team (team decision 19.11: only the lead edits / deactivates).
    Returns the team, so the route does not load it again.
    """
    from app.services import team_service  # here, not at the top: team_service imports this module

    team = team_service.get_team(db, team_id)
    if user.role != SystemRole.TEAM_LEAD or team.team_lead_employee_id != user.employee_id:
        raise ApiError(403, FORBIDDEN, "Only the team lead of this team can do this.")
    return team
