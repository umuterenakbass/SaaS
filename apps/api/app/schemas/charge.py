from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.charge import ChargeStatus


class ChargeCreateRequest(BaseModel):
    flat_id: str
    charge_type: str = Field(min_length=1, max_length=50)
    period: str = Field(min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    amount: Decimal = Field(gt=Decimal("0"))
    due_date: date
    status: ChargeStatus = ChargeStatus.pending


class ChargeUpdateRequest(BaseModel):
    charge_type: str | None = Field(default=None, min_length=1, max_length=50)
    period: str | None = Field(default=None, min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    amount: Decimal | None = Field(default=None, gt=Decimal("0"))
    due_date: date | None = None
    status: ChargeStatus | None = None


class ChargeResponse(BaseModel):
    id: str
    site_id: str
    flat_id: str
    charge_type: str
    period: str
    amount: Decimal
    due_date: date
    status: ChargeStatus
