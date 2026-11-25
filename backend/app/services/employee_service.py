"""Business rules for employees (Member 3 – Employee Management)."""  # File description

from sqlalchemy import func, select          # SQLAlchemy tools: select = build a database query, func = SQL functions like lower()
from sqlalchemy.orm import Session           # Session = our connection to the database

from app.errors import EMAIL_TAKEN, EMPLOYEE_REF_TAKEN, NOT_FOUND, TEAM_INACTIVE, ApiError  # Error codes + the error class
from app.models import Employee, EmployeeStatus, Team, TeamStatus  # Database tables and their allowed values
from app.schemas.employee import EmployeeCreate                    # The form we made in schemas/employee.py


def _email_taken(db: Session, email: str, except_employee_id: int | None = None) -> bool:  # Is this email already used?
    """True if another employee already uses this email (ignoring upper/lower case)."""
    stmt = select(Employee.id).where(func.lower(Employee.email) == email.lower())  # Find an employee with the same email (small letters)
    if except_employee_id is not None:                      # When editing, ignore the employee's own email
        stmt = stmt.where(Employee.id != except_employee_id)  # Exclude that employee from the search
    return db.execute(stmt).first() is not None             # True if the database found someone


def _ref_taken(db: Session, ref: str, except_employee_id: int | None = None) -> bool:  # Is this employee reference already used?
    """True if another employee already uses this employee reference."""
    stmt = select(Employee.id).where(Employee.employee_ref == ref)  # Find an employee with the same reference
    if except_employee_id is not None:                      # When editing, ignore the employee's own reference
        stmt = stmt.where(Employee.id != except_employee_id)  # Exclude that employee from the search
    return db.execute(stmt).first() is not None             # True if the database found someone


def _check_team_can_take_members(db: Session, team_id: int) -> None:  # Can employees be added to this team?
    """The team must exist (404 NOT_FOUND) and be ACTIVE (409 TEAM_INACTIVE)."""
    team = db.get(Team, team_id)                            # Load the team from the database by its id
    if team is None:                                        # No team with this id
        raise ApiError(404, NOT_FOUND, "Team not found.")   # Stop -> API returns 404 NOT_FOUND
    if team.status != TeamStatus.ACTIVE:                    # Team exists but is INACTIVE
        raise ApiError(409, TEAM_INACTIVE, "Employees can only be assigned to an active team.")  # Stop -> 409 TEAM_INACTIVE


def create_employee(db: Session, data: EmployeeCreate) -> Employee:  # Main function: create a new employee
    """Create an employee (status ACTIVE).

    Rules (Work Division, Member 3):
    - email is unique, ignoring upper/lower case -> 409 EMAIL_TAKEN
    - employee reference (if given) is unique -> 409 EMPLOYEE_REF_TAKEN
    - a given team must exist and be active -> 404 NOT_FOUND / 409 TEAM_INACTIVE
    Field checks (required fields, FTE range, contract dates) happen in EmployeeCreate.
    """
    if _email_taken(db, data.email):                        # Email already used by someone?
        raise ApiError(409, EMAIL_TAKEN, "An employee with this email already exists.")  # Stop -> 409 EMAIL_TAKEN
    if data.employee_ref is not None and _ref_taken(db, data.employee_ref):  # Reference given AND already used?
        raise ApiError(409, EMPLOYEE_REF_TAKEN, "An employee with this reference already exists.")  # Stop -> 409
    if data.team_id is not None:                            # A team was chosen?
        _check_team_can_take_members(db, data.team_id)      # Check that the team exists and is active

    employee = Employee(**data.model_dump(), status=EmployeeStatus.ACTIVE)  # Build a new employee row from the form; status = ACTIVE
    db.add(employee)                                        # Put it in the database session
    db.commit()                                             # Save it permanently in the database
    db.refresh(employee)                                    # Reload it, so we get the new id from the database
    return employee                                         # Send the saved employee back to the router