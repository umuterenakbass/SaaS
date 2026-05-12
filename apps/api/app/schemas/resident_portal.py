from decimal import Decimal

from pydantic import BaseModel


class MyFlatInfo(BaseModel):
    flat_id: str
    unit_no: str
    block_name: str
    floor: int
    relation_type: str  # owner | tenant
    move_in_date: str | None
    move_out_date: str | None


class MyChargeItem(BaseModel):
    id: str
    flat_id: str
    unit_no: str
    block_name: str
    charge_type: str
    period: str
    amount: Decimal
    due_date: str
    status: str


class MyPaymentItem(BaseModel):
    id: str
    flat_id: str
    unit_no: str
    block_name: str
    amount: Decimal
    paid_at: str
    method: str
    reference_no: str | None
    note: str | None


class MyBalanceSummary(BaseModel):
    total_charges: Decimal
    total_payments: Decimal
    balance: Decimal          # pozitif → borçlu, negatif → alacaklı
    pending_count: int        # bekleyen borç sayısı
    overdue_count: int        # vadesi geçmiş borç sayısı


class MyNotificationItem(BaseModel):
    id: str
    notification_type: str
    title: str
    body: str
    is_read: bool
    created_at: str
