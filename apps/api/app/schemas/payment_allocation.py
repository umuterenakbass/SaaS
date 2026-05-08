from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentAllocationCreateRequest(BaseModel):
    payment_id: str
    charge_id: str
    allocated_amount: Decimal = Field(gt=Decimal("0"))


class PaymentAllocationResponse(BaseModel):
    id: str
    site_id: str
    payment_id: str
    charge_id: str
    allocated_amount: Decimal
