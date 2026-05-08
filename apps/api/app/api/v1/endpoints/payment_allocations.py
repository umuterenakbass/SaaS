from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge
from app.models.payment import Payment
from app.models.payment_allocation import PaymentAllocation
from app.models.user import User, UserRole
from app.schemas.payment_allocation import PaymentAllocationCreateRequest, PaymentAllocationResponse

router = APIRouter(prefix="/payment-allocations", tags=["payment-allocations"])


def _sum_allocations_for_payment(db: Session, payment_id: str) -> Decimal:
    value = (
        db.query(func.coalesce(func.sum(PaymentAllocation.allocated_amount), 0))
        .filter(PaymentAllocation.payment_id == payment_id, PaymentAllocation.deleted_at.is_(None))
        .scalar()
    )
    return Decimal(str(value))


def _sum_allocations_for_charge(db: Session, charge_id: str) -> Decimal:
    value = (
        db.query(func.coalesce(func.sum(PaymentAllocation.allocated_amount), 0))
        .filter(PaymentAllocation.charge_id == charge_id, PaymentAllocation.deleted_at.is_(None))
        .scalar()
    )
    return Decimal(str(value))


@router.get("", response_model=list[PaymentAllocationResponse])
def list_payment_allocations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    payment_id: str | None = Query(default=None),
    charge_id: str | None = Query(default=None),
) -> list[PaymentAllocationResponse]:
    query = db.query(PaymentAllocation).filter(
        PaymentAllocation.site_id == current_user.site_id,
        PaymentAllocation.deleted_at.is_(None),
    )
    if payment_id:
        query = query.filter(PaymentAllocation.payment_id == payment_id)
    if charge_id:
        query = query.filter(PaymentAllocation.charge_id == charge_id)

    items = query.order_by(PaymentAllocation.created_at.desc()).all()
    return [PaymentAllocationResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("", response_model=PaymentAllocationResponse, status_code=status.HTTP_201_CREATED)
def create_payment_allocation(
    payload: PaymentAllocationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> PaymentAllocationResponse:
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payload.payment_id,
            Payment.site_id == current_user.site_id,
            Payment.deleted_at.is_(None),
        )
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    charge = (
        db.query(Charge)
        .filter(
            Charge.id == payload.charge_id,
            Charge.site_id == current_user.site_id,
            Charge.deleted_at.is_(None),
        )
        .first()
    )
    if not charge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")

    if payment.flat_id != charge.flat_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment and charge must belong to the same flat",
        )

    payment_allocated = _sum_allocations_for_payment(db, payment.id)
    if payment_allocated + payload.allocated_amount > payment.amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Allocation exceeds payment amount",
        )

    charge_allocated = _sum_allocations_for_charge(db, charge.id)
    if charge_allocated + payload.allocated_amount > charge.amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Allocation exceeds charge amount",
        )

    allocation = PaymentAllocation(
        site_id=current_user.site_id,
        payment_id=payload.payment_id,
        charge_id=payload.charge_id,
        allocated_amount=payload.allocated_amount,
    )
    db.add(allocation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Allocation already exists for this payment and charge",
        ) from None

    db.refresh(allocation)
    return PaymentAllocationResponse.model_validate(allocation, from_attributes=True)


@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_allocation(
    allocation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> None:
    allocation = (
        db.query(PaymentAllocation)
        .filter(
            PaymentAllocation.id == allocation_id,
            PaymentAllocation.site_id == current_user.site_id,
            PaymentAllocation.deleted_at.is_(None),
        )
        .first()
    )
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")

    allocation.deleted_at = datetime.now(UTC)
    db.commit()
