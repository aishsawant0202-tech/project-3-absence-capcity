"""EM-01 – Create an employee: POST /api/v1/employees"""  # Tests for user story US-01

from decimal import Decimal   # Exact numbers (for team FTE)

import pytest                 # Testing tool

from app.models import Employee, Team, TeamStatus   # Database tables
from tests.conftest import headers                  # Helper that builds the X-Role / X-Employee-Id headers

URL = "/api/v1/employees"     # The API we test
BODY = {                      # A correct employee, used in most tests
    "firstName": "Alex",
    "lastName": "Miller",
    "email": "alex.miller@example.com",
    "jobTitle": "Software Engineer",
    "employmentType": "PERMANENT",
    "workingTimeShare": 1.0,
    "startDate": "2026-11-01",
}


@pytest.fixture
def make_team(db):            # Helper: create a team in the test database
    def _make(name="Development", status=TeamStatus.ACTIVE):
        team = Team(name=name, min_required_fte=Decimal("1"), status=status)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    return _make


@pytest.fixture
def hr(make_employee):        # Helper: headers of an HR Admin
    return headers("HR_ADMIN", make_employee().id)


# ---------- success ----------

def test_hr_admin_creates_employee(client, hr):          # HR Admin creates an employee -> 201
    r = client.post(URL, json=BODY, headers=hr)

    assert r.status_code == 201
    emp = r.json()
    assert emp["id"] > 0
    assert emp["firstName"] == "Alex"
    assert emp["lastName"] == "Miller"
    assert emp["email"] == "alex.miller@example.com"
    assert emp["jobTitle"] == "Software Engineer"
    assert emp["employmentType"] == "PERMANENT"
    assert emp["workingTimeShare"] == 1.0
    assert emp["startDate"] == "2026-11-01"
    assert emp["endDate"] is None
    assert emp["teamId"] is None
    assert emp["status"] == "ACTIVE"


def test_employee_is_saved_in_database(client, hr, db):  # The employee is really stored
    r = client.post(URL, json=BODY, headers=hr)

    saved = db.get(Employee, r.json()["id"])
    assert saved is not None
    assert saved.email == "alex.miller@example.com"


def test_create_with_active_team(client, hr, make_team):  # Employee can join an active team
    team = make_team()

    r = client.post(URL, json={**BODY, "teamId": team.id}, headers=hr)

    assert r.status_code == 201
    assert r.json()["teamId"] == team.id


def test_contract_employee_with_end_date(client, hr):    # Contract with end date and 0.5 FTE is fine
    body = {**BODY, "employmentType": "CONTRACT", "workingTimeShare": 0.5, "endDate": "2027-03-31"}

    r = client.post(URL, json=body, headers=hr)

    assert r.status_code == 201
    assert r.json()["endDate"] == "2027-03-31"
    assert r.json()["workingTimeShare"] == 0.5


def test_names_and_email_are_cleaned(client, hr):        # Spaces removed, email in small letters
    body = {**BODY, "firstName": "  Alex ", "email": "  Alex.Miller@Example.COM "}

    r = client.post(URL, json=body, headers=hr)

    assert r.status_code == 201
    assert r.json()["firstName"] == "Alex"
    assert r.json()["email"] == "alex.miller@example.com"


def test_working_time_share_defaults_to_full_time(client, hr):  # No FTE sent -> 1.0
    body = {k: v for k, v in BODY.items() if k != "workingTimeShare"}

    r = client.post(URL, json=body, headers=hr)

    assert r.status_code == 201
    assert r.json()["workingTimeShare"] == 1.0


# ---------- duplicates and team checks ----------

def test_duplicate_email_is_rejected(client, hr):        # Same email again -> 409 EMAIL_TAKEN
    client.post(URL, json=BODY, headers=hr)

    r = client.post(URL, json={**BODY, "email": "ALEX.MILLER@example.com"}, headers=hr)

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_TAKEN"


def test_duplicate_employee_ref_is_rejected(client, hr):  # Same reference again -> 409
    client.post(URL, json={**BODY, "employeeRef": "G2-1"}, headers=hr)

    r = client.post(URL, json={**BODY, "email": "other@example.com", "employeeRef": "G2-1"}, headers=hr)

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMPLOYEE_REF_TAKEN"


def test_unknown_team_is_rejected(client, hr):           # Team does not exist -> 404
    r = client.post(URL, json={**BODY, "teamId": 999}, headers=hr)

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_inactive_team_is_rejected(client, hr, make_team):  # Inactive team -> 409 TEAM_INACTIVE
    team = make_team(status=TeamStatus.INACTIVE)

    r = client.post(URL, json={**BODY, "teamId": team.id}, headers=hr)

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "TEAM_INACTIVE"


# ---------- validation (400) ----------

@pytest.mark.parametrize("field", ["firstName", "lastName", "email", "employmentType", "startDate"])
def test_required_field_missing(client, hr, field):     # Each required field missing -> 400
    body = {k: v for k, v in BODY.items() if k != field}

    r = client.post(URL, json=body, headers=hr)

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("changes", [
    {"firstName": "   "},                                    # blank name
    {"email": "not-an-email"},                               # bad email
    {"employmentType": "FREELANCE"},                         # unknown type
    {"workingTimeShare": 0},                                 # FTE too small
    {"workingTimeShare": 1.5},                               # FTE too big
    {"employmentType": "CONTRACT"},                          # contract without end date
    {"employmentType": "CONTRACT", "endDate": "2026-10-01"}, # end before start
    {"endDate": "2027-01-01"},                               # permanent with end date
])
def test_invalid_data_is_rejected(client, hr, changes):  # Each wrong value -> 400
    r = client.post(URL, json={**BODY, **changes}, headers=hr)

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------- authorization ----------

@pytest.mark.parametrize("role", ["EMPLOYEE", "TEAM_LEAD"])
def test_only_hr_admin_can_create(client, make_employee, role):  # Other roles -> 403
    r = client.post(URL, json=BODY, headers=headers(role, make_employee().id))

    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_not_logged_in(client):                          # No login headers -> 401
    r = client.post(URL, json=BODY)

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"