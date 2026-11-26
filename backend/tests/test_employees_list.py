"""EM-02 – View and search employees: GET /api/v1/employees and GET /api/v1/employees/{id}"""  # Tests for US-02

from datetime import date      # Dates for test employees
from decimal import Decimal    # Exact numbers (team FTE)

import pytest                  # Testing tool

from app.models import Employee, EmployeeStatus, EmploymentType, Team, TeamStatus  # Database tables and values
from tests.conftest import headers                                                 # Builds login headers

URL = "/api/v1/employees"      # The API we test


@pytest.fixture
def team(db):                  # Helper: one active team in the test database
    t = Team(name="Development", min_required_fte=Decimal("1"), status=TeamStatus.ACTIVE)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def people(db, team):          # Helper: four test employees with different data
    def add(first, last, email, team_id=None, status=EmployeeStatus.ACTIVE, contract=False):
        e = Employee(
            first_name=first, last_name=last, email=email, team_id=team_id,
            employment_type=EmploymentType.CONTRACT if contract else EmploymentType.PERMANENT,
            start_date=date(2025, 1, 1),
            end_date=date(2027, 1, 1) if contract else None,
            status=status,
        )
        db.add(e)
        return e

    rahul = add("Rahul", "Sharma", "rahul@example.com", team_id=team.id)              # in team, permanent, active
    ada = add("Ada", "Weber", "ada@example.com", team_id=team.id, contract=True)      # in team, contract
    ben = add("Ben", "Klein", "ben@example.com")                                       # no team
    cara = add("Cara", "Abel", "cara@example.com", status=EmployeeStatus.INACTIVE)    # inactive
    db.commit()
    return {"rahul": rahul, "ada": ada, "ben": ben, "cara": cara}


def ids(response):             # Helper: only the ids from a list response
    return [e["id"] for e in response.json()]


def as_employee(people):       # Helper: login headers of a normal employee (Ben)
    return headers("EMPLOYEE", people["ben"].id)


# ---------- list ----------

def test_list_all_sorted_by_last_name(client, people):   # All employees, sorted A-Z by last name
    r = client.get(URL, headers=as_employee(people))

    assert r.status_code == 200
    # Abel, Klein, Sharma, Weber
    assert ids(r) == [people["cara"].id, people["ben"].id, people["rahul"].id, people["ada"].id]


def test_list_contains_all_fields(client, people):       # Every employee has all fields
    r = client.get(URL, headers=as_employee(people))

    first = r.json()[0]
    for field in ["id", "employeeRef", "firstName", "lastName", "email", "teamId", "jobTitle",
                  "employmentType", "workingTimeShare", "startDate", "endDate", "status"]:
        assert field in first


def test_list_is_empty_when_no_employees(client, db):    # No employees -> []
    r = client.get(URL, headers=headers("HR_ADMIN", 1))

    assert r.status_code == 200
    assert r.json() == []


def test_filter_by_team(client, people, team):           # ?teamId= -> only that team
    r = client.get(URL, params={"teamId": team.id}, headers=as_employee(people))

    assert sorted(ids(r)) == sorted([people["rahul"].id, people["ada"].id])


def test_filter_by_status(client, people):               # ?status=INACTIVE -> only inactive
    r = client.get(URL, params={"status": "INACTIVE"}, headers=as_employee(people))

    assert ids(r) == [people["cara"].id]


def test_filter_by_employment_type(client, people):      # ?employmentType=CONTRACT -> only contract
    r = client.get(URL, params={"employmentType": "CONTRACT"}, headers=as_employee(people))

    assert ids(r) == [people["ada"].id]


@pytest.mark.parametrize("text", ["rahul", "RAHUL", "sharma", "Rahul Sharma", "rahul@exa"])
def test_search_by_name_or_email(client, people, text):  # Search finds Rahul by name or email
    r = client.get(URL, params={"search": text}, headers=as_employee(people))

    assert ids(r) == [people["rahul"].id]


def test_filters_can_be_combined(client, people, team):  # Team + status + search together
    r = client.get(URL, params={"teamId": team.id, "status": "ACTIVE", "search": "Rahul"},
                   headers=as_employee(people))

    assert ids(r) == [people["rahul"].id]


def test_no_match_returns_empty_list(client, people):    # Nothing found -> [] (not an error)
    r = client.get(URL, params={"search": "xyz"}, headers=as_employee(people))

    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.parametrize("params", [{"status": "SLEEPING"}, {"employmentType": "FREELANCE"}, {"teamId": "abc"}])
def test_invalid_filter_is_rejected(client, people, params):  # Wrong filter values -> 400
    r = client.get(URL, params=params, headers=as_employee(people))

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_needs_login(client, people):               # No login -> 401
    r = client.get(URL)

    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


# ---------- details ----------

def test_get_one_employee(client, people, team):         # One employee with correct data
    rahul = people["rahul"]

    r = client.get(f"{URL}/{rahul.id}", headers=as_employee(people))

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == rahul.id
    assert body["firstName"] == "Rahul"
    assert body["email"] == "rahul@example.com"
    assert body["teamId"] == team.id
    assert body["status"] == "ACTIVE"


def test_inactive_employee_can_be_viewed(client, people):  # Inactive employees can be opened too
    r = client.get(f"{URL}/{people['cara'].id}", headers=as_employee(people))

    assert r.status_code == 200
    assert r.json()["status"] == "INACTIVE"


def test_unknown_employee_is_404(client, people):        # Unknown id -> 404
    r = client.get(f"{URL}/999", headers=as_employee(people))

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_id_must_be_a_number(client, people):            # /employees/abc -> 400
    r = client.get(f"{URL}/abc", headers=as_employee(people))

    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_details_need_login(client, people):             # No login -> 401
    r = client.get(f"{URL}/{people['ben'].id}")

    assert r.status_code == 401