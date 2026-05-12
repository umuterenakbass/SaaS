from decimal import Decimal

from pydantic import BaseModel


# ---------- Period Summary ----------

class PeriodChargeSummary(BaseModel):
    charge_type: str
    charge_count: int
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    cancelled_amount: Decimal


class PeriodSummaryResponse(BaseModel):
    site_id: str
    period: str
    total_charges: Decimal
    total_payments: Decimal
    total_allocated: Decimal
    collection_rate: Decimal          # tahsilat oranı (0-100)
    charge_count: int
    payment_count: int
    by_charge_type: list[PeriodChargeSummary]


# ---------- Flat Summary ----------

class FlatSummaryItem(BaseModel):
    flat_id: str
    unit_no: str
    block_name: str
    total_charges: Decimal
    total_payments: Decimal
    balance: Decimal                  # borç - ödeme (pozitif = borçlu)
    pending_charge_count: int
    overdue_charge_count: int


class FlatSummaryResponse(BaseModel):
    site_id: str
    period: str | None               # None ise tüm zamanlar
    flat_count: int
    items: list[FlatSummaryItem]
