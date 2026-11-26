"""Employee Management API (Member 3)."""  # File description

from fastapi import APIRouter, Depends, Query, status  # APIRouter = group of URLs, Depends = run a check first, Query = URL filters, status = HTTP codes
from sqlalchemy.orm import Session                     # Session = our connection to the database

from app.database import get_db                                           # Gives each request a database connection
from app.dependencies import CurrentUser, get_current_user, require_role  # Who is calling, "must be logged in", "only these roles"
from app.errors import ErrorResponse                                      # Error format, shown in Swagger
from app.models import EmployeeStatus, EmploymentType, SystemRole         # Allowed values for filters + roles
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeStatusUpdate, EmployeeUpdate  # Forms and response
from app.services import employee_service                                 # Our business rules (service file)


router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])  # All URLs here start with /api/v1/employees


# ===================== US-01: create =====================

@router.post(                                   # POST /api/v1/employees
    "",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an employee (HR Admin only)",
    description="`teamId` may be null (employee without a team). CONTRACT needs `endDate`; "
                "PERMANENT must not have one. New employees are ACTIVE.",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: missing or invalid field"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN: not HR Admin"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: the given team does not exist"},
        409: {"model": ErrorResponse, "description": "EMAIL_TAKEN, EMPLOYEE_REF_TAKEN or TEAM_INACTIVE"},
    },
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role(SystemRole.HR_ADMIN)),  # Only HR_ADMIN
):
    return employee_service.create_employee(db, data)


# ===================== US-02: list =====================

@router.get(                                    # GET /api/v1/employees
    "",
    response_model=list[EmployeeRead],
    summary="List employees, with filters and search (all logged-in users)",
    description="All filters are optional and can be combined. `search` looks in first name, last name "
                "and email (not case-sensitive). Sorted by last name. `[]` when nothing matches.",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: invalid filter value"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
    },
)
def list_employees(
    team_id: int | None = Query(default=None, alias="teamId", description="Only employees of this team"),
    employee_status: EmployeeStatus | None = Query(default=None, alias="status", description="ACTIVE or INACTIVE"),
    employment_type: EmploymentType | None = Query(default=None, alias="employmentType", description="PERMANENT or CONTRACT"),
    search: str | None = Query(default=None, max_length=100, description="Part of a name or email, e.g. `rahul`"),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),  # Any logged-in user
):
    return employee_service.list_employees(db, team_id, employee_status, employment_type, search)


# ===================== US-04: my profile (MUST stay above /{employee_id}) =====================

@router.get(                                    # GET /api/v1/employees/me
    "/me",
    response_model=EmployeeRead,
    summary="My own employee profile (all logged-in users)",
    description="The employee record of the caller. Must stay ABOVE `/{employee_id}`, "
                "otherwise FastAPI reads `me` as an id.",
    responses={
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: no employee record for this user"},
    },
)
def get_my_profile(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),  # Any logged-in user
):
    return employee_service.get_employee(db, user.employee_id)  # Always the caller's OWN id, never another one


# ===================== US-02: details =====================

@router.get(                                    # GET /api/v1/employees/5
    "/{employee_id}",
    response_model=EmployeeRead,
    summary="Get one employee (all logged-in users)",
    description="Active or inactive employee by id.",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: employee id is not a number"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: no employee with this id"},
    },
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return employee_service.get_employee(db, employee_id)


# ===================== US-03: update and team transfer =====================

@router.patch(                                  # PATCH /api/v1/employees/5
    "/{employee_id}",
    response_model=EmployeeRead,
    summary="Edit an employee or move them to another team (HR Admin only)",
    description="Send only the fields to change. `teamId` = another active team (transfer) or `null` "
                "(no team). Status is changed with `/status`, not here.",
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: invalid or unknown field, or wrong dates"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN: not HR Admin"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: no employee or team with this id"},
        409: {"model": ErrorResponse, "description": "EMAIL_TAKEN, EMPLOYEE_REF_TAKEN or TEAM_INACTIVE"},
    },
)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role(SystemRole.HR_ADMIN)),  # Only HR_ADMIN
):
    employee = employee_service.get_employee(db, employee_id)
    return employee_service.update_employee(db, employee, data)


# ===================== US-04: activate / deactivate =====================

@router.patch(                                  # PATCH /api/v1/employees/5/status
    "/{employee_id}/status",
    response_model=EmployeeRead,
    summary="Activate or deactivate an employee (HR Admin only)",
    description='Body `{"status": "ACTIVE"}` or `{"status": "INACTIVE"}`. Employees are never deleted.',
    responses={
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: status must be ACTIVE or INACTIVE"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN: not HR Admin"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: no employee with this id"},
    },
)
def set_employee_status(
    employee_id: int,
    data: EmployeeStatusUpdate,                 # {"status": "INACTIVE"}
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_role(SystemRole.HR_ADMIN)),  # Only HR_ADMIN
):
    employee = employee_service.get_employee(db, employee_id)       # 404 if missing
    return employee_service.set_status(db, employee, data.status)   # Change status and save