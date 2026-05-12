from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge, ChargeStatus
from app.models.flat import Flat
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.resident_flat_relation import ResidentFlatRelation
from app.models.user import User, UserRole
from app.schemas.resident_portal import (
    MyBalanceSummary,
    MyChargeItem,
    MyFlatInfo,
    MyNotificationItem,
    MyPaymentItem,
)

router = APIRouter(prefix="/me", tags=["resident-portal"])

_RESIDENT_ONLY = require_roles({UserRole.resident})


# ---------------------------------------------------------------------------
# Helper: sakin'in daire ID'lerini getir
# ---------------------------------------------------------------------------

def _get_my_flat_ids(db: Session, user_id: str, site_id: str) -> list[str]:
    relations = (
        db.query(ResidentFlatRelation)
        .filter(
            ResidentFlatRelation.user_id == user_id,
            ResidentFlatRelation.site_id == site_id,
            ResidentFlatRelation.deleted_at.is_(None),
        )
        .all()
    )
    return [r.flat_id for r in relations]


# ---------------------------------------------------------------------------
# GET /me/flats
# ---------------------------------------------------------------------------

@router.get("/flats", response_model=list[MyFlatInfo])
def my_flats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_RESIDENT_ONLY),
) -> list[MyFlatInfo]:
    relations = (
        db.query(ResidentFlatRelation)
        .filter(
            ResidentFlatRelation.user_id == current_user.id,
            ResidentFlatRelation.site_id == current_user.site_id,
            ResidentFlatRelation.deleted_at.is_(None),
        )
        .all()
    )

    result = []
    for rel in relations:
        flat = db.query(Flat).filter(Flat.id == rel.flat_id, Flat.deleted_at.is_(None)).first()
        if not flat:
            continue
        result.append(
            MyFlatInfo(
                flat_id=flat.id,
                unit_no=flat.unit_no,
                block_name=flat.block.name if flat.block else "",
                floor=flat.floor,
                relation_type=rel.relation_type,
                move_in_date=rel.start_date.isoformat() if rel.start_date else None,
                move_out_date=rel.end_date.isoformat() if rel.end_date else None,
            )
        )
    return result


# ---------------------------------------------------------------------------
# GET /me/charges
# ---------------------------------------------------------------------------

@router.get("/charges", response_model=list[MyChargeItem])
def my_charges(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_RESIDENT_ONLY),
    period: str | None = Query(default=None),
    charge_status: str | None = Query(default=None, alias="status"),
) -> list[MyChargeItem]:
    flat_ids = _get_my_flat_ids(db, current_user.id, current_user.site_id)
    if not flat_ids:
        return []

    query = db.query(Charge).filter(
        Charge.flat_id.in_(flat_ids),
        Charge.site_id == current_user.site_id,
        Charge.deleted_at.is_(None),
    )
    if period:
        query = query.filter(Charge.period == period)
    if charge_status:
        query = query.filter(Charge.status == charge_status)

    charges = query.order_by(Charge.due_date.desc()).all()

    result = []
    for c in charges:
        flat = db.query(Flat).filter(Flat.id == c.flat_id).first()
        result.append(
            MyChargeItem(
                id=c.id,
                flat_id=c.flat_id,
                unit_no=flat.unit_no if flat else "",
                block_name=flat.block.name if flat and flat.block else "",
                charge_type=c.charge_type,
                period=c.period,
                amount=c.amount,
                due_date=c.due_date.isoformat(),
                status=c.status,
            )
        )
    return result


# ---------------------------------------------------------------------------
# GET /me/payments
# ---------------------------------------------------------------------------

@router.get("/payments", response_model=list[MyPaymentItem])
def my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_RESIDENT_ONLY),
) -> list[MyPaymentItem]:
    flat_ids = _get_my_flat_ids(db, current_user.id, current_user.site_id)
    if not flat_ids:
        return []

    payments = (
        db.query(Payment)
        .filter(
            Payment.flat_id.in_(flat_ids),
            Payment.site_id == current_user.site_id,
            Payment.deleted_at.is_(None),
        )
        .order_by(Payment.paid_at.desc())
        .all()
    )

    result = []
    for p in payments:
        flat = db.query(Flat).filter(Flat.id == p.flat_id).first()
        result.append(
            MyPaymentItem(
                id=p.id,
                flat_id=p.flat_id,
                unit_no=flat.unit_no if flat else "",
                block_name=flat.block.name if flat and flat.block else "",
                amount=p.amount,
                paid_at=p.paid_at.isoformat(),
                method=p.method,
                reference_no=p.reference_no,
                note=p.note,
            )
        )
    return result


# ---------------------------------------------------------------------------
# GET /me/balance
# ---------------------------------------------------------------------------

@router.get("/balance", response_model=MyBalanceSummary)
def my_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_RESIDENT_ONLY),
) -> MyBalanceSummary:
    flat_ids = _get_my_flat_ids(db, current_user.id, current_user.site_id)
    if not flat_ids:
        return MyBalanceSummary(
            total_charges=Decimal("0"),
            total_payments=Decimal("0"),
            balance=Decimal("0"),
            pending_count=0,
            overdue_count=0,
        )

    charges = (
        db.query(Charge)
        .filter(
            Charge.flat_id.in_(flat_ids),
            Charge.site_id == current_user.site_id,
            Charge.deleted_at.is_(None),
            Charge.status != ChargeStatus.cancelled,
        )
        .all()
    )
    payments = (
        db.query(Payment)
        .filter(
            Payment.flat_id.in_(flat_ids),
            Payment.site_id == current_user.site_id,
            Payment.deleted_at.is_(None),
        )
        .all()
    )

    total_charges = sum((c.amount for c in charges), Decimal("0"))
    total_payments = sum((p.amount for p in payments), Decimal("0"))
    today = date.today()

    pending_count = sum(1 for c in charges if c.status == ChargeStatus.pending)
    overdue_count = sum(
        1 for c in charges
        if c.status == ChargeStatus.pending and c.due_date < today
    )

    return MyBalanceSummary(
        total_charges=total_charges,
        total_payments=total_payments,
        balance=total_charges - total_payments,
        pending_count=pending_count,
        overdue_count=overdue_count,
    )


# ---------------------------------------------------------------------------
# GET /me/notifications
# ---------------------------------------------------------------------------

@router.get("/notifications", response_model=list[MyNotificationItem])
def my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_RESIDENT_ONLY),
    unread_only: bool = Query(default=False),
) -> list[MyNotificationItem]:
    query = db.query(Notification).filter(
        Notification.site_id == current_user.site_id,
        Notification.user_id == current_user.id,
        Notification.deleted_at.is_(None),
    )
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    notifications = query.order_by(Notification.created_at.desc()).all()

    return [
        MyNotificationItem(
            id=n.id,
            notification_type=n.notification_type,
            title=n.title,
            body=n.body,
            is_read=n.is_read,
            created_at=n.created_at.isoformat(),
        )
        for n in notifications
    ]
