"""Employee form fields and their rules (Member 3 – Employee Management)."""  # File description

import re                                    # Tool to check text patterns (used for email)
from datetime import date                    # Date type, e.g. 2026-11-01
from decimal import Decimal                  # Exact decimal numbers, e.g. 0.5 (used for FTE)

from pydantic import Field, field_validator, model_validator  # Pydantic: library that checks incoming data

from app.models import EmployeeStatus, EmploymentType  # Allowed values: ACTIVE/INACTIVE, PERMANENT/CONTRACT
from app.schemas.team import CamelModel                # Base class: JSON uses camelCase (firstName)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")  # Email must look like: name@domain.com


# ===================== US-01: create form =====================

class EmployeeCreate(CamelModel):            # Data the HR Admin SENDS to create an employee
    """Request body for POST /api/v1/employees."""

    employee_ref: str | None = Field(default=None, max_length=50, examples=[None])            # Optional business reference
    first_name: str = Field(max_length=100, examples=["Alex"])                                # Required first name
    last_name: str = Field(max_length=100, examples=["Miller"])                               # Required last name
    email: str = Field(max_length=255, examples=["alex.miller@example.com"])                  # Required email
    team_id: int | None = Field(default=None, examples=[1])                                   # Optional team id (null = no team)
    job_title: str | None = Field(default=None, max_length=100, examples=["Software Engineer"])  # Optional job title
    employment_type: EmploymentType = Field(examples=["PERMANENT"])                           # Required: PERMANENT or CONTRACT
    working_time_share: Decimal = Field(                                                      # FTE (working time share)
        default=Decimal("1.0"), gt=0, le=1, max_digits=5, decimal_places=2, examples=[1.0]    # Default 1.0; must be > 0 and <= 1
    )
    start_date: date = Field(examples=["2026-11-01"])                                         # Required start date
    end_date: date | None = Field(default=None, examples=[None])                              # End date (needed for CONTRACT)

    @field_validator("first_name", "last_name")   # Check first and last name
    @classmethod
    def not_blank(cls, value: str) -> str:        # Name must not be empty
        value = value.strip()
        if not value:
            raise ValueError("Must not be blank.")
        return value

    @field_validator("email")                     # Check email
    @classmethod
    def valid_email(cls, value: str) -> str:      # Email must look valid, saved in small letters
        value = value.strip().lower()
        if not _EMAIL_PATTERN.match(value):
            raise ValueError("Not a valid email address.")
        return value

    @field_validator("employee_ref", "job_title")  # Empty text -> "no value"
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")                 # Compare fields after all are checked
    def check_dates(self) -> "EmployeeCreate":     # Dates must fit the employment type
        if self.employment_type == EmploymentType.CONTRACT:
            if self.end_date is None:
                raise ValueError("A contract employee needs an end date.")
            if self.end_date < self.start_date:
                raise ValueError("End date must not be before start date.")
        elif self.end_date is not None:
            raise ValueError("A permanent employee must not have an end date.")
        return self


# ===================== Response format =====================

class EmployeeRead(CamelModel):                  # Data the API SENDS BACK
    """Employee as returned by the API."""

    model_config = CamelModel.model_config | {"from_attributes": True}  # Read values from the database row

    id: int
    employee_ref: str | None
    first_name: str
    last_name: str
    email: str
    team_id: int | None
    job_title: str | None
    employment_type: EmploymentType
    working_time_share: float
    start_date: date
    end_date: date | None
    status: EmployeeStatus


# ===================== US-03: edit form =====================

class EmployeeUpdate(CamelModel):                # Data the HR Admin sends to EDIT an employee
    """Request body for PATCH /api/v1/employees/{id}: only the fields that are sent are changed."""

    model_config = CamelModel.model_config | {"extra": "forbid"}  # Unknown fields (e.g. "status") -> 400 error

    employee_ref: str | None = Field(default=None, max_length=50)                                         # Business reference
    first_name: str | None = Field(default=None, max_length=100, examples=["Alex"])                       # First name
    last_name: str | None = Field(default=None, max_length=100, examples=["Miller"])                      # Last name
    email: str | None = Field(default=None, max_length=255, examples=["alex.miller@example.com"])          # Email
    team_id: int | None = Field(default=None, examples=[2])                                               # New team id, or null = no team
    job_title: str | None = Field(default=None, max_length=100, examples=["Senior Software Engineer"])     # Job title
    employment_type: EmploymentType | None = Field(default=None, examples=["PERMANENT"])                  # PERMANENT or CONTRACT
    working_time_share: Decimal | None = Field(default=None, gt=0, le=1, max_digits=5, decimal_places=2, examples=[0.8])  # FTE
    start_date: date | None = Field(default=None, examples=["2026-11-01"])                                # Start date
    end_date: date | None = Field(default=None, examples=[None])                                          # End date

    @field_validator("first_name", "last_name")   # Runs only if the name is sent
    @classmethod
    def not_blank(cls, value: str | None) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("Must not be blank.")
        return value

    @field_validator("email")                     # Runs only if the email is sent
    @classmethod
    def valid_email(cls, value: str | None) -> str:
        value = (value or "").strip().lower()
        if not _EMAIL_PATTERN.match(value):
            raise ValueError("Not a valid email address.")
        return value

    @field_validator("employee_ref", "job_title")  # Empty text -> "no value"
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("employment_type", "working_time_share", "start_date")  # May be changed, not removed
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("Must not be empty.")
        return value

        

class EmployeeStatusUpdate(CamelModel):          # US-04: body for activate / deactivate
    """Request body for PATCH /api/v1/employees/{id}/status."""

    model_config = CamelModel.model_config | {"extra": "forbid"}  # Only "status" is allowed

    status: EmployeeStatus = Field(examples=["INACTIVE"])         # ACTIVE or INACTIVE
    