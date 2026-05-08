from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge, ChargeStatus
from app.models.flat import Flat
from app.models.payment import Payment
from app.models.payment_allocation import PaymentAllocation
from app.models.user import User
from app.schemas.ledger import FlatLedgerResponse, LedgerChargeItem, LedgerPaymentItem

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/flats/{flat_id}", response_model=FlatLedgerResponse)
def get_flat_ledger(
    flat_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> FlatLedgerResponse:
    flat = (
        db.query(Flat)
        .filter(
            Flat.id == flat_id,
            Flat.site_id == current_user.site_id,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found")

    charges = (
        db.query(Charge)
        .filter(
            Charge.flat_id == flat_id,
            Charge.site_id == current_user.site_id,
            Charge.deleted_at.is_(None),
            Charge.status != ChargeStatus.cancelled,
        )
        .order_by(Charge.created_at.desc())
        .all()
    )

    payments = (
        db.query(Payment)
        .filter(
            Payment.flat_id == flat_id,
            Payment.site_id == current_user.site_id,
            Payment.deleted_at.is_(None),
        )
        .order_by(Payment.paid_at.desc(), Payment.created_at.desc())
        .all()
    )

    charge_ids = [item.id for item in charges]
    payment_ids = [item.id for item in payments]

    allocations: list[PaymentAllocation] = []
    if charge_ids and payment_ids:
        allocations = (
            db.query(PaymentAllocation)
            .filter(
                PaymentAllocation.site_id == current_user.site_id,
                PaymentAllocation.deleted_at.is_(None),
                PaymentAllocation.charge_id.in_(charge_ids),
                PaymentAllocation.payment_id.in_(payment_ids),
            )
            .all()
        )

    allocated_by_charge: dict[str, Decimal] = {}
    allocated_by_payment: dict[str, Decimal] = {}
    for item in allocations:
        allocated_by_charge[item.charge_id] = allocated_by_charge.get(item.charge_id, Decimal("0.00")) + item.allocated_amount
        allocated_by_payment[item.payment_id] = allocated_by_payment.get(item.payment_id, Decimal("0.00")) + item.allocated_amount

    total_charges = sum((item.amount for item in charges), Decimal("0.00"))
    total_payments = sum((item.amount for item in payments), Decimal("0.00"))
    allocated_total = sum((item.allocated_amount for item in allocations), Decimal("0.00"))
    open_charge_total = sum(
        (
            max(item.amount - allocated_by_charge.get(item.id, Decimal("0.00")), Decimal("0.00"))
            for item in charges
        ),
        Decimal("0.00"),
    )
    unallocated_payment_total = sum(
        (
            max(item.amount - allocated_by_payment.get(item.id, Decimal("0.00")), Decimal("0.00"))
            for item in payments
        ),
        Decimal("0.00"),
    )

    return FlatLedgerResponse(
        site_id=current_user.site_id,
        flat_id=flat_id,
        total_charges=total_charges,
        total_payments=total_payments,
        allocated_total=allocated_total,
        open_charge_total=open_charge_total,
        unallocated_payment_total=unallocated_payment_total,
        balance=total_charges - total_payments,
        charge_count=len(charges),
        payment_count=len(payments),
        recent_charges=[
            LedgerChargeItem(
                charge_id=item.id,
                charge_type=item.charge_type,
                period=item.period,
                amount=item.amount,
                allocated_amount=allocated_by_charge.get(item.id, Decimal("0.00")),
                remaining_amount=max(
                    item.amount - allocated_by_charge.get(item.id, Decimal("0.00")),
                    Decimal("0.00"),
                ),
                due_date=item.due_date,
                status=item.status,
            )
            for item in charges[:limit]
        ],
        recent_payments=[
            LedgerPaymentItem(
                payment_id=item.id,
                amount=item.amount,
                allocated_amount=allocated_by_payment.get(item.id, Decimal("0.00")),
                remaining_amount=max(
                    item.amount - allocated_by_payment.get(item.id, Decimal("0.00")),
                    Decimal("0.00"),
                ),
                paid_at=item.paid_at,
                method=item.method,
                reference_no=item.reference_no,
            )
            for item in payments[:limit]
        ],
    )
