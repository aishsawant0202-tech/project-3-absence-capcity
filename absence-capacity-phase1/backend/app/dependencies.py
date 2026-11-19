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

from fastapi import Depends, Header, HTTPException, status

from app.models import SystemRole


@dataclass(frozen=True)
class CurrentUser:
    role: SystemRole
    employee_id: int


def get_current_user(
    x_role: str | None = Header(default=None),
    x_employee_id: int | None = Header(default=None),
) -> CurrentUser:
    """Return the caller. 401 if we cannot tell who they are."""
    if x_role is None or x_employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in.",
        )
    try:
        role = SystemRole(x_role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown role.",
        )
    return CurrentUser(role=role, employee_id=x_employee_id)


def require_role(*allowed: SystemRole):
    """Use as `Depends(require_role(SystemRole.TEAM_LEAD))`. 403 for other roles."""

    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed.",
            )
        return user

    return checker
