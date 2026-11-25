"""Employee Management API (Member 3)."""  # File description

from fastapi import APIRouter, Depends, status  # FastAPI tools: APIRouter = group of URLs, Depends = run a check first, status = HTTP codes
from sqlalchemy.orm import Session              # Session = our connection to the database

from app.database import get_db                         # Gives each request a database connection
from app.dependencies import CurrentUser, require_role  # Who is calling + "only these roles allowed" check
from app.errors import ErrorResponse                    # Error format, shown in Swagger
from app.models import SystemRole                       # Roles: EMPLOYEE / TEAM_LEAD / HR_ADMIN
from app.schemas.employee import EmployeeCreate, EmployeeRead  # Our form (input) and response (output)
from app.services import employee_service               # Our business rules (service file)


router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])  # All URLs here start with /api/v1/employees; shown as "Employees" in Swagger


@router.post(                                   # This function answers POST requests
    "",                                         # URL = /api/v1/employees (nothing added to the prefix)
    response_model=EmployeeRead,                # The response uses the EmployeeRead format
    status_code=status.HTTP_201_CREATED,        # Success returns 201 Created
    summary="Create an employee (HR Admin only)",  # Title shown in Swagger
    description="`teamId` may be null (employee without a team). CONTRACT needs `endDate`; "
                "PERMANENT must not have one. New employees are ACTIVE.",  # Help text shown in Swagger
    responses={                                 # Possible errors, listed in Swagger
        400: {"model": ErrorResponse, "description": "VALIDATION_ERROR: missing or invalid field"},
        401: {"model": ErrorResponse, "description": "UNAUTHENTICATED: not logged in or unknown role"},
        403: {"model": ErrorResponse, "description": "FORBIDDEN: not HR Admin"},
        404: {"model": ErrorResponse, "description": "NOT_FOUND: the given team does not exist"},
        409: {"model": ErrorResponse, "description": "EMAIL_TAKEN, EMPLOYEE_REF_TAKEN or TEAM_INACTIVE"},
    },
)
def create_employee(                            # The function that runs for POST /api/v1/employees
    data: EmployeeCreate,                       # The JSON body, already checked by our schema
    db: Session = Depends(get_db),              # Get a database connection
    user: CurrentUser = Depends(require_role(SystemRole.HR_ADMIN)),  # Only HR_ADMIN may continue; others get 403
):
    return employee_service.create_employee(db, data)  # Let the service check the rules and save the employee