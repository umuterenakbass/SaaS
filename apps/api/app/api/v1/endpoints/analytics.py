from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.block import Block
from app.models.charge import Charge, ChargeStatus
from app.models.flat import Flat, FlatStatus
from app.models.payment import Payment
from app.models.resident_flat_relation import ResidentFlatRelation
from app.models.user import User, UserRole
from app.schemas.analytics import (
    ActionItem,
    AnalyticsDashboardResponse,
    ChargeTypeBreakdownItem,
    FlatOccupancyStats,
    MonthlyTrendItem,
    OverdueChargeItem,
    TodayActionsResponse,
    TopDebtorItem,
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
                extract("year", Payment.paid_at) == int(period[:4]),
                extract("month", Payment.paid_at) == int(period[5:]),
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

    # En az bir aktif sakin ilişkisi olan daire (end_date null veya gelecekte/bugün)
    today = date.today()
    occupied_flat_ids = (
        db.query(ResidentFlatRelation.flat_id)
        .filter(
            ResidentFlatRelation.site_id == site_id,
            ResidentFlatRelation.deleted_at.is_(None),
            (
                ResidentFlatRelation.end_date.is_(None)
                | (ResidentFlatRelation.end_date >= today)
            ),
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


# ---------------------------------------------------------------------------
# Yeni: Vadesi geçmiş borçlar listesi
# ---------------------------------------------------------------------------

@router.get("/overdue-charges", response_model=list[OverdueChargeItem])
def overdue_charges(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MGMT),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[OverdueChargeItem]:
    today = date.today()
    rows = (
        db.query(Charge)
        .filter(
            Charge.site_id == current_user.site_id,
            Charge.status == ChargeStatus.pending,
            Charge.due_date < today,
            Charge.deleted_at.is_(None),
        )
        .order_by(Charge.due_date.asc())
        .limit(limit)
        .all()
    )
    block_map = {
        b.id: b.name
        for b in db.query(Block).filter(
            Block.site_id == current_user.site_id,
            Block.deleted_at.is_(None),
        ).all()
    }
    result = []
    for c in rows:
        flat = db.query(Flat).filter(Flat.id == c.flat_id).first()
        block_name = block_map.get(flat.block_id, "-") if flat else "-"
        days_overdue = (today - c.due_date).days
        result.append(OverdueChargeItem(
            charge_id=c.id,
            flat_id=c.flat_id,
            unit_no=flat.unit_no if flat else "-",
            block_name=block_name,
            charge_type=c.charge_type,
            period=c.period,
            amount=c.amount,
            due_date=c.due_date.isoformat(),
            days_overdue=days_overdue,
        ))
    return result


# ---------------------------------------------------------------------------
# Yeni: En çok borçlu daireler
# ---------------------------------------------------------------------------

@router.get("/top-debtors", response_model=list[TopDebtorItem])
def top_debtors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MGMT),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[TopDebtorItem]:
    site_id = current_user.site_id

    flats = db.query(Flat).filter(
        Flat.site_id == site_id, Flat.deleted_at.is_(None)
    ).all()

    block_map = {
        b.id: b.name
        for b in db.query(Block).filter(
            Block.site_id == site_id, Block.deleted_at.is_(None)
        ).all()
    }

    items = []
    for flat in flats:
        total_charges = db.query(func.coalesce(func.sum(Charge.amount), 0)).filter(
            Charge.flat_id == flat.id,
            Charge.site_id == site_id,
            Charge.status != ChargeStatus.cancelled,
            Charge.deleted_at.is_(None),
        ).scalar()

        total_payments = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.flat_id == flat.id,
            Payment.site_id == site_id,
            Payment.deleted_at.is_(None),
        ).scalar()

        balance = Decimal(str(total_charges)) - Decimal(str(total_payments))
        if balance <= 0:
            continue

        pending_count = db.query(Charge).filter(
            Charge.flat_id == flat.id,
            Charge.site_id == site_id,
            Charge.status == ChargeStatus.pending,
            Charge.deleted_at.is_(None),
        ).count()

        items.append(TopDebtorItem(
            flat_id=flat.id,
            unit_no=flat.unit_no,
            block_name=block_map.get(flat.block_id, "-"),
            total_debt=balance,
            pending_charge_count=pending_count,
        ))

    items.sort(key=lambda x: x.total_debt, reverse=True)
    return items[:limit]


# ---------------------------------------------------------------------------
# GET /analytics/today-actions  — "Bugün ne yapmalıyım?" dashboard
# ---------------------------------------------------------------------------

@router.get(
    "/today-actions",
    response_model=TodayActionsResponse,
    summary="Bugünkü aksiyon listesi",
    description="Vadesi geçmiş borçlar, bu hafta vadesi dolacaklar ve bugün yapılan ödemeler.",
)
def today_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MGMT),
) -> TodayActionsResponse:
    site_id = current_user.site_id
    today = date.today()
    week_end = date(today.year, today.month, today.day)
    from datetime import timedelta
    week_later = today + timedelta(days=7)

    # Blok haritası
    blocks = db.query(Block).filter(Block.site_id == site_id, Block.deleted_at.is_(None)).all()
    block_map = {b.id: b.name for b in blocks}

    # Daire haritası
    flats = db.query(Flat).filter(Flat.site_id == site_id, Flat.deleted_at.is_(None)).all()
    flat_map = {f.id: f for f in flats}

    # --- Vadesi geçmiş borçlar ---
    overdue_charges = (
        db.query(Charge)
        .filter(
            Charge.site_id == site_id,
            Charge.status == ChargeStatus.pending,
            Charge.due_date < today,
            Charge.deleted_at.is_(None),
        )
        .order_by(Charge.due_date.asc())
        .all()
    )
    overdue_items = []
    overdue_total = Decimal("0")
    for c in overdue_charges:
        flat = flat_map.get(c.flat_id)
        if not flat:
            continue
        days = (today - c.due_date).days
        overdue_items.append(ActionItem(
            flat_id=flat.id,
            unit_no=flat.unit_no,
            block_name=block_map.get(flat.block_id, "-"),
            description=f"{c.charge_type} — {c.period}",
            amount=c.amount,
            due_date=c.due_date.isoformat(),
            days_overdue=days,
        ))
        overdue_total += c.amount

    # --- Bu hafta vadesi dolacak ---
    week_charges = (
        db.query(Charge)
        .filter(
            Charge.site_id == site_id,
            Charge.status == ChargeStatus.pending,
            Charge.due_date >= today,
            Charge.due_date <= week_later,
            Charge.deleted_at.is_(None),
        )
        .order_by(Charge.due_date.asc())
        .all()
    )
    due_week_items = []
    due_week_total = Decimal("0")
    for c in week_charges:
        flat = flat_map.get(c.flat_id)
        if not flat:
            continue
        due_week_items.append(ActionItem(
            flat_id=flat.id,
            unit_no=flat.unit_no,
            block_name=block_map.get(flat.block_id, "-"),
            description=f"{c.charge_type} — {c.period}",
            amount=c.amount,
            due_date=c.due_date.isoformat(),
        ))
        due_week_total += c.amount

    # --- Bugün yapılan ödemeler ---
    todays_payments = (
        db.query(Payment)
        .filter(
            Payment.site_id == site_id,
            Payment.payment_date == today,
            Payment.deleted_at.is_(None),
        )
        .order_by(Payment.created_at.desc())
        .all()
    )
    paid_items = []
    paid_total = Decimal("0")
    for p in todays_payments:
        flat = flat_map.get(p.flat_id)
        if not flat:
            continue
        paid_items.append(ActionItem(
            flat_id=flat.id,
            unit_no=flat.unit_no,
            block_name=block_map.get(flat.block_id, "-"),
            description=f"Ödeme alındı",
            amount=p.amount,
        ))
        paid_total += p.amount

    # --- Bu ay tahsilat oranı ---
    current_period = f"{today.year:04d}-{today.month:02d}"
    month_charged = db.query(func.coalesce(func.sum(Charge.amount), 0)).filter(
        Charge.site_id == site_id,
        Charge.period == current_period,
        Charge.status != ChargeStatus.cancelled,
        Charge.deleted_at.is_(None),
    ).scalar() or 0

    month_paid = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.site_id == site_id,
        extract("year", Payment.payment_date) == today.year,
        extract("month", Payment.payment_date) == today.month,
        Payment.deleted_at.is_(None),
    ).scalar() or 0

    if month_charged > 0:
        rate = Decimal(str(month_paid)) / Decimal(str(month_charged)) * 100
        collection_rate = f"{min(rate, Decimal('100')):.2f}"
    else:
        collection_rate = "0.00"

    return TodayActionsResponse(
        overdue_count=len(overdue_items),
        overdue_total=overdue_total,
        due_this_week_count=len(due_week_items),
        due_this_week_total=due_week_total,
        paid_today_count=len(paid_items),
        paid_today_total=paid_total,
        collection_rate_this_month=collection_rate,
        overdue_items=overdue_items,
        due_this_week_items=due_week_items,
        paid_today_items=paid_items,
    )
