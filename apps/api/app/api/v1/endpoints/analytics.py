from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge, ChargeStatus
from app.models.flat import Flat, FlatStatus
from app.models.payment import Payment
from app.models.resident_flat_relation import ResidentFlatRelation
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    ChargeTypeBreakdownItem,
    FlatOccupancyStats,
    MonthlyTrendItem,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

_MGMT = require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _last_n_periods(n: int = 12) -> list[str]:
    """Şu andan geriye doğru n ay, YYYY-MM formatında liste döndürür."""
    now = datetime.now(UTC)
    periods = []
    year, month = now.year, now.month
    for _ in range(n):
        periods.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(periods))


def _monthly_trend(db: Session, site_id: str, periods: list[str]) -> list[MonthlyTrendItem]:
    items = []
    for period in periods:
        charges = (
            db.query(func.coalesce(func.sum(Charge.amount), 0))
            .filter(
                Charge.site_id == site_id,
                Charge.period == period,
                Charge.deleted_at.is_(None),
                Charge.status != ChargeStatus.cancelled,
            )
            .scalar()
        )
        payments = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(
                Payment.site_id == site_id,
                Payment.deleted_at.is_(None),
                func.strftime("%Y-%m", Payment.paid_at) == period,
            )
            .scalar()
        )
        total_c = Decimal(str(charges))
        total_p = Decimal(str(payments))
        rate = (total_p / total_c * 100).quantize(Decimal("0.01")) if total_c > 0 else Decimal("0.00")
        items.append(
            MonthlyTrendItem(
                period=period,
                total_charges=total_c,
                total_payments=total_p,
                collection_rate=str(rate),
            )
        )
    return items


def _occupancy(db: Session, site_id: str) -> FlatOccupancyStats:
    total = db.query(Flat).filter(
        Flat.site_id == site_id, Flat.deleted_at.is_(None)
    ).count()

    active = db.query(Flat).filter(
        Flat.site_id == site_id,
        Flat.deleted_at.is_(None),
        Flat.status == FlatStatus.active,
    ).count()

    # En az bir aktif sakin ilişkisi olan daire (move_out_date null veya gelecekte)
    occupied_flat_ids = (
        db.query(ResidentFlatRelation.flat_id)
        .filter(
            ResidentFlatRelation.site_id == site_id,
            ResidentFlatRelation.deleted_at.is_(None),
            ResidentFlatRelation.move_out_date.is_(None),
        )
        .distinct()
        .subquery()
    )
    occupied = db.query(Flat).filter(
        Flat.site_id == site_id,
        Flat.deleted_at.is_(None),
        Flat.status == FlatStatus.active,
        Flat.id.in_(occupied_flat_ids),
    ).count()

    return FlatOccupancyStats(
        total_flats=total,
        active_flats=active,
        occupied_flats=occupied,
        vacant_flats=max(active - occupied, 0),
    )


def _charge_type_breakdown(db: Session, site_id: str) -> list[ChargeTypeBreakdownItem]:
    rows = (
        db.query(
            Charge.charge_type,
            func.sum(Charge.amount).label("total_amount"),
            func.count(Charge.id).label("charge_count"),
        )
        .filter(
            Charge.site_id == site_id,
            Charge.deleted_at.is_(None),
            Charge.status != ChargeStatus.cancelled,
        )
        .group_by(Charge.charge_type)
        .order_by(func.sum(Charge.amount).desc())
        .all()
    )
    return [
        ChargeTypeBreakdownItem(
            charge_type=row.charge_type,
            total_amount=Decimal(str(row.total_amount or 0)),
            charge_count=row.charge_count,
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
def analytics_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MGMT),
    months: int = Query(default=12, ge=1, le=24),
) -> AnalyticsDashboardResponse:
    """Son N ayın trend verisi + daire doluluk + tipe göre borç dağılımı."""
    periods = _last_n_periods(months)
    trend = _monthly_trend(db, current_user.site_id, periods)
    occupancy = _occupancy(db, current_user.site_id)
    breakdown = _charge_type_breakdown(db, current_user.site_id)

    # Ortalama tahsilat oranı (sadece borç olan aylar)
    rates = [Decimal(t.collection_rate) for t in trend if Decimal(t.total_charges) > 0]
    avg_rate = (sum(rates) / len(rates)).quantize(Decimal("0.01")) if rates else Decimal("0.00")

    return AnalyticsDashboardResponse(
        monthly_trend=trend,
        occupancy=occupancy,
        charge_type_breakdown=breakdown,
        avg_collection_rate=str(avg_rate),
    )


@router.get("/monthly-trend", response_model=list[MonthlyTrendItem])
def monthly_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MGMT),
    months: int = Query(default=12, ge=1, le=24),
) -> list[MonthlyTrendItem]:
    return _monthly_trend(db, current_user.site_id, _last_n_periods(months))


@router.get("/flat-occupancy", response_model=FlatOccupancyStats)
def flat_occupancy(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MGMT),
) -> FlatOccupancyStats:
    return _occupancy(db, current_user.site_id)
