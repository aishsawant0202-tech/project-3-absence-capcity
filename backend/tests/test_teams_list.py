"""TM-02 – View teams: GET /api/v1/teams"""

import pytest

from app.models import Team, TeamStatus
from tests.conftest import headers

URL = "/api/v1/teams"
TEAM_FIELDS = {"id", "teamRef", "name", "description", "minRequiredFte", "teamLeadEmployeeId", "status"}


@pytest.fixture
def make_team(client, make_employee):
    """Create a team through the API (each with its own new lead) and return its JSON."""

    def _make(name: str, fte: float = 1):
        lead = make_employee()
        r = client.post(URL, json={"name": name, "minRequiredFte": fte}, headers=headers("TEAM_LEAD", lead.id))
        assert r.status_code == 201
        return r.json()

    return _make


def test_empty_database_returns_empty_list(client):
    r = client.get(URL, headers=headers("EMPLOYEE", 1))

    assert r.status_code == 200
    assert r.json() == []


def test_returns_active_and_inactive_teams(client, make_team, db):
    make_team("Development")
    ops = make_team("Ops")
    db.get(Team, ops["id"]).status = TeamStatus.INACTIVE
    db.commit()

    r = client.get(URL, headers=headers("EMPLOYEE", 1))

    assert {t["name"]: t["status"] for t in r.json()} == {"Development": "ACTIVE", "Ops": "INACTIVE"}


def test_sorted_by_name_ignoring_case(client, make_team):
    for name in ["sales", "Development", "ops", "Admin"]:
        make_team(name)

    r = client.get(URL, headers=headers("EMPLOYEE", 1))

    assert [t["name"] for t in r.json()] == ["Admin", "Development", "ops", "sales"]


def test_items_have_only_team_fields(client, make_team):
    created = make_team("Development", fte=2.5)

    item = client.get(URL, headers=headers("EMPLOYEE", 1)).json()[0]

    assert set(item) == TEAM_FIELDS  # no employee details
    assert item == created  # same shape and values as the create response
    assert item["minRequiredFte"] == 2.5


@pytest.mark.parametrize("role", ["EMPLOYEE", "TEAM_LEAD", "HR_ADMIN"])
def test_every_role_can_list(client, make_team, role):
    make_team("Development")

    r = client.get(URL, headers=headers(role, 1))

    assert r.status_code == 200
    assert len(r.json()) == 1


def test_without_login_headers_returns_401(client):
    r = client.get(URL)

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"
