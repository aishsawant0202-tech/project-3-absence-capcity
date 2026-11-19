"""Team Management API (Member 2)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser, require_role
from app.models import SystemRole
from app.schemas.team import TeamCreate, TeamRead
from app.services import team_service

# Base path still to confirm with Member 1 (/api/v1/teams vs /api/teams).
router = APIRouter(prefix="/api/v1/teams", tags=["Teams"])


@router.post(
    "",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team (Team Lead only)",
    responses={
        401: {"description": "Not logged in"},
        403: {"description": "Caller is not a Team Lead, or has no active employee record"},
        409: {"description": "Team name already exists, or caller already leads a team"},
    },
)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role(SystemRole.TEAM_LEAD)),
):
    return team_service.create_team(db, data, creator_employee_id=user.employee_id)
