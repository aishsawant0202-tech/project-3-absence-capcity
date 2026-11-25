"""Employee form fields and their rules (Member 3 – Employee Management)."""  # File description

import re                                    # Tool to check text patterns (used for email)
from datetime import date                    # Date type, e.g. 2026-11-01
from decimal import Decimal                  # Exact decimal numbers, e.g. 0.5 (used for FTE)

from pydantic import Field, field_validator, model_validator  # Pydantic: library that checks incoming data

from app.models import EmployeeStatus, EmploymentType  # Allowed values: ACTIVE/INACTIVE, PERMANENT/CONTRACT
from app.schemas.team import CamelModel                # Base class: JSON uses camelCase (firstName)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")  # Email must look like: name@domain.com


class EmployeeCreate(CamelModel):            # Data the HR Admin SENDS to create an employee
    """Request body for POST /api/v1/employees."""

    employee_ref: str | None = Field(default=None, max_length=50, examples=[None])            # Optional business reference, max 50 chars
    first_name: str = Field(max_length=100, examples=["Alex"])                                # Required first name, max 100 chars
    last_name: str = Field(max_length=100, examples=["Miller"])                               # Required last name, max 100 chars
    email: str = Field(max_length=255, examples=["alex.miller@example.com"])                  # Required email, max 255 chars
    team_id: int | None = Field(default=None, examples=[1])                                   # Optional team id (null = no team)
    job_title: str | None = Field(default=None, max_length=100, examples=["Software Engineer"])  # Optional job title
    employment_type: EmploymentType = Field(examples=["PERMANENT"])                           # Required: PERMANENT or CONTRACT
    working_time_share: Decimal = Field(                                                      # FTE (working time share)
        default=Decimal("1.0"), gt=0, le=1, max_digits=5, decimal_places=2, examples=[1.0]    # Default 1.0; must be > 0 and <= 1
    )
    start_date: date = Field(examples=["2026-11-01"])                                         # Required start date
    end_date: date | None = Field(default=None, examples=[None])                              # Optional end date (needed for CONTRACT)

    @field_validator("first_name", "last_name")   # Run this check on first_name and last_name
    @classmethod                                  # Required by Pydantic for validators
    def not_blank(cls, value: str) -> str:        # Check: name must not be empty
        value = value.strip()                     # Remove spaces at the start and end
        if not value:                             # If nothing is left (only spaces were sent)
            raise ValueError("Must not be blank.")  # Reject -> API returns 400 VALIDATION_ERROR
        return value                              # Keep the cleaned name

    @field_validator("email")                     # Run this check on email
    @classmethod                                  # Required by Pydantic for validators
    def valid_email(cls, value: str) -> str:      # Check: email must look valid
        value = value.strip().lower()             # Remove spaces and convert to small letters
        if not _EMAIL_PATTERN.match(value):       # If it does not match name@domain.com
            raise ValueError("Not a valid email address.")  # Reject -> 400 VALIDATION_ERROR
        return value                              # Keep the cleaned email

    @field_validator("employee_ref", "job_title")  # Run this check on employee_ref and job_title
    @classmethod                                   # Required by Pydantic for validators
    def blank_to_none(cls, value: str | None) -> str | None:  # Turn empty text into "no value"
        if value is None:                          # Nothing was sent
            return None                            # Keep it empty
        value = value.strip()                      # Remove spaces at the start and end
        return value or None                       # Empty text -> None, otherwise keep the text

    @model_validator(mode="after")                 # Runs after all fields are checked (compares fields)
    def check_dates(self) -> "EmployeeCreate":     # Check: dates must fit the employment type
        if self.employment_type == EmploymentType.CONTRACT:  # If the employee is on a contract
            if self.end_date is None:                        # Contract without end date
                raise ValueError("A contract employee needs an end date.")      # Reject
            if self.end_date < self.start_date:              # End date is before start date
                raise ValueError("End date must not be before start date.")     # Reject
        elif self.end_date is not None:                      # Permanent employee with an end date
            raise ValueError("A permanent employee must not have an end date.")  # Reject
        return self                                          # All dates are fine


class EmployeeRead(CamelModel):                  # Data the API SENDS BACK in the response
    """Employee as returned by the API."""

    model_config = CamelModel.model_config | {"from_attributes": True}  # Read values directly from the database row

    id: int                                      # Employee id (created by the database)
    employee_ref: str | None                     # Business reference or null
    first_name: str                              # First name
    last_name: str                               # Last name
    email: str                                   # Email
    team_id: int | None                          # Team id or null
    job_title: str | None                        # Job title or null
    employment_type: EmploymentType              # PERMANENT or CONTRACT
    working_time_share: float                    # FTE as a normal number, e.g. 1.0
    start_date: date                             # Start date
    end_date: date | None                        # End date or null
    status: EmployeeStatus                       # ACTIVE or INACTIVE