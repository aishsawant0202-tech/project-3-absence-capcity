"""Team Management API (Member 2)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user, require_lead_of_team, require_role
from app.errors import ErrorResponse
from app.models import SystemRole, Team
from app.schemas.team import (
    TeamCreate,
    TeamMemberBrief,
    TeamMemberRead,
    TeamRead,
    TeamStatusUpdate,
    TeamUpdate,
)
from app.services import team_service


router = APIRouter(prefix="/api/v1/teams", tags=["Teams"])


@router.post(
    "",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team (Team Lead only)",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: missing or invalid field"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN: not a Team Lead, or no active employee record"},
        409: {"model": ErrorResponse, "description": "TEAM_NAME_TAKEN or ALREADY_TEAM_LEAD"},
    },
)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role(SystemRole.TEAM_LEAD)),
):
    return team_service.create_team(db, data, creator_employee_id=user.employee_id)


@router.get(
    "",
    response_model=list[TeamRead],
    summary="List all teams (all logged-in users)",
    description="Active and inactive teams, sorted by name. Only team fields, no employee details. "
                "`[]` when there are no teams. Searching by name happens in the frontend.",
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
    },
)
def list_teams(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),  # any role may see teams (contract: "all users")
):
    return team_service.list_teams(db)


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    summary="Get one team (all logged-in users)",
    description="Active or inactive team by id.",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: team id is not a number"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: no team with this id"},
    },
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return team_service.get_team(db, team_id)


@router.get(
    "/{team_id}/employees",
    response_model=list[TeamMemberRead | TeamMemberBrief],
    summary="List a team's members (members of the team and HR Admin)",
    description="Sorted by last name; `[]` if the team has no members. HR Admin and the lead of this team "
                "get full details; other members get only `id` and `name` (API contract v2).",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: team id is not a number"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN: caller is not a member of this team or HR Admin"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: no team with this id"},
    },
)
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    team = team_service.get_team(db, team_id)  # 404 before 403: an unknown team is "not found" for everyone
    members, full_details = team_service.list_members(db, team, user)
    schema = TeamMemberRead if full_details else TeamMemberBrief
    return [schema.from_employee(e) for e in members]


_LEAD_ONLY_RESPONSES = {
    400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: invalid field, unknown field, or team id is not a number"},
    401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
    403: {"model": ErrorResponse, "description": "FORBIDDEN: caller is not the Team Lead of this team"},
    404: {"model": ErrorResponse, "description": "NOT_FOUND: no team with this id"},
}


@router.patch(
    "/{team_id}",
    response_model=TeamRead,
    summary="Edit a team (Team Lead of this team only)",
    description="Send only the fields to change: `name`, `description`, `minRequiredFte`. "
                "Status and team lead are changed elsewhere and are rejected here.",
    responses={**_LEAD_ONLY_RESPONSES, 409: {"model": ErrorResponse, "description": "TEAM_NAME_TAKEN: another team has this name"}},
)
def update_team(
    data: TeamUpdate,
    team: Team = Depends(require_lead_of_team),
    db: Session = Depends(get_db),
):
    return team_service.update_team(db, team, data)


@router.patch(
    "/{team_id}/status",
    response_model=TeamRead,
    summary="Activate or deactivate a team (Team Lead of this team only)",
    description='Body `{"status": "ACTIVE"}` or `{"status": "INACTIVE"}`. Teams are never deleted.',
    responses=_LEAD_ONLY_RESPONSES,
)
def set_team_status(
    data: TeamStatusUpdate,
    team: Team = Depends(require_lead_of_team),
    db: Session = Depends(get_db),
):
    return team_service.set_status(db, team, data.status)
