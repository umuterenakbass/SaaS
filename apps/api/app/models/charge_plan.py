from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.flat import Flat


class ChargePlanFrequency(enum.StrEnum):
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


class ChargePlan(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "charge_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    charge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    frequency: Mapped[ChargePlanFrequency] = mapped_column(
        Enum(ChargePlanFrequency, name="charge_plan_frequency"),
        nullable=False,
        default=ChargePlanFrequency.monthly,
    )
    start_period: Mapped[str] = mapped_column(String(7), nullable=False)
    end_period: Mapped[str | None] = mapped_column(String(7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    assignments: Mapped[list[ChargePlanAssignment]] = relationship(back_populates="charge_plan")


class ChargePlanAssignment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "charge_plan_assignments"
    __table_args__ = (
        Index(
            "uq_charge_plan_assignments_plan_flat_active",
            "charge_plan_id",
            "flat_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    charge_plan_id: Mapped[str] = mapped_column(
        ForeignKey("charge_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    flat_id: Mapped[str] = mapped_column(ForeignKey("flats.id", ondelete="RESTRICT"), nullable=False)

    charge_plan: Mapped[ChargePlan] = relationship(back_populates="assignments")
    flat: Mapped[Flat] = relationship(back_populates="charge_plan_assignments")
