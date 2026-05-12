from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge
from app.models.flat import Flat
from app.models.user import User, UserRole
from app.schemas.charge import ChargeCreateRequest, ChargeResponse, ChargeUpdateRequest
from app.services import notification_service

router = APIRouter(prefix="/charges", tags=["charges"])


@router.get("", response_model=list[ChargeResponse])
def list_charges(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    flat_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[ChargeResponse]:
    query = db.query(Charge).filter(Charge.site_id == current_user.site_id, Charge.deleted_at.is_(None))

    if flat_id:
        query = query.filter(Charge.flat_id == flat_id)
    if period:
        query = query.filter(Charge.period == period)
    if status_filter:
        query = query.filter(Charge.status == status_filter)

    charges = query.order_by(Charge.created_at.desc()).all()
    return [ChargeResponse.model_validate(item, from_attributes=True) for item in charges]


@router.post("", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
def create_charge(
    payload: ChargeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> ChargeResponse:
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

    duplicate = (
        db.query(Charge)
        .filter(
            Charge.flat_id == payload.flat_id,
            Charge.period == payload.period,
            Charge.charge_type == payload.charge_type,
            Charge.deleted_at.is_(None),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Charge already exists")

    charge = Charge(
        site_id=current_user.site_id,
        flat_id=payload.flat_id,
        charge_type=payload.charge_type.strip(),
        period=payload.period,
        amount=payload.amount,
        due_date=payload.due_date,
        status=payload.status,
    )
    db.add(charge)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Charge already exists") from None
    db.refresh(charge)

    notification_service.notify_charge_created(
        db,
        site_id=current_user.site_id,
        flat_id=charge.flat_id,
        charge_id=charge.id,
        charge_type=charge.charge_type,
        period=charge.period,
        amount=str(charge.amount),
        user_id=current_user.id,
    )
    db.commit()

    return ChargeResponse.model_validate(charge, from_attributes=True)


@router.get("/{charge_id}", response_model=ChargeResponse)
def get_charge(
    charge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> ChargeResponse:
    charge = (
        db.query(Charge)
        .filter(
            Charge.id == charge_id,
            Charge.site_id == current_user.site_id,
            Charge.deleted_at.is_(None),
        )
        .first()
    )
    if not charge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")

    return ChargeResponse.model_validate(charge, from_attributes=True)


@router.patch("/{charge_id}", response_model=ChargeResponse)
def update_charge(
    charge_id: str,
    payload: ChargeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> ChargeResponse:
    charge = (
        db.query(Charge)
        .filter(
            Charge.id == charge_id,
            Charge.site_id == current_user.site_id,
            Charge.deleted_at.is_(None),
        )
        .first()
    )
    if not charge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")

    updates = payload.model_dump(exclude_unset=True)
    candidate_period = updates.get("period", charge.period)
    candidate_type = updates.get("charge_type", charge.charge_type)

    duplicate = (
        db.query(Charge)
        .filter(
            Charge.flat_id == charge.flat_id,
            Charge.period == candidate_period,
            Charge.charge_type == candidate_type,
            Charge.id != charge_id,
            Charge.deleted_at.is_(None),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Charge already exists")

    for key, value in updates.items():
        setattr(charge, key, value.strip() if isinstance(value, str) else value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Charge already exists") from None
    db.refresh(charge)

    return ChargeResponse.model_validate(charge, from_attributes=True)


@router.delete("/{charge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_charge(
    charge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> None:
    charge = (
        db.query(Charge)
        .filter(
            Charge.id == charge_id,
            Charge.site_id == current_user.site_id,
            Charge.deleted_at.is_(None),
        )
        .first()
    )
    if not charge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found")

    charge.deleted_at = datetime.now(UTC)
    db.commit()
