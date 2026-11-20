from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmploymentType(PyEnum):
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"


class EmployeeStatus(PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Employee(Base):
    __tablename__ = "employees"

    __table_args__ = (
        CheckConstraint(
            "working_time_share > 0 AND working_time_share <= 1",
            name="ck_employees_working_time_share_range",
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_employees_valid_employment_dates",
        ),
        CheckConstraint(
            "(employment_type = 'PERMANENT' AND end_date IS NULL) OR "
            "(employment_type = 'CONTRACT' AND end_date IS NOT NULL)",
            name="ck_employees_employment_type_dates",
        ),
    )

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Employee information
    employee_ref: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # Team assignment
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )

    job_title: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Employment details
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="employment_type"),
        nullable=False,
    )

    working_time_share: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Employee status
    status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus, name="employee_status"),
        nullable=False,
        default=EmployeeStatus.ACTIVE,
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

