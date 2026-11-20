"""TM-03 – View team details and members: GET /api/v1/teams/{id} and GET /api/v1/teams/{id}/employees"""

import pytest

from app.models import EmployeeStatus, Team, TeamStatus
from tests.conftest import headers

URL = "/api/v1/teams"
BRIEF_FIELDS = {"id", "name"}
FULL_FIELDS = {"id", "name", "email", "jobTitle", "workingTimeShare", "status"}


@pytest.fixture
def team_with_lead(client, make_employee):
    """Create a team through the API; return (team JSON, lead employee)."""

    def _make(name: str = "Development"):
        lead = make_employee()
        r = client.post(URL, json={"name": name, "minRequiredFte": 3}, headers=headers("TEAM_LEAD", lead.id))
        assert r.status_code == 201
        return r.json(), lead

    return _make


# ---------- GET /teams/{id} ----------

def test_get_team(client, team_with_lead):
    team, _ = team_with_lead()

    r = client.get(f"{URL}/{team['id']}", headers=headers("EMPLOYEE", 1))

    assert r.status_code == 200
    assert r.json() == team


def test_get_inactive_team(client, team_with_lead, db):
    team, _ = team_with_lead()
    db.get(Team, team["id"]).status = TeamStatus.INACTIVE
    db.commit()

    r = client.get(f"{URL}/{team['id']}", headers=headers("EMPLOYEE", 1))

    assert r.status_code == 200
    assert r.json()["status"] == "INACTIVE"


def test_get_unknown_team_returns_404(client):
    r = client.get(f"{URL}/999", headers=headers("EMPLOYEE", 1))

    assert r.status_code == 404
    assert r.json()["error"] == {"code": "NOT_FOUND", "message": "Team not found.", "details": {}}


def test_get_team_with_text_id_returns_400(client):
    r = client.get(f"{URL}/abc", headers=headers("EMPLOYEE", 1))

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_team_without_login_returns_401(client, team_with_lead):
    team, _ = team_with_lead()
    assert client.get(f"{URL}/{team['id']}").status_code == 401


# ---------- GET /teams/{id}/employees: who may see what ----------

def test_lead_sees_full_details_sorted_by_last_name(client, team_with_lead, make_employee):
    team, lead = team_with_lead()  # lead is "First1 Last1"
    member = make_employee(team_id=team["id"])  # "First2 Last2"

    r = client.get(f"{URL}/{team['id']}/employees", headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 200
    body = r.json()
    assert [m["id"] for m in body] == [lead.id, member.id]
    assert all(set(m) == FULL_FIELDS for m in body)
    assert body[1] == {"id": member.id, "name": "First2 Last2", "email": member.email,
                       "jobTitle": None, "workingTimeShare": 1.0, "status": "ACTIVE"}


def test_hr_admin_sees_full_details_without_being_a_member(client, team_with_lead):
    team, _ = team_with_lead()

    r = client.get(f"{URL}/{team['id']}/employees", headers=headers("HR_ADMIN", 999))

    assert r.status_code == 200
    assert set(r.json()[0]) == FULL_FIELDS


def test_ordinary_member_sees_only_id_and_name(client, team_with_lead, make_employee):
    team, lead = team_with_lead()
    member = make_employee(team_id=team["id"])

    r = client.get(f"{URL}/{team['id']}/employees", headers=headers("EMPLOYEE", member.id))

    assert r.status_code == 200
    assert r.json() == [{"id": lead.id, "name": "First1 Last1"}, {"id": member.id, "name": "First2 Last2"}]
    assert all(set(m) == BRIEF_FIELDS for m in r.json())


@pytest.mark.parametrize("role", ["EMPLOYEE", "TEAM_LEAD"])
def test_non_member_gets_403(client, team_with_lead, make_employee, role):
    team, _ = team_with_lead()
    outsider = make_employee()  # in no team

    r = client.get(f"{URL}/{team['id']}/employees", headers=headers(role, outsider.id))

    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_lead_of_another_team_gets_403(client, team_with_lead):
    team, _ = team_with_lead("Development")
    _, other_lead = team_with_lead("Ops")

    r = client.get(f"{URL}/{team['id']}/employees", headers=headers("TEAM_LEAD", other_lead.id))

    assert r.status_code == 403


def test_inactive_members_are_listed_with_their_status(client, team_with_lead, make_employee):
    team, lead = team_with_lead()
    make_employee(team_id=team["id"], status=EmployeeStatus.INACTIVE)

    r = client.get(f"{URL}/{team['id']}/employees", headers=headers("TEAM_LEAD", lead.id))

    assert [m["status"] for m in r.json()] == ["ACTIVE", "INACTIVE"]


def test_team_without_members_returns_empty_list(client, team_with_lead, db):
    team, lead = team_with_lead()
    lead.team_id = None  # only possible by editing the DB; a new team always has its lead as member
    db.commit()

    r = client.get(f"{URL}/{team['id']}/employees", headers=headers("HR_ADMIN", 1))

    assert r.status_code == 200
    assert r.json() == []


def test_members_of_unknown_team_returns_404(client):
    r = client.get(f"{URL}/999/employees", headers=headers("HR_ADMIN", 1))

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_creator_no_longer_listed_in_old_team(client, team_with_lead, make_employee):
    old, _ = team_with_lead("Old")
    mover = make_employee(team_id=old["id"])
    client.post(URL, json={"name": "New", "minRequiredFte": 1}, headers=headers("TEAM_LEAD", mover.id))

    r = client.get(f"{URL}/{old['id']}/employees", headers=headers("HR_ADMIN", 1))

    assert mover.id not in [m["id"] for m in r.json()]
