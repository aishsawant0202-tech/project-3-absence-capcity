"""TM-04 – Edit and activate / deactivate a team: PATCH /api/v1/teams/{id} and PATCH /api/v1/teams/{id}/status"""

from datetime import datetime, timezone

import pytest

from app.models import Team
from tests.conftest import headers

URL = "/api/v1/teams"


@pytest.fixture
def team_with_lead(client, make_employee):
    """Create a team through the API; return (team JSON, lead employee)."""

    def _make(name: str = "Development"):
        lead = make_employee()
        r = client.post(URL, json={"name": name, "description": "Old text", "minRequiredFte": 3},
                        headers=headers("TEAM_LEAD", lead.id))
        assert r.status_code == 201
        return r.json(), lead

    return _make


# ---------- PATCH /teams/{id}: success ----------

def test_lead_edits_all_fields(client, team_with_lead):
    team, lead = team_with_lead()

    r = client.patch(f"{URL}/{team['id']}", json={"name": "Dev Team", "description": "New text", "minRequiredFte": 4.5},
                     headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 200
    assert r.json() == {**team, "name": "Dev Team", "description": "New text", "minRequiredFte": 4.5}


def test_only_sent_fields_change(client, team_with_lead):
    team, lead = team_with_lead()

    r = client.patch(f"{URL}/{team['id']}", json={"minRequiredFte": 6}, headers=headers("TEAM_LEAD", lead.id))

    assert r.json() == {**team, "minRequiredFte": 6.0}


def test_description_can_be_cleared(client, team_with_lead):
    team, lead = team_with_lead()

    r = client.patch(f"{URL}/{team['id']}", json={"description": None}, headers=headers("TEAM_LEAD", lead.id))

    assert r.json()["description"] is None


@pytest.mark.parametrize("same_name", ["Development", "development", "  DEVELOPMENT  "])
def test_keeping_own_name_is_allowed(client, team_with_lead, same_name):
    team, lead = team_with_lead()

    r = client.patch(f"{URL}/{team['id']}", json={"name": same_name}, headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 200


def test_edit_updates_updated_at(client, team_with_lead, db):
    team, lead = team_with_lead()
    row = db.get(Team, team["id"])
    row.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db.commit()

    client.patch(f"{URL}/{team['id']}", json={"name": "Renamed"}, headers=headers("TEAM_LEAD", lead.id))

    db.refresh(row)
    assert row.updated_at.year > 2020


# ---------- PATCH /teams/{id}: invalid ----------

def test_name_of_another_team_returns_409(client, team_with_lead):
    team, lead = team_with_lead("Development")
    team_with_lead("Ops")

    r = client.patch(f"{URL}/{team['id']}", json={"name": " ops "}, headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 409
    assert r.json()["error"]["code"] == "TEAM_NAME_TAKEN"


@pytest.mark.parametrize("body", [
    {"name": ""},
    {"name": "   "},
    {"name": None},
    {"name": "x" * 101},
    {"minRequiredFte": -1},
    {"minRequiredFte": None},
    {"status": "INACTIVE"},              # status only via /status
    {"teamLeadEmployeeId": 99},          # lead cannot be changed here
])
def test_invalid_edit_returns_400_and_changes_nothing(client, team_with_lead, body):
    team, lead = team_with_lead()

    r = client.patch(f"{URL}/{team['id']}", json=body, headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get(f"{URL}/{team['id']}", headers=headers("EMPLOYEE", 1)).json() == team


# ---------- PATCH /teams/{id}/status ----------

def test_lead_deactivates_and_reactivates(client, team_with_lead):
    team, lead = team_with_lead()

    off = client.patch(f"{URL}/{team['id']}/status", json={"status": "INACTIVE"}, headers=headers("TEAM_LEAD", lead.id))
    on = client.patch(f"{URL}/{team['id']}/status", json={"status": "ACTIVE"}, headers=headers("TEAM_LEAD", lead.id))

    assert off.status_code == 200
    assert off.json() == {**team, "status": "INACTIVE"}  # nothing else changes
    assert on.json()["status"] == "ACTIVE"


def test_deactivated_team_is_kept_with_its_members(client, team_with_lead, db):
    team, lead = team_with_lead()

    client.patch(f"{URL}/{team['id']}/status", json={"status": "INACTIVE"}, headers=headers("TEAM_LEAD", lead.id))

    assert db.get(Team, team["id"]) is not None  # never deleted
    db.refresh(lead)
    assert lead.team_id == team["id"]


def test_inactive_team_can_still_be_edited(client, team_with_lead):
    team, lead = team_with_lead()
    client.patch(f"{URL}/{team['id']}/status", json={"status": "INACTIVE"}, headers=headers("TEAM_LEAD", lead.id))

    r = client.patch(f"{URL}/{team['id']}", json={"description": "Closed"}, headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 200
    assert r.json()["status"] == "INACTIVE"


@pytest.mark.parametrize("body", [{"status": "DELETED"}, {"status": "inactive"}, {}, {"status": None}])
def test_invalid_status_returns_400(client, team_with_lead, body):
    team, lead = team_with_lead()

    r = client.patch(f"{URL}/{team['id']}/status", json=body, headers=headers("TEAM_LEAD", lead.id))

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------- both endpoints: 404 / 403 / 401 ----------

ENDPOINTS = [("", {"name": "New"}), ("/status", {"status": "INACTIVE"})]


@pytest.mark.parametrize("suffix,body", ENDPOINTS)
def test_unknown_team_returns_404(client, make_employee, suffix, body):
    r = client.patch(f"{URL}/999{suffix}", json=body, headers=headers("TEAM_LEAD", make_employee().id))

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("suffix,body", ENDPOINTS)
@pytest.mark.parametrize("role", ["HR_ADMIN", "EMPLOYEE"])
def test_other_roles_get_403(client, team_with_lead, make_employee, suffix, body, role):
    team, _ = team_with_lead()
    member = make_employee(team_id=team["id"])  # even a member of the team

    r = client.patch(f"{URL}/{team['id']}{suffix}", json=body, headers=headers(role, member.id))

    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.parametrize("suffix,body", ENDPOINTS)
def test_lead_of_another_team_gets_403(client, team_with_lead, suffix, body):
    team, _ = team_with_lead("Development")
    _, other_lead = team_with_lead("Ops")

    r = client.patch(f"{URL}/{team['id']}{suffix}", json=body, headers=headers("TEAM_LEAD", other_lead.id))

    assert r.status_code == 403


@pytest.mark.parametrize("suffix,body", ENDPOINTS)
def test_without_login_returns_401(client, team_with_lead, suffix, body):
    team, _ = team_with_lead()

    assert client.patch(f"{URL}/{team['id']}{suffix}", json=body).status_code == 401
