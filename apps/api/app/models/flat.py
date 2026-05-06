from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.block import Block
    from app.models.resident_flat_relation import ResidentFlatRelation


class FlatStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"


class Flat(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "flats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id: Mapped[str] = mapped_column(
        ForeignKey("sites.id", ondelete="RESTRICT"),
        nullable=False,
    )
    block_id: Mapped[str] = mapped_column(
        ForeignKey("blocks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    unit_no: Mapped[str] = mapped_column(String(50), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[FlatStatus] = mapped_column(
        Enum(FlatStatus, name="flat_status"),
        nullable=False,
        default=FlatStatus.active,
    )

    block: Mapped[Block] = relationship(back_populates="flats")
    resident_relations: Mapped[list[ResidentFlatRelation]] = relationship(back_populates="flat")
