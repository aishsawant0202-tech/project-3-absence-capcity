"""Shared request dependencies for authentication and authorization.

Authentication uses JWT bearer tokens issued by the login endpoint.
Authorization checks the authenticated user's role and team membership.
"""
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import FORBIDDEN, UNAUTHENTICATED, ApiError
from app.models import (
    AccountStatus,
    Employee,
    EmployeeStatus,
    SystemRole,
    Team,
    UserAccount,
)
from app.security import decode_access_token


@dataclass(frozen=True)
class CurrentUser:
    role: SystemRole
    employee_id: int



def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Return the authenticated caller using a JWT bearer token."""

    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError(401, UNAUTHENTICATED, "Not logged in.")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise ApiError(
            401,
            UNAUTHENTICATED,
            "Invalid or expired authentication token.",
        )

    account = db.get(UserAccount, user_id)

    if account is None or account.status != AccountStatus.ACTIVE:
        raise ApiError(401, UNAUTHENTICATED, "Account is not active.")

    employee = db.get(Employee, account.employee_id)

    if employee is None or employee.status != EmployeeStatus.ACTIVE:
        raise ApiError(401, UNAUTHENTICATED, "Employee is not active.")

    return CurrentUser(
        role=account.system_role,
        employee_id=account.employee_id,
    )



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
