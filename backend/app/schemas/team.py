"""Team request/response bodies.

JSON uses camelCase (API contract v2, section 1): `minRequiredFte`, `teamLeadEmployeeId`, ...
Python code keeps snake_case (`data.min_required_fte`); Pydantic converts with the alias generator.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.models import EmployeeStatus, Employee, TeamStatus


class CamelModel(BaseModel):
    """Base for API bodies: snake_case in Python, camelCase in JSON (both accepted on input)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TeamCreate(CamelModel):
    """Request body for POST /api/v1/teams."""

    name: str = Field(max_length=100, examples=["Development"])
    description: str | None = Field(default=None, examples=["Software development team"])
    min_required_fte: Decimal = Field(
        ge=0, max_digits=5, decimal_places=2, examples=[5.0]
    )

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Team name must not be blank.")
        return value


class TeamUpdate(CamelModel):
    """Request body for PATCH /api/v1/teams/{id}: only the fields that are sent are changed.

    Same rules as TeamCreate. Status and team lead cannot be changed here (unknown fields -> 400).
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=100, examples=["Development"])
    description: str | None = Field(default=None, examples=["Software development team"])
    min_required_fte: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2, examples=[5.0])

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str | None) -> str:
        # Runs only when "name" is sent; null or blank is not allowed (a team always has a name)
        value = (value or "").strip()
        if not value:
            raise ValueError("Team name must not be blank.")
        return value

    @field_validator("min_required_fte")
    @classmethod
    def fte_not_null(cls, value: Decimal | None) -> Decimal:
        if value is None:
            raise ValueError("Minimum required capacity must not be empty.")
        return value


class TeamStatusUpdate(CamelModel):
    """Request body for PATCH /api/v1/teams/{id}/status."""

    model_config = ConfigDict(extra="forbid")

    status: TeamStatus = Field(examples=["INACTIVE"])


class TeamRead(CamelModel):
    """Team as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    team_ref: str | None
    name: str
    description: str | None
    min_required_fte: float
    team_lead_employee_id: int | None
    status: TeamStatus


class TeamMemberBrief(CamelModel):
    """A team member as ordinary members see them (contract v2: only id and name)."""

    id: int
    name: str = Field(examples=["Maria Weber"])

    @classmethod
    def from_employee(cls, e: Employee) -> "TeamMemberBrief":
        return cls(id=e.id, name=f"{e.first_name} {e.last_name}")


class TeamMemberRead(TeamMemberBrief):
    """A team member as HR Admin and the lead of the team see them."""

    email: str
    job_title: str | None
    working_time_share: float = Field(examples=[1.0])
    status: EmployeeStatus

    @classmethod
    def from_employee(cls, e: Employee) -> "TeamMemberRead":
        return cls(
            id=e.id,
            name=f"{e.first_name} {e.last_name}",
            email=e.email,
            job_title=e.job_title,
            working_time_share=float(e.working_time_share),
            status=e.status,
        )
