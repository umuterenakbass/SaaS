from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.charge import ChargeStatus
from app.models.payment import PaymentMethod


class LedgerChargeItem(BaseModel):
    charge_id: str
    charge_type: str
    period: str
    amount: Decimal
    due_date: date
    status: ChargeStatus


class LedgerPaymentItem(BaseModel):
    payment_id: str
    amount: Decimal
    paid_at: datetime
    method: PaymentMethod
    reference_no: str | None


class FlatLedgerResponse(BaseModel):
    site_id: str
    flat_id: str
    total_charges: Decimal
    total_payments: Decimal
    balance: Decimal
    charge_count: int
    payment_count: int
    recent_charges: list[LedgerChargeItem]
    recent_payments: list[LedgerPaymentItem]
