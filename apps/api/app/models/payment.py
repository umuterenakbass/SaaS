from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.flat import Flat


class PaymentMethod(enum.StrEnum):
    cash = "cash"
    bank_transfer = "bank_transfer"
    credit_card = "credit_card"
    other = "other"


class Payment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False)
    flat_id: Mapped[str] = mapped_column(ForeignKey("flats.id", ondelete="RESTRICT"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=False,
        default=PaymentMethod.bank_transfer,
    )
    reference_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    flat: Mapped[Flat] = relationship(back_populates="payments")
