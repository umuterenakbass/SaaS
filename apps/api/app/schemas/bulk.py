from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.charge import ChargeStatus


# ---------------------------------------------------------------------------
# Bulk charge
# ---------------------------------------------------------------------------

class BulkChargeRequest(BaseModel):
    """Belirtilen dairelere (ya da tüm aktif dairelere) toplu borç oluştur."""

    flat_ids: list[str] | None = Field(
        default=None,
        description="Boş bırakılırsa sitedeki tüm aktif dairelere uygulanır.",
    )
    charge_type: str = Field(min_length=1, max_length=50)
    period: str = Field(min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    amount: Decimal = Field(gt=Decimal("0"))
    due_date: date
    status: ChargeStatus = ChargeStatus.pending


class BulkChargeResult(BaseModel):
    created: int
    skipped: int          # aynı flat+period+type zaten varsa atlandı
    errors: list[str]     # beklenmeyen hatalar (flat bulunamadı vs.)


# ---------------------------------------------------------------------------
# Scheduled charge (tekrarlayan kural)
# ---------------------------------------------------------------------------

class ScheduledChargeCreateRequest(BaseModel):
    charge_type: str = Field(min_length=1, max_length=50)
    amount: Decimal = Field(gt=Decimal("0"))
    day_of_month: int = Field(ge=1, le=28, description="Ayın kaçında vade? (1-28)")
    active: bool = True


class ScheduledChargeUpdateRequest(BaseModel):
    charge_type: str | None = Field(default=None, min_length=1, max_length=50)
    amount: Decimal | None = Field(default=None, gt=Decimal("0"))
    day_of_month: int | None = Field(default=None, ge=1, le=28)
    active: bool | None = None


class ScheduledChargeResponse(BaseModel):
    id: str
    site_id: str
    charge_type: str
    amount: Decimal
    day_of_month: int
    active: bool
    created_at: str
    updated_at: str


class ScheduledChargeRunResult(BaseModel):
    period: str            # hangi dönem için çalıştırıldı (YYYY-MM)
    created: int
    skipped: int
    errors: list[str]
