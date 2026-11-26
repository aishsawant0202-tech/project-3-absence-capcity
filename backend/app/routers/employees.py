"""Employee Management API (Member 3)."""  # File description

from fastapi import APIRouter, Depends, Query, status  # APIRouter = group of URLs, Depends = run a check first, Query = URL filters (?status=...), status = HTTP codes
from sqlalchemy.orm import Session                     # Session = our connection to the database

from app.database import get_db                                           # Gives each request a database connection
from app.dependencies import CurrentUser, get_current_user, require_role  # Who is calling, "must be logged in", "only these roles"
from app.errors import ErrorResponse                                      # Error format, shown in Swagger
from app.models import EmployeeStatus, EmploymentType, SystemRole         # Allowed values for filters + roles
from app.schemas.employee import EmployeeCreate, EmployeeRead             # Our form (input) and response (output)
from app.services import employee_service                                 # Our business rules (service file)


router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])  # All URLs here start with /api/v1/employees


# ===================== US-01: create =====================

@router.post(                                   # Answers POST /api/v1/employees
    "",
    response_model=EmployeeRead,                # Response uses the EmployeeRead format
    status_code=status.HTTP_201_CREATED,        # Success returns 201 Created
    summary="Create an employee (HR Admin only)",
    description="`teamId` may be null (employee without a team). CONTRACT needs `endDate`; "
                "PERMANENT must not have one. New employees are ACTIVE.",
    responses={                                 # Possible errors, listed in Swagger
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: missing or invalid field"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN: not HR Admin"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: the given team does not exist"},
        409: {"model": ErrorResponse, "description": "EMAIL_TAKEN, EMPLOYEE_REF_TAKEN or TEAM_INACTIVE"},
    },
)
def create_employee(
    data: EmployeeCreate,                       # JSON body, already checked by the schema
    db: Session = Depends(get_db),              # Database connection
    user: CurrentUser = Depends(require_role(SystemRole.HR_ADMIN)),  # Only HR_ADMIN; others get 403
):
    return employee_service.create_employee(db, data)  # Service checks the rules and saves


# ===================== US-02: list and details =====================

@router.get(                                    # Answers GET /api/v1/employees
    "",
    response_model=list[EmployeeRead],          # Response is a LIST of employees
    summary="List employees, with filters and search (all logged-in users)",
    description="All filters are optional and can be combined. `search` looks in first name, last name "
                "and email (not case-sensitive). Sorted by last name. `[]` when nothing matches.",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: invalid filter value"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
    },
)
def list_employees(
    team_id: int | None = Query(default=None, alias="teamId", description="Only employees of this team"),                    # ?teamId=1
    employee_status: EmployeeStatus | None = Query(default=None, alias="status", description="ACTIVE or INACTIVE"),          # ?status=ACTIVE
    employment_type: EmploymentType | None = Query(default=None, alias="employmentType", description="PERMANENT or CONTRACT"),  # ?employmentType=CONTRACT
    search: str | None = Query(default=None, max_length=100, description="Part of a name or email, e.g. `rahul`"),           # ?search=rahul
    db: Session = Depends(get_db),              # Database connection
    user: CurrentUser = Depends(get_current_user),  # Any logged-in user; not logged in -> 401
):
    return employee_service.list_employees(db, team_id, employee_status, employment_type, search)  # Service filters and sorts


@router.get(                                    # Answers GET /api/v1/employees/5
    "/{employee_id}",                           # {employee_id} = the number in the URL
    response_model=EmployeeRead,                # Response is ONE employee
    summary="Get one employee (all logged-in users)",
    description="Active or inactive employee by id.",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: employee id is not a number"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: no employee with this id"},
    },
)
def get_employee(
    employee_id: int,                           # Taken from the URL; must be a number
    db: Session = Depends(get_db),              # Database connection
    user: CurrentUser = Depends(get_current_user),  # Any logged-in user; not logged in -> 401
):
    return employee_service.get_employee(db, employee_id)  # Service finds it or returns 404