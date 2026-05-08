from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.charge import Charge
    from app.models.payment import Payment


class PaymentAllocation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "payment_allocations"
    __table_args__ = (
        Index(
            "uq_payment_allocations_payment_charge_active",
            "payment_id",
            "charge_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    payment_id: Mapped[str] = mapped_column(
        ForeignKey("payments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    charge_id: Mapped[str] = mapped_column(ForeignKey("charges.id", ondelete="RESTRICT"), nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    payment: Mapped[Payment] = relationship(back_populates="allocations")
    charge: Mapped[Charge] = relationship(back_populates="allocations")
