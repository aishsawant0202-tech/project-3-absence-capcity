"""Business rules for employees (Member 3 – Employee Management)."""  # File description

from sqlalchemy import func, or_, select     # select = build a query, func = SQL functions like lower(), or_ = "this OR that"
from sqlalchemy.orm import Session           # Session = our connection to the database

from app.errors import EMAIL_TAKEN, EMPLOYEE_REF_TAKEN, NOT_FOUND, TEAM_INACTIVE, VALIDATION_ERROR, ApiError  # Error codes + error class
from app.models import Employee, EmployeeStatus, EmploymentType, Team, TeamStatus  # Database tables and allowed values
from app.schemas.employee import EmployeeCreate, EmployeeUpdate    # Forms: create (US-01) and edit (US-03)


# ===================== US-01: helpers and create =====================

def _email_taken(db: Session, email: str, except_employee_id: int | None = None) -> bool:  # Is this email already used?
    """True if another employee already uses this email (ignoring upper/lower case)."""
    stmt = select(Employee.id).where(func.lower(Employee.email) == email.lower())
    if except_employee_id is not None:                      # When editing, ignore the employee's own email
        stmt = stmt.where(Employee.id != except_employee_id)
    return db.execute(stmt).first() is not None


def _ref_taken(db: Session, ref: str, except_employee_id: int | None = None) -> bool:  # Is this reference already used?
    """True if another employee already uses this employee reference."""
    stmt = select(Employee.id).where(Employee.employee_ref == ref)
    if except_employee_id is not None:                      # When editing, ignore the employee's own reference
        stmt = stmt.where(Employee.id != except_employee_id)
    return db.execute(stmt).first() is not None


def _check_team_can_take_members(db: Session, team_id: int) -> None:  # Can employees be added to this team?
    """The team must exist (404 NOT_FOUND) and be ACTIVE (409 TEAM_INACTIVE)."""
    team = db.get(Team, team_id)
    if team is None:
        raise ApiError(404, NOT_FOUND, "Team not found.")
    if team.status != TeamStatus.ACTIVE:
        raise ApiError(409, TEAM_INACTIVE, "Employees can only be assigned to an active team.")


def create_employee(db: Session, data: EmployeeCreate) -> Employee:  # US-01: create a new employee
    """Create an employee (status ACTIVE). Duplicate email/reference -> 409; bad team -> 404/409."""
    if _email_taken(db, data.email):
        raise ApiError(409, EMAIL_TAKEN, "An employee with this email already exists.")
    if data.employee_ref is not None and _ref_taken(db, data.employee_ref):
        raise ApiError(409, EMPLOYEE_REF_TAKEN, "An employee with this reference already exists.")
    if data.team_id is not None:
        _check_team_can_take_members(db, data.team_id)

    employee = Employee(**data.model_dump(), status=EmployeeStatus.ACTIVE)  # New row from the form; status ACTIVE
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


# ===================== US-02: list, search and details =====================

def list_employees(                                         # US-02: list employees with optional filters
    db: Session,
    team_id: int | None = None,
    status: EmployeeStatus | None = None,
    employment_type: EmploymentType | None = None,
    search: str | None = None,
) -> list[Employee]:
    """Employees sorted by last name, then first name. No match -> [] (empty list), never an error."""
    stmt = select(Employee)                                 # Start with "all employees"
    if team_id is not None:
        stmt = stmt.where(Employee.team_id == team_id)
    if status is not None:
        stmt = stmt.where(Employee.status == status)
    if employment_type is not None:
        stmt = stmt.where(Employee.employment_type == employment_type)
    if search and search.strip():
        pattern = f"%{search.strip().lower()}%"             # "%rahul%" = contains "rahul" anywhere
        full_name = func.lower(Employee.first_name + " " + Employee.last_name)
        stmt = stmt.where(or_(
            func.lower(Employee.first_name).like(pattern),
            func.lower(Employee.last_name).like(pattern),
            full_name.like(pattern),
            func.lower(Employee.email).like(pattern),
        ))
    stmt = stmt.order_by(func.lower(Employee.last_name), func.lower(Employee.first_name), Employee.id)
    return list(db.scalars(stmt))


def get_employee(db: Session, employee_id: int) -> Employee:  # US-02: one employee by id
    """The employee with this id (active or inactive). 404 NOT_FOUND if there is none."""
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise ApiError(404, NOT_FOUND, "Employee not found.")
    return employee


# ===================== US-03: update and team transfer =====================

def update_employee(db: Session, employee: Employee, data: EmployeeUpdate) -> Employee:  # US-03: edit an employee
    """Change only the fields that were sent. Status is not touched here."""
    changes = data.model_dump(exclude_unset=True)           # Only the fields that were really sent

    # 1) Email and reference must not belong to ANOTHER employee
    if "email" in changes and _email_taken(db, changes["email"], except_employee_id=employee.id):
        raise ApiError(409, EMAIL_TAKEN, "An employee with this email already exists.")
    if changes.get("employee_ref") is not None and _ref_taken(db, changes["employee_ref"], except_employee_id=employee.id):
        raise ApiError(409, EMPLOYEE_REF_TAKEN, "An employee with this reference already exists.")

    # 2) Team transfer: the NEW team must exist and be active (teamId null = remove from team)
    if changes.get("team_id") is not None and changes["team_id"] != employee.team_id:
        _check_team_can_take_members(db, changes["team_id"])

    # 3) Dates: check the FINAL values (new value if sent, otherwise the old one)
    employment_type = changes.get("employment_type", employee.employment_type)
    start_date = changes.get("start_date", employee.start_date)
    end_date = changes.get("end_date", employee.end_date)
    if employment_type == EmploymentType.PERMANENT and "employment_type" in changes and "end_date" not in changes:
        end_date = changes["end_date"] = None               # Switching to PERMANENT removes the old contract end date
    if employment_type == EmploymentType.CONTRACT:
        if end_date is None:
            raise ApiError(400, VALIDATION_ERROR, "A contract employee needs an end date.")
        if end_date < start_date:
            raise ApiError(400, VALIDATION_ERROR, "End date must not be before start date.")
    elif end_date is not None:
        raise ApiError(400, VALIDATION_ERROR, "A permanent employee must not have an end date.")

    # 4) Save: copy each sent field onto the employee
    for field, value in changes.items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee

    

# ===================== US-04: activate / deactivate =====================

def set_status(db: Session, employee: Employee, new_status: EmployeeStatus) -> Employee:  # Change ACTIVE <-> INACTIVE
    """Activate or deactivate an employee. Employees are never deleted; team and history stay."""
    employee.status = new_status                # Only the status changes
    db.commit()                                 # Save permanently
    db.refresh(employee)                        # Reload the saved values
    return employee