from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge
from app.models.flat import Flat
from app.models.user import User, UserRole
from app.schemas.bulk import BulkChargeRequest, BulkChargeResult
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


@router.post("/bulk", response_model=BulkChargeResult, status_code=status.HTTP_200_OK)
def bulk_create_charges(
    payload: BulkChargeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> BulkChargeResult:
    """Tüm aktif dairelere veya seçili flat_ids listesine toplu borç oluştur."""

    # Hedef daireleri belirle
    flat_query = db.query(Flat).filter(
        Flat.site_id == current_user.site_id,
        Flat.deleted_at.is_(None),
        Flat.status == "active",
    )
    if payload.flat_ids:
        flat_query = flat_query.filter(Flat.id.in_(payload.flat_ids))
    flats = flat_query.all()

    # flat_ids verilmişse, DB'de bulunamayanları hata olarak raporla
    found_ids = {f.id for f in flats}
    errors: list[str] = []
    if payload.flat_ids:
        for fid in payload.flat_ids:
            if fid not in found_ids:
                errors.append(f"flat_id={fid} bulunamadı veya bu siteye ait değil")

    created = 0
    skipped = 0

    for flat in flats:
        # Duplicate kontrolü
        existing = (
            db.query(Charge)
            .filter(
                Charge.flat_id == flat.id,
                Charge.period == payload.period,
                Charge.charge_type == payload.charge_type,
                Charge.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            skipped += 1
            continue

        charge = Charge(
            site_id=current_user.site_id,
            flat_id=flat.id,
            charge_type=payload.charge_type.strip(),
            period=payload.period,
            amount=payload.amount,
            due_date=payload.due_date,
            status=payload.status,
        )
        db.add(charge)
        try:
            db.flush()  # ID üret, ama henüz commit etme
            created += 1
        except IntegrityError:
            db.rollback()
            skipped += 1
            continue

    db.commit()
    return BulkChargeResult(created=created, skipped=skipped, errors=errors)
