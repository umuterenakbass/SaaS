from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.flat import Flat
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreateRequest, PaymentResponse, PaymentUpdateRequest
from app.services import notification_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentResponse])
def list_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    flat_id: str | None = Query(default=None),
) -> list[PaymentResponse]:
    query = db.query(Payment).filter(Payment.site_id == current_user.site_id, Payment.deleted_at.is_(None))
    if flat_id:
        query = query.filter(Payment.flat_id == flat_id)

    payments = query.order_by(Payment.paid_at.desc(), Payment.created_at.desc()).all()
    return [PaymentResponse.model_validate(item, from_attributes=True) for item in payments]


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> PaymentResponse:
    flat = (
        db.query(Flat)
        .filter(
            Flat.id == payload.flat_id,
            Flat.site_id == current_user.site_id,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found")

    payment = Payment(
        site_id=current_user.site_id,
        flat_id=payload.flat_id,
        amount=payload.amount,
        paid_at=payload.paid_at,
        method=payload.method,
        reference_no=payload.reference_no.strip() if payload.reference_no else None,
        note=payload.note.strip() if payload.note else None,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    notification_service.notify_payment_received(
        db,
        site_id=current_user.site_id,
        flat_id=payment.flat_id,
        payment_id=payment.id,
        amount=str(payment.amount),
        method=str(payment.method),
        user_id=current_user.id,
    )
    db.commit()

    return PaymentResponse.model_validate(payment, from_attributes=True)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> PaymentResponse:
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.site_id == current_user.site_id,
            Payment.deleted_at.is_(None),
        )
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    return PaymentResponse.model_validate(payment, from_attributes=True)


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: str,
    payload: PaymentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> PaymentResponse:
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.site_id == current_user.site_id,
            Payment.deleted_at.is_(None),
        )
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(payment, key, value)

    db.commit()
    db.refresh(payment)
    return PaymentResponse.model_validate(payment, from_attributes=True)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> None:
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.site_id == current_user.site_id,
            Payment.deleted_at.is_(None),
        )
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    payment.deleted_at = datetime.now(UTC)
    db.commit()
