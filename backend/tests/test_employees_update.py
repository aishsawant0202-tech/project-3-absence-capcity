"""EM-03 – Update an employee and transfer between teams: PATCH /api/v1/employees/{id}"""  # Tests for US-03

from datetime import date      # Dates for the test employee
from decimal import Decimal    # Exact numbers (FTE)

import pytest                  # Testing tool

from app.models import Employee, EmployeeStatus, EmploymentType, Team, TeamStatus  # Database tables and values
from tests.conftest import headers                                                 # Builds login headers


@pytest.fixture
def make_team(db):             # Helper: create a team in the test database
    def _make(name, status=TeamStatus.ACTIVE):
        team = Team(name=name, min_required_fte=Decimal("1"), status=status)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    return _make


@pytest.fixture
def dev(make_team):            # Helper: the "Development" team
    return make_team("Development")


@pytest.fixture
def alex(db, dev):             # Helper: Alex, a permanent employee in Development
    e = Employee(
        first_name="Alex", last_name="Miller", email="alex@example.com", team_id=dev.id,
        job_title="Developer", employment_type=EmploymentType.PERMANENT,
        working_time_share=Decimal("1.0"), start_date=date(2026, 1, 1), status=EmployeeStatus.ACTIVE,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def hr(make_employee):         # Helper: login headers of an HR Admin
    return headers("HR_ADMIN", make_employee().id)


def url(employee):             # Helper: /api/v1/employees/<id>
    return f"/api/v1/employees/{employee.id}"


# ---------- success ----------

def test_update_some_fields(client, hr, alex):           # Only sent fields change
    r = client.patch(url(alex), json={"jobTitle": "Senior Developer", "workingTimeShare": 0.8}, headers=hr)

    assert r.status_code == 200
    body = r.json()
    assert body["jobTitle"] == "Senior Developer"
    assert body["workingTimeShare"] == 0.8
    assert body["firstName"] == "Alex"  # not sent -> unchanged
    assert body["email"] == "alex@example.com"


def test_change_is_saved_in_database(client, hr, alex, db):  # Change is really stored
    client.patch(url(alex), json={"lastName": "Smith"}, headers=hr)

    db.refresh(alex)
    assert alex.last_name == "Smith"


def test_transfer_to_another_team(client, hr, alex, make_team):  # Move Alex to QA
    qa = make_team("QA")

    r = client.patch(url(alex), json={"teamId": qa.id}, headers=hr)

    assert r.status_code == 200
    assert r.json()["teamId"] == qa.id


def test_remove_from_team(client, hr, alex):             # teamId null -> no team
    r = client.patch(url(alex), json={"teamId": None}, headers=hr)

    assert r.status_code == 200
    assert r.json()["teamId"] is None


def test_keep_own_email(client, hr, alex):               # Own email (other case) is fine
    r = client.patch(url(alex), json={"email": "ALEX@example.com"}, headers=hr)

    assert r.status_code == 200
    assert r.json()["email"] == "alex@example.com"


def test_change_to_contract_with_end_date(client, hr, alex):  # Permanent -> contract with end date
    r = client.patch(url(alex), json={"employmentType": "CONTRACT", "endDate": "2027-06-30"}, headers=hr)

    assert r.status_code == 200
    assert r.json()["employmentType"] == "CONTRACT"
    assert r.json()["endDate"] == "2027-06-30"


def test_change_to_permanent_clears_end_date(client, hr, alex):  # Contract -> permanent removes end date
    client.patch(url(alex), json={"employmentType": "CONTRACT", "endDate": "2027-06-30"}, headers=hr)

    r = client.patch(url(alex), json={"employmentType": "PERMANENT"}, headers=hr)

    assert r.status_code == 200
    assert r.json()["endDate"] is None


def test_status_is_not_changed(client, hr, alex):        # Editing does not touch status
    r = client.patch(url(alex), json={"jobTitle": "Lead"}, headers=hr)

    assert r.json()["status"] == "ACTIVE"


def test_empty_body_changes_nothing(client, hr, alex):   # {} -> nothing changes
    r = client.patch(url(alex), json={}, headers=hr)

    assert r.status_code == 200
    assert r.json()["jobTitle"] == "Developer"


# ---------- conflicts and missing things ----------

def test_email_of_another_employee_is_rejected(client, hr, alex, make_employee):  # -> 409 EMAIL_TAKEN
    other = make_employee()

    r = client.patch(url(alex), json={"email": other.email}, headers=hr)

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_TAKEN"


def test_reference_of_another_employee_is_rejected(client, hr, alex, make_employee, db):  # -> 409
    other = make_employee()
    other.employee_ref = "G2-7"
    db.commit()

    r = client.patch(url(alex), json={"employeeRef": "G2-7"}, headers=hr)

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMPLOYEE_REF_TAKEN"


def test_transfer_to_inactive_team_is_rejected(client, hr, alex, make_team):  # -> 409 TEAM_INACTIVE
    old = make_team("Old", status=TeamStatus.INACTIVE)

    r = client.patch(url(alex), json={"teamId": old.id}, headers=hr)

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "TEAM_INACTIVE"


def test_transfer_to_unknown_team_is_rejected(client, hr, alex):  # -> 404
    r = client.patch(url(alex), json={"teamId": 999}, headers=hr)

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_unknown_employee_is_404(client, hr):            # Employee 999 does not exist -> 404
    r = client.patch("/api/v1/employees/999", json={"jobTitle": "X"}, headers=hr)

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


# ---------- validation (400) ----------

@pytest.mark.parametrize("body", [
    {"firstName": "  "},                                 # blank name
    {"firstName": None},                                 # name removed
    {"email": "not-an-email"},                           # bad email
    {"workingTimeShare": 0},                             # FTE too small
    {"workingTimeShare": 1.5},                           # FTE too big
    {"employmentType": "FREELANCE"},                     # unknown type
    {"startDate": None},                                 # start date removed
    {"status": "INACTIVE"},                              # status is changed elsewhere
    {"employmentType": "CONTRACT"},                      # contract without end date
    {"endDate": "2027-01-01"},                           # permanent with end date
])
def test_invalid_update_is_rejected(client, hr, alex, body):  # Each wrong value -> 400
    r = client.patch(url(alex), json=body, headers=hr)

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_contract_end_before_start_is_rejected(client, hr, alex):  # End before start -> 400
    r = client.patch(url(alex), json={"employmentType": "CONTRACT", "endDate": "2025-12-31"}, headers=hr)

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------- authorization ----------

@pytest.mark.parametrize("role", ["EMPLOYEE", "TEAM_LEAD"])
def test_only_hr_admin_can_update(client, alex, role):   # Other roles -> 403
    r = client.patch(url(alex), json={"jobTitle": "X"}, headers=headers(role, alex.id))

    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_update_needs_login(client, alex):               # No login -> 401
    r = client.patch(url(alex), json={"jobTitle": "X"})

    assert r.status_code == 401