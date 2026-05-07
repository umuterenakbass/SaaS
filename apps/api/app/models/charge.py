from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.flat import Flat


class ChargeStatus(enum.StrEnum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class Charge(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "charges"
    __table_args__ = (
        Index(
            "uq_charges_flat_period_type_active",
            "flat_id",
            "period",
            "charge_type",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    flat_id: Mapped[str] = mapped_column(ForeignKey("flats.id", ondelete="RESTRICT"), nullable=False)
    charge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ChargeStatus] = mapped_column(
        Enum(ChargeStatus, name="charge_status"),
        nullable=False,
        default=ChargeStatus.pending,
    )

    flat: Mapped[Flat] = relationship(back_populates="charges")
