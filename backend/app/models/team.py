
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TeamStatus(PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Team(Base):
    __tablename__ = "teams"

    __table_args__ = (
        CheckConstraint(
            "min_required_fte >= 0",
            name="ck_teams_min_required_fte_non_negative",
        ),
    )

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Team information
    team_ref: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # FTE requirement
    min_required_fte: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Designated team lead
    team_lead_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    # Team status
    status: Mapped[TeamStatus] = mapped_column(
        Enum(TeamStatus, name="team_status"),
        nullable=False,
        default=TeamStatus.ACTIVE,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
