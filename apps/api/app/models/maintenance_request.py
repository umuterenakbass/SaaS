from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class MaintenanceCategory(enum.StrEnum):
    electrical = "electrical"
    plumbing = "plumbing"
    elevator = "elevator"
    common_area = "common_area"
    heating = "heating"
    other = "other"


class MaintenanceStatus(enum.StrEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    cancelled = "cancelled"


class MaintenanceRequest(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "maintenance_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(
        ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    flat_id: Mapped[str | None] = mapped_column(
        ForeignKey("flats.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reported_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    category: Mapped[MaintenanceCategory] = mapped_column(
        Enum(MaintenanceCategory, name="maintenance_category"),
        nullable=False,
        default=MaintenanceCategory.other,
    )
    status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus, name="maintenance_status"),
        nullable=False,
        default=MaintenanceStatus.open,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Admin notu
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
