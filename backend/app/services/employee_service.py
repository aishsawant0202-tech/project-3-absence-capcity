"""Business rules for employees (Member 3 – Employee Management)."""  # File description

from sqlalchemy import func, or_, select     # select = build a query, func = SQL functions like lower(), or_ = "this OR that"
from sqlalchemy.orm import Session           # Session = our connection to the database

from app.errors import EMAIL_TAKEN, EMPLOYEE_REF_TAKEN, NOT_FOUND, TEAM_INACTIVE, ApiError  # Error codes + the error class
from app.models import Employee, EmployeeStatus, EmploymentType, Team, TeamStatus  # Database tables and allowed values
from app.schemas.employee import EmployeeCreate                    # The form from schemas/employee.py


# ===================== US-01: helpers and create =====================

def _email_taken(db: Session, email: str, except_employee_id: int | None = None) -> bool:  # Is this email already used?
    """True if another employee already uses this email (ignoring upper/lower case)."""
    stmt = select(Employee.id).where(func.lower(Employee.email) == email.lower())  # Find an employee with the same email
    if except_employee_id is not None:                      # When editing, ignore the employee's own email
        stmt = stmt.where(Employee.id != except_employee_id)
    return db.execute(stmt).first() is not None             # True if someone was found


def _ref_taken(db: Session, ref: str, except_employee_id: int | None = None) -> bool:  # Is this reference already used?
    """True if another employee already uses this employee reference."""
    stmt = select(Employee.id).where(Employee.employee_ref == ref)  # Find an employee with the same reference
    if except_employee_id is not None:                      # When editing, ignore the employee's own reference
        stmt = stmt.where(Employee.id != except_employee_id)
    return db.execute(stmt).first() is not None             # True if someone was found


def _check_team_can_take_members(db: Session, team_id: int) -> None:  # Can employees be added to this team?
    """The team must exist (404 NOT_FOUND) and be ACTIVE (409 TEAM_INACTIVE)."""
    team = db.get(Team, team_id)                            # Load the team by its id
    if team is None:                                        # No such team
        raise ApiError(404, NOT_FOUND, "Team not found.")
    if team.status != TeamStatus.ACTIVE:                    # Team is INACTIVE
        raise ApiError(409, TEAM_INACTIVE, "Employees can only be assigned to an active team.")


def create_employee(db: Session, data: EmployeeCreate) -> Employee:  # US-01: create a new employee
    """Create an employee (status ACTIVE). Duplicate email/reference -> 409; bad team -> 404/409."""
    if _email_taken(db, data.email):                        # Email already used?
        raise ApiError(409, EMAIL_TAKEN, "An employee with this email already exists.")
    if data.employee_ref is not None and _ref_taken(db, data.employee_ref):  # Reference already used?
        raise ApiError(409, EMPLOYEE_REF_TAKEN, "An employee with this reference already exists.")
    if data.team_id is not None:                            # A team was chosen?
        _check_team_can_take_members(db, data.team_id)      # It must exist and be active

    employee = Employee(**data.model_dump(), status=EmployeeStatus.ACTIVE)  # New row from the form; status ACTIVE
    db.add(employee)                                        # Put it in the session
    db.commit()                                             # Save permanently
    db.refresh(employee)                                    # Reload to get the new id
    return employee


# ===================== US-02: list, search and details =====================

def list_employees(                                         # US-02: list employees with optional filters
    db: Session,
    team_id: int | None = None,                             # Only this team (optional)
    status: EmployeeStatus | None = None,                   # Only ACTIVE or INACTIVE (optional)
    employment_type: EmploymentType | None = None,          # Only PERMANENT or CONTRACT (optional)
    search: str | None = None,                              # Text to find in name or email (optional)
) -> list[Employee]:
    """Employees sorted by last name, then first name. No match -> [] (empty list), never an error."""
    stmt = select(Employee)                                 # Start with "all employees"
    if team_id is not None:                                 # Team filter given?
        stmt = stmt.where(Employee.team_id == team_id)      # Keep only that team
    if status is not None:                                  # Status filter given?
        stmt = stmt.where(Employee.status == status)        # Keep only that status
    if employment_type is not None:                         # Employment type filter given?
        stmt = stmt.where(Employee.employment_type == employment_type)  # Keep only that type
    if search and search.strip():                           # Search text given (and not only spaces)?
        pattern = f"%{search.strip().lower()}%"             # "%rahul%" = contains "rahul" anywhere
        full_name = func.lower(Employee.first_name + " " + Employee.last_name)  # "rahul sharma"
        stmt = stmt.where(or_(                              # Match if ANY of these contains the text:
            func.lower(Employee.first_name).like(pattern),  #   first name
            func.lower(Employee.last_name).like(pattern),   #   last name
            full_name.like(pattern),                        #   full name
            func.lower(Employee.email).like(pattern),       #   email
        ))
    stmt = stmt.order_by(func.lower(Employee.last_name), func.lower(Employee.first_name), Employee.id)  # Sort A-Z
    return list(db.scalars(stmt))                           # Run the query and return the list


def get_employee(db: Session, employee_id: int) -> Employee:  # US-02: one employee by id
    """The employee with this id (active or inactive). 404 NOT_FOUND if there is none."""
    employee = db.get(Employee, employee_id)                # Load the employee by id
    if employee is None:                                    # Not found
        raise ApiError(404, NOT_FOUND, "Employee not found.")
    return employee