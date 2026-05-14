import csv
import io
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.deps import require_tenant_context
from app.db.session import get_db
from app.models.block import Block
from app.models.charge import Charge, ChargeStatus
from app.models.flat import Flat
from app.models.payment import Payment
from app.models.payment_allocation import PaymentAllocation
from app.models.user import User
from app.schemas.report import (
    FlatSummaryItem,
    FlatSummaryResponse,
    PeriodChargeSummary,
    PeriodSummaryResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _coalesce(value: object) -> Decimal:
    return Decimal(str(value)) if value is not None else Decimal("0")


# ── period summary ────────────────────────────────────────────────────────────

@router.get("/period-summary", response_model=PeriodSummaryResponse)
def period_summary(
    period: str = Query(description="YYYY-MM formatında dönem"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> PeriodSummaryResponse:
    site_id = current_user.site_id

    charges = (
        db.query(Charge)
        .filter(
            Charge.site_id == site_id,
            Charge.period == period,
            Charge.deleted_at.is_(None),
        )
        .all()
    )

    total_charges = sum((c.amount for c in charges), Decimal("0"))
    charge_count = len(charges)

    # Dönem içi ödemeler (paid_at aynı ay)
    year, month = period.split("-")
    payments = (
        db.query(Payment)
        .filter(
            Payment.site_id == site_id,
            extract("year", Payment.paid_at) == int(year),
            extract("month", Payment.paid_at) == int(month),
            Payment.deleted_at.is_(None),
        )
        .all()
    )
    total_payments = sum((p.amount for p in payments), Decimal("0"))
    payment_count = len(payments)

    # Tahsis toplamı (bu dönem borçlarına karşılık)
    charge_ids = [c.id for c in charges]
    if charge_ids:
        allocated_row = (
            db.query(func.coalesce(func.sum(PaymentAllocation.allocated_amount), 0))
            .filter(
                PaymentAllocation.charge_id.in_(charge_ids),
                PaymentAllocation.deleted_at.is_(None),
            )
            .scalar()
        )
        total_allocated = _coalesce(allocated_row)
    else:
        total_allocated = Decimal("0")

    collection_rate = (
        (total_allocated / total_charges * 100).quantize(Decimal("0.01"))
        if total_charges > 0
        else Decimal("0")
    )

    # Tipe göre gruplama
    type_map: dict[str, dict] = {}
    for c in charges:
        ct = c.charge_type
        if ct not in type_map:
            type_map[ct] = {
                "charge_count": 0,
                "total_amount": Decimal("0"),
                "paid_amount": Decimal("0"),
                "pending_amount": Decimal("0"),
                "cancelled_amount": Decimal("0"),
            }
        type_map[ct]["charge_count"] += 1
        type_map[ct]["total_amount"] += c.amount
        if c.status == ChargeStatus.paid:
            type_map[ct]["paid_amount"] += c.amount
        elif c.status == ChargeStatus.pending:
            type_map[ct]["pending_amount"] += c.amount
        else:
            type_map[ct]["cancelled_amount"] += c.amount

    by_charge_type = [
        PeriodChargeSummary(charge_type=ct, **data)
        for ct, data in type_map.items()
    ]

    return PeriodSummaryResponse(
        site_id=site_id,
        period=period,
        total_charges=total_charges,
        total_payments=total_payments,
        total_allocated=total_allocated,
        collection_rate=collection_rate,
        charge_count=charge_count,
        payment_count=payment_count,
        by_charge_type=by_charge_type,
    )


# ── flat summary ──────────────────────────────────────────────────────────────

@router.get("/flat-summary", response_model=FlatSummaryResponse)
def flat_summary(
    period: str | None = Query(default=None, description="YYYY-MM — boş bırakılırsa tüm zamanlar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> FlatSummaryResponse:
    site_id = current_user.site_id
    today = datetime.now(UTC).date()

    flats = (
        db.query(Flat)
        .filter(Flat.site_id == site_id, Flat.deleted_at.is_(None))
        .all()
    )

    block_map = {
        b.id: b.name
        for b in db.query(Block).filter(Block.site_id == site_id, Block.deleted_at.is_(None)).all()
    }

    items: list[FlatSummaryItem] = []
    for flat in flats:
        charge_q = db.query(Charge).filter(
            Charge.flat_id == flat.id,
            Charge.deleted_at.is_(None),
        )
        if period:
            charge_q = charge_q.filter(Charge.period == period)
        flat_charges = charge_q.all()

        payment_q = db.query(Payment).filter(
            Payment.flat_id == flat.id,
            Payment.deleted_at.is_(None),
        )
        if period:
            p_year, p_month = period.split("-")
            payment_q = payment_q.filter(
                extract("year", Payment.paid_at) == int(p_year),
                extract("month", Payment.paid_at) == int(p_month),
            )
        flat_payments = payment_q.all()

        total_charges = sum((c.amount for c in flat_charges), Decimal("0"))
        total_payments = sum((p.amount for p in flat_payments), Decimal("0"))
        balance = total_charges - total_payments

        pending_count = sum(1 for c in flat_charges if c.status == ChargeStatus.pending)
        overdue_count = sum(
            1 for c in flat_charges
            if c.status == ChargeStatus.pending and c.due_date < today
        )

        items.append(
            FlatSummaryItem(
                flat_id=flat.id,
                unit_no=flat.unit_no,
                block_name=block_map.get(flat.block_id, "-"),
                total_charges=total_charges,
                total_payments=total_payments,
                balance=balance,
                pending_charge_count=pending_count,
                overdue_charge_count=overdue_count,
            )
        )

    # Bakiyeye göre azalan sırala (en borçlu üstte)
    items.sort(key=lambda x: x.balance, reverse=True)

    return FlatSummaryResponse(
        site_id=site_id,
        period=period,
        flat_count=len(items),
        items=items,
    )


# ── CSV exports ───────────────────────────────────────────────────────────────

@router.get("/export/charges")
def export_charges_csv(
    period: str | None = Query(default=None),
    flat_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> StreamingResponse:
    site_id = current_user.site_id

    q = db.query(Charge).filter(Charge.site_id == site_id, Charge.deleted_at.is_(None))
    if period:
        q = q.filter(Charge.period == period)
    if flat_id:
        q = q.filter(Charge.flat_id == flat_id)

    charges = q.order_by(Charge.period.desc(), Charge.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "flat_id", "charge_type", "period", "amount", "due_date", "status", "created_at"])
    for c in charges:
        writer.writerow([
            c.id, c.flat_id, c.charge_type, c.period,
            str(c.amount), str(c.due_date), c.status, c.created_at.isoformat(),
        ])

    output.seek(0)
    filename = f"charges_{period or 'all'}_{site_id[:8]}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/payments")
def export_payments_csv(
    period: str | None = Query(default=None, description="YYYY-MM — paid_at ayına göre"),
    flat_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> StreamingResponse:
    site_id = current_user.site_id

    q = db.query(Payment).filter(Payment.site_id == site_id, Payment.deleted_at.is_(None))
    if period:
        exp_year, exp_month = period.split("-")
        q = q.filter(
            extract("year", Payment.paid_at) == int(exp_year),
            extract("month", Payment.paid_at) == int(exp_month),
        )
    if flat_id:
        q = q.filter(Payment.flat_id == flat_id)

    payments = q.order_by(Payment.paid_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "flat_id", "amount", "paid_at", "method", "reference_no", "note", "created_at"])
    for p in payments:
        writer.writerow([
            p.id, p.flat_id, str(p.amount), p.paid_at.isoformat(),
            p.method, p.reference_no or "", p.note or "", p.created_at.isoformat(),
        ])

    output.seek(0)
    filename = f"payments_{period or 'all'}_{site_id[:8]}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
