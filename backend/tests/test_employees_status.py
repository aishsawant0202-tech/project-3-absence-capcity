"""EM-04 – Activate / deactivate an employee and My Profile:
PATCH /api/v1/employees/{id}/status and GET /api/v1/employees/me"""  # Tests for US-04

from datetime import date      # Dates for the test employee
from decimal import Decimal    # Exact numbers (team FTE)

import pytest                  # Testing tool

from app.models import Employee, EmployeeStatus, EmploymentType, Team, TeamStatus  # Database tables and values
from tests.conftest import headers                                                 # Builds login headers

URL = "/api/v1/employees"      # The API we test


@pytest.fixture
def dev(db):                   # Helper: the "Development" team
    team = Team(name="Development", min_required_fte=Decimal("1"), status=TeamStatus.ACTIVE)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@pytest.fixture
def alex(db, dev):             # Helper: Alex, an active employee in Development
    e = Employee(
        first_name="Alex", last_name="Miller", email="alex@example.com", team_id=dev.id,
        employment_type=EmploymentType.PERMANENT, start_date=date(2026, 1, 1),
        status=EmployeeStatus.ACTIVE,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def hr(make_employee):         # Helper: login headers of an HR Admin
    return headers("HR_ADMIN", make_employee().id)


def status_url(employee):      # Helper: /api/v1/employees/<id>/status
    return f"{URL}/{employee.id}/status"


# ---------- activate / deactivate ----------

def test_hr_admin_deactivates_employee(client, hr, alex):        # ACTIVE -> INACTIVE
    r = client.patch(status_url(alex), json={"status": "INACTIVE"}, headers=hr)

    assert r.status_code == 200
    assert r.json()["id"] == alex.id
    assert r.json()["status"] == "INACTIVE"


def test_deactivated_employee_is_not_deleted(client, hr, alex, db, dev):  # Record and team stay
    client.patch(status_url(alex), json={"status": "INACTIVE"}, headers=hr)

    db.expire_all()
    saved = db.get(Employee, alex.id)
    assert saved is not None                 # still in the database
    assert saved.status == EmployeeStatus.INACTIVE
    assert saved.team_id == dev.id           # team assignment kept


def test_hr_admin_reactivates_employee(client, hr, alex):        # INACTIVE -> ACTIVE again
    client.patch(status_url(alex), json={"status": "INACTIVE"}, headers=hr)

    r = client.patch(status_url(alex), json={"status": "ACTIVE"}, headers=hr)

    assert r.status_code == 200
    assert r.json()["status"] == "ACTIVE"


def test_setting_same_status_is_fine(client, hr, alex):          # ACTIVE -> ACTIVE is not an error
    r = client.patch(status_url(alex), json={"status": "ACTIVE"}, headers=hr)

    assert r.status_code == 200
    assert r.json()["status"] == "ACTIVE"


def test_deactivated_employee_shows_in_inactive_filter(client, hr, alex):  # Works with the US-02 filter
    client.patch(status_url(alex), json={"status": "INACTIVE"}, headers=hr)

    r = client.get(URL, params={"status": "INACTIVE"}, headers=hr)

    assert [e["id"] for e in r.json()] == [alex.id]


@pytest.mark.parametrize("body", [{"status": "DELETED"}, {}, {"status": "INACTIVE", "jobTitle": "X"}])
def test_invalid_status_body_is_rejected(client, hr, alex, body):  # Wrong value / missing / extra field -> 400
    r = client.patch(status_url(alex), json=body, headers=hr)

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_employee_is_404(client, hr):                    # Employee 999 -> 404
    r = client.patch(f"{URL}/999/status", json={"status": "INACTIVE"}, headers=hr)

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("role", ["EMPLOYEE", "TEAM_LEAD"])
def test_only_hr_admin_can_change_status(client, alex, role):    # Other roles -> 403
    r = client.patch(status_url(alex), json={"status": "INACTIVE"}, headers=headers(role, alex.id))

    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_status_change_needs_login(client, alex):                # No login -> 401
    r = client.patch(status_url(alex), json={"status": "INACTIVE"})

    assert r.status_code == 401


# ---------- my profile ----------

@pytest.mark.parametrize("role", ["EMPLOYEE", "TEAM_LEAD", "HR_ADMIN"])
def test_my_profile_returns_own_data(client, alex, dev, role):   # Every role sees their own profile
    r = client.get(f"{URL}/me", headers=headers(role, alex.id))

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == alex.id
    assert body["firstName"] == "Alex"
    assert body["email"] == "alex@example.com"
    assert body["teamId"] == dev.id


def test_my_profile_never_shows_someone_else(client, alex, make_employee):  # Only your own data
    other = make_employee()

    r = client.get(f"{URL}/me", headers=headers("EMPLOYEE", other.id))

    assert r.json()["id"] == other.id
    assert r.json()["id"] != alex.id


def test_my_profile_unknown_employee_is_404(client):             # Logged in, but no employee record -> 404
    r = client.get(f"{URL}/me", headers=headers("EMPLOYEE", 999))

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_my_profile_needs_login(client):                         # No login -> 401
    r = client.get(f"{URL}/me")

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"