
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import ErrorResponse
from app.schemas.auth import LoginRequest, TokenResponse
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
    """
    Authenticate a user using username and password.

    Returns a JWT access token when authentication succeeds.
    """

    result = auth_service.login(
        db=db,
        username=data.username,
        password=data.password,
    )

    return TokenResponse(**result)
