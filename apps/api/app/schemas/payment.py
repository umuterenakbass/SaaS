from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.payment import PaymentMethod


class PaymentCreateRequest(BaseModel):
    flat_id: str
    amount: Decimal = Field(gt=Decimal("0"))
    paid_at: datetime
    method: PaymentMethod = PaymentMethod.bank_transfer
    reference_no: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=500)


class PaymentUpdateRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=Decimal("0"))
    paid_at: datetime | None = None
    method: PaymentMethod | None = None
    reference_no: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=500)


class PaymentResponse(BaseModel):
    id: str
    site_id: str
    flat_id: str
    amount: Decimal
    paid_at: datetime
    method: PaymentMethod
    reference_no: str | None
    note: str | None
