from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Item ─────────────────────────────────────────────────────────────────────

class InstallmentItemOut(BaseModel):
    id: str
    installment_no: int
    amount: Decimal
    due_date: str
    status: str
    paid_at: str | None


# ── Plan ─────────────────────────────────────────────────────────────────────

class InstallmentPlanCreate(BaseModel):
    flat_id: str
    charge_id: str | None = None
    title: str
    total_amount: Decimal = Field(gt=0)
    installment_count: int = Field(ge=2, le=60)
    first_due_date: date   # ilk taksit vadesi; diğerleri +1ay, +2ay...


class InstallmentPlanOut(BaseModel):
    id: str
    site_id: str
    flat_id: str
    charge_id: str | None
    title: str
    total_amount: Decimal
    installment_count: int
    is_active: bool
    items: list[InstallmentItemOut]


class InstallmentItemPayOut(BaseModel):
    id: str
    installment_no: int
    amount: Decimal
    due_date: str
    status: str
    paid_at: str
