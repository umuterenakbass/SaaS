from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.charge import Charge
    from app.models.flat import Flat


class InstallmentStatus(enum.StrEnum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


class InstallmentPlan(Base, TimestampMixin, SoftDeleteMixin):
    """Bir borca bağlı taksit planı."""

    __tablename__ = "installment_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    flat_id: Mapped[str] = mapped_column(ForeignKey("flats.id", ondelete="RESTRICT"), nullable=False)
    charge_id: Mapped[str | None] = mapped_column(
        ForeignKey("charges.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    installment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    flat: Mapped[Flat] = relationship()
    items: Mapped[list[InstallmentItem]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class InstallmentItem(Base, TimestampMixin, SoftDeleteMixin):
    """Taksit planına ait tek bir taksit kalemi."""

    __tablename__ = "installment_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("installment_plans.id", ondelete="CASCADE"), nullable=False
    )
    installment_no: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3...
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InstallmentStatus] = mapped_column(
        Enum(InstallmentStatus, name="installment_status"),
        nullable=False,
        default=InstallmentStatus.pending,
    )
    paid_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    plan: Mapped[InstallmentPlan] = relationship(back_populates="items")
