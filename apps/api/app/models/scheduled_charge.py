from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class ScheduledCharge(Base, TimestampMixin, SoftDeleteMixin):
    """Site yöneticisinin tanımladığı tekrarlayan borç kuralı.

    Her ay ``day_of_month`` tarihinde bu sitedeki tüm aktif dairelere
    ``charge_type`` tipinde ``amount`` tutarında borç üretmek için kullanılır.
    Üretme işlemi otomatik (cron) veya manuel tetikle yapılır.
    """

    __tablename__ = "scheduled_charges"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False
    )
    charge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-28
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
