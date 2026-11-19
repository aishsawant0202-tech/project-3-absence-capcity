"""Test setup: each test gets a fresh in-memory SQLite database.

No PostgreSQL needed to run the tests:  pytest
"""

import os
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite://")  # must be set before importing app

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Employee, EmployeeStatus, EmploymentType


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
    app.dependency_overrides.clear()


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
    """Temporary test headers until real login exists."""
    return {"X-Role": role, "X-Employee-Id": str(employee_id)}
