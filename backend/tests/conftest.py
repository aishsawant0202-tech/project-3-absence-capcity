"""Test setup: each test gets a fresh in-memory SQLite database.

No PostgreSQL needed to run the tests:  pytest
"""

import os
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import CurrentUser, get_current_user
from app.main import app
from app.models import (
    Employee,
    EmployeeStatus,
    EmploymentType,
    SystemRole,
)

@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def make_employee(db):
    """Create an employee in the test database and return it."""
    counter = {"n": 0}

    def _make(team_id=None, status=EmployeeStatus.ACTIVE):
        counter["n"] += 1
        n = counter["n"]
        emp = Employee(
            first_name=f"First{n}",
            last_name=f"Last{n}",
            email=f"person{n}@example.com",
            team_id=team_id,
            employment_type=EmploymentType.PERMANENT,
            start_date=date(2025, 1, 1),
            status=status,
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return emp

    return _make


def headers(role: str, employee_id: int) -> dict[str, str]:
    """Generate test-only identity headers."""
    return {
        "X-Test-Role": role,
        "X-Test-Employee-Id": str(employee_id),
    }
@pytest.fixture(autouse=True)
def override_test_authentication():
    def fake_current_user(
        x_test_role: str | None = Header(default=None),
        x_test_employee_id: int | None = Header(default=None),
    ) -> CurrentUser:
        if x_test_role is None or x_test_employee_id is None:
            from app.errors import UNAUTHENTICATED, ApiError
            raise ApiError(401, UNAUTHENTICATED, "Not logged in.")

        try:
            role = SystemRole(x_test_role)
        except ValueError:
            from app.errors import UNAUTHENTICATED, ApiError
            raise ApiError(401, UNAUTHENTICATED, "Unknown role.")

        return CurrentUser(
            role=role,
            employee_id=x_test_employee_id,
        )

    app.dependency_overrides[get_current_user] = fake_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)
