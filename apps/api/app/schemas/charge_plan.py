from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field

from app.models.charge import ChargeStatus
from app.models.charge_plan import ChargePlanFrequency


class ChargePlanCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    charge_type: str = Field(min_length=1, max_length=50)
    amount: Decimal = Field(gt=Decimal("0"))
    frequency: ChargePlanFrequency = ChargePlanFrequency.monthly
    start_period: str = Field(min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    end_period: str | None = Field(default=None, min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    is_active: bool = True


class ChargePlanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    charge_type: str | None = Field(default=None, min_length=1, max_length=50)
    amount: Decimal | None = Field(default=None, gt=Decimal("0"))
    frequency: ChargePlanFrequency | None = None
    start_period: str | None = Field(default=None, min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    end_period: str | None = Field(default=None, min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    is_active: bool | None = None


class ChargePlanResponse(BaseModel):
    id: str
    site_id: str
    name: str
    charge_type: str
    amount: Decimal
    frequency: ChargePlanFrequency
    start_period: str
    end_period: str | None
    is_active: bool


class ChargePlanAssignmentCreateRequest(BaseModel):
    flat_id: str


class ChargePlanAssignmentResponse(BaseModel):
    id: str
    site_id: str
    charge_plan_id: str
    flat_id: str


class ChargePlanGenerateRequest(BaseModel):
    period: str = Field(min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    due_date: date
    status: ChargeStatus = ChargeStatus.pending


class ChargePlanGenerateResponse(BaseModel):
    charge_plan_id: str
    period: str
    requested_assignments: int
    created_count: int
    skipped_count: int
    created_charge_ids: list[str]
