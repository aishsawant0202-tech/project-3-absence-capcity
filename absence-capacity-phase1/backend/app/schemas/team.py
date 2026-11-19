from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TeamStatus


class TeamCreate(BaseModel):
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


class TeamRead(BaseModel):
    """Team as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    team_ref: str | None
    name: str
    description: str | None
    min_required_fte: float
    team_lead_employee_id: int | None
    status: TeamStatus
