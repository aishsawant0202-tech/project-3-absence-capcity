"""TM-01 – Create a team: POST /api/v1/teams"""

import pytest

from app.models import Employee, Team
from tests.conftest import headers

URL = "/api/v1/teams"
BODY = {"name": "Development", "description": "Software team", "min_required_fte": 5.0}


# ---------- success ----------

def test_team_lead_creates_team(client, make_employee, db):
    lead = make_employee()

    r = client.post(URL, json=BODY, headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 201
    team = r.json()
    assert team["name"] == "Development"
    assert team["description"] == "Software team"
    assert team["min_required_fte"] == 5.0
    assert team["status"] == "ACTIVE"
    assert team["team_lead_employee_id"] == lead.id  # creator becomes lead


def test_creator_becomes_member_of_new_team(client, make_employee, db):
    lead = make_employee()

    r = client.post(URL, json=BODY, headers=headers("TEAM_LEAD", lead.id))

    db.refresh(lead)
    assert lead.team_id == r.json()["id"]


def test_creator_is_moved_from_old_team(client, make_employee, db):
    other_lead = make_employee()
    old = client.post(URL, json={"name": "Old", "min_required_fte": 1},
                      headers=headers("TEAM_LEAD", other_lead.id)).json()
    member = make_employee(team_id=old["id"])  # member of "Old", not its lead

    r = client.post(URL, json=BODY, headers=headers("TEAM_LEAD", member.id))

    assert r.status_code == 201
    db.refresh(member)
    assert member.team_id == r.json()["id"]


def test_name_is_trimmed_and_description_optional(client, make_employee):
    lead = make_employee()

    r = client.post(URL, json={"name": "  QA  ", "min_required_fte": 0},
                    headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 201
    assert r.json()["name"] == "QA"
    assert r.json()["description"] is None


# ---------- 409 conflicts ----------

@pytest.mark.parametrize("same_name", ["Development", "development", "DEVELOPMENT", "  Development  "])
def test_duplicate_name_returns_409(client, make_employee, same_name):
    client.post(URL, json=BODY, headers=headers("TEAM_LEAD", make_employee().id))

    r = client.post(URL, json={**BODY, "name": same_name},
                    headers=headers("TEAM_LEAD", make_employee().id))

    assert r.status_code == 409
    assert r.json()["detail"] == "A team with this name already exists."


def test_lead_cannot_create_second_team(client, make_employee, db):
    lead = make_employee()
    client.post(URL, json=BODY, headers=headers("TEAM_LEAD", lead.id))

    r = client.post(URL, json={**BODY, "name": "Second"}, headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 409
    assert r.json()["detail"] == "You already lead a team."
    assert db.query(Team).count() == 1


# ---------- 422 invalid data ----------

@pytest.mark.parametrize("body", [
    {"name": "", "min_required_fte": 1},
    {"name": "   ", "min_required_fte": 1},
    {"name": "Ops", "min_required_fte": -1},
    {"name": "Ops"},                       # FTE missing
    {"min_required_fte": 1},               # name missing
    {"name": "x" * 101, "min_required_fte": 1},
])
def test_invalid_data_returns_422(client, make_employee, body):
    r = client.post(URL, json=body, headers=headers("TEAM_LEAD", make_employee().id))
    assert r.status_code == 422


# ---------- 401 / 403 permissions ----------

@pytest.mark.parametrize("role", ["HR_ADMIN", "EMPLOYEE"])
def test_other_roles_cannot_create(client, make_employee, db, role):
    r = client.post(URL, json=BODY, headers=headers(role, make_employee().id))

    assert r.status_code == 403
    assert db.query(Team).count() == 0


def test_without_login_headers_returns_401(client):
    assert client.post(URL, json=BODY).status_code == 401


def test_unknown_role_returns_401(client, make_employee):
    r = client.post(URL, json=BODY, headers=headers("BOSS", make_employee().id))
    assert r.status_code == 401


def test_lead_without_employee_record_returns_403(client):
    r = client.post(URL, json=BODY, headers=headers("TEAM_LEAD", 999))
    assert r.status_code == 403


def test_inactive_lead_returns_403(client, make_employee):
    from app.models import EmployeeStatus

    lead = make_employee(status=EmployeeStatus.INACTIVE)
    r = client.post(URL, json=BODY, headers=headers("TEAM_LEAD", lead.id))
    assert r.status_code == 403
