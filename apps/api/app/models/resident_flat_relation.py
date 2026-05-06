from __future__ import annotations

import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.flat import Flat
    from app.models.user import User


class ResidentRelationType(enum.StrEnum):
    owner = "owner"
    tenant = "tenant"


class ResidentFlatRelation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "resident_flat_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(
        ForeignKey("sites.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    flat_id: Mapped[str] = mapped_column(
        ForeignKey("flats.id", ondelete="RESTRICT"),
        nullable=False,
    )
    relation_type: Mapped[ResidentRelationType] = mapped_column(
        Enum(ResidentRelationType, name="resident_relation_type"),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    flat: Mapped[Flat] = relationship(back_populates="resident_relations")
    user: Mapped[User] = relationship()
