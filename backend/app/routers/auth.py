
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.errors import ErrorResponse, ApiError, UNAUTHENTICATED
from app.models import Employee, UserAccount
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    CurrentUserResponse,
)
from app.services import auth_service


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse},
    },
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user using username and password."""

    result = auth_service.login(
        db=db,
        username=data.username,
        password=data.password,
    )

    return TokenResponse(**result)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    responses={
        401: {"model": ErrorResponse},
    },
)
def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUserResponse:
    """Return the currently authenticated user's account details."""

    account = (
        db.query(UserAccount)
        .filter(UserAccount.employee_id == current_user.employee_id)
        .first()
    )

    employee = db.get(Employee, current_user.employee_id)

    if account is None or employee is None:
        raise ApiError(401, UNAUTHENTICATED, "User account not found.")

    return CurrentUserResponse(
        id=account.id,
        employee_id=employee.id,
        username=account.username,
        role=account.system_role.value,
        status=account.status.value,
        must_change_password=account.must_change_password,
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
    )
