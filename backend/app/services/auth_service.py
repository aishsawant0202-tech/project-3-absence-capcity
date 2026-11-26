
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import UNAUTHENTICATED, ApiError
from app.models import (
    AccountStatus,
    Employee,
    EmployeeStatus,
    UserAccount,
)
from app.security import verify_password, create_access_token


def login(db: Session, username: str, password: str) -> dict:
    """
    Authenticate a user and generate a JWT access token.

    Rules:
    - Username must exist.
    - Password must match the stored Argon2 hash.
    - Account must be ACTIVE.
    - Linked employee must be ACTIVE.
    - Successful login updates last_login_at.
    """

    # Find account by username
    stmt = select(UserAccount).where(
        UserAccount.username == username
    )

    account = db.scalars(stmt).first()

    # Use the same error for unknown username and wrong password
    if account is None:
        raise ApiError(
            401,
            UNAUTHENTICATED,
            "Invalid username or password.",
        )

    if not verify_password(password, account.password_hash):
        raise ApiError(
            401,
            UNAUTHENTICATED,
            "Invalid username or password.",
        )

    # Check account status
    if account.status != AccountStatus.ACTIVE:
        raise ApiError(
            401,
            UNAUTHENTICATED,
            "Account is not active.",
        )

    # Check linked employee
    employee = db.get(Employee, account.employee_id)

    if employee is None or employee.status != EmployeeStatus.ACTIVE:
        raise ApiError(
            401,
            UNAUTHENTICATED,
            "Employee account is not active.",
        )

    # Update last login timestamp
    account.last_login_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(account)

    # Generate access token
    access_token = create_access_token(account.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "must_change_password": account.must_change_password,
    }
